# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from typing import Any, Dict

from comfylab.engine.registry import register_block
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, validate_via_external_parser
from comfylab.blocks.script import DECORATOR_PATTERN

DEFAULT_R_CODE = """# @input name="value" type="number" default=1.0
# @output name="result" type="number"

result <- value * 2
"""


@register_block("script/r")
class RScriptBlock(BaseSubprocessScriptBlock):
    icon = "📊"
    display_name = "R Script"
    description = "User-defined R code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_R_CODE
    file_extension = ".R"
    executable_name = "Rscript"

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Map Python values to R literals
        def to_r_literal(val):
            if val is None:
                return "NULL"
            elif isinstance(val, bool):
                return "TRUE" if val else "FALSE"
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, str):
                escaped = val.replace('"', '\\"').replace('\n', '\\n')
                return f'"{escaped}"'
            elif isinstance(val, list):
                parts = [to_r_literal(v) for v in val]
                return f"c({', '.join(parts)})"
            elif isinstance(val, dict):
                parts = [f"{k} = {to_r_literal(v)}" for k, v in val.items()]
                return f"list({', '.join(parts)})"
            return "NULL"

        # Generate inputs injection code in R syntax
        injection_lines = []
        for name, val in inputs.items():
            injection_lines.append(f"{name} <- {to_r_literal(val)}")

        injection_code = "\n".join(injection_lines) + "\n\n"

        # Pure R JSON serializer fallback (no external package dependency)
        r_json_serializer = r"""
serialize_to_json <- function(val) {
  if (is.null(val)) {
    return("null")
  } else if (is.logical(val)) {
    return(ifelse(val, "true", "false"))
  } else if (is.numeric(val)) {
    if (length(val) > 1) {
      return(paste0("[", paste(val, collapse=","), "]"))
    }
    return(as.character(val))
  } else if (is.character(val)) {
    if (length(val) > 1) {
      escaped <- gsub('"', '\\\\"', val)
      return(paste0("[", paste0('"', escaped, '"', collapse=","), "]"))
    }
    return(paste0('"', gsub('"', '\\\\"', val), '"'))
  } else if (is.vector(val)) {
    parts <- sapply(val, serialize_to_json)
    return(paste0("[", paste(parts, collapse=","), "]"))
  } else if (is.list(val)) {
    ns <- names(val)
    if (is.null(ns) || any(ns == "")) {
      parts <- sapply(val, serialize_to_json)
      return(paste0("[", paste(parts, collapse=","), "]"))
    } else {
      parts <- sapply(ns, function(n) {
        paste0('"', n, '":', serialize_to_json(val[[n]]))
      })
      return(paste0("{", paste(parts, collapse=","), "}"))
    }
  }
  return("null")
}
"""

        # Append execution extraction script
        out_list_elements = ", ".join(f'{out["name"]} = {out["name"]}' for out in self._parsed_outputs)
        output_script = f"""
{r_json_serializer}

out_table <- list({out_list_elements})
if (requireNamespace("jsonlite", quietly = TRUE)) {{{{
    out_str <- jsonlite::toJSON(out_table, auto_unbox = TRUE)
}}}} else {{{{
    parts <- sapply(names(out_table), function(n) {{{{
        paste0('"', n, '":', serialize_to_json(out_table[[n]]))
    }}}})
    out_str <- paste0("{{", paste(parts, collapse=","), "}}")
}}}}
writeLines(out_str, "{output_file_path}")
"""
        return injection_code + code + "\n" + output_script


async def validate_code(code: str) -> dict:
    """Validates R script syntax using Rscript parse()."""
    return await validate_via_external_parser(
        "Rscript", ["-e", "parse(file='{temp}')"], code, ".R"
    )
