# Copyright (C) 2026 Paulo Felipe Jarschel

from typing import Any
from comfylab.engine.registry import register_block
from comfylab.blocks.base import BaseBlock, DataIn, DataOut, ExecutionContext

@register_block("string/substring")
class StringSubstringBlock(BaseBlock):
    """Extracts a substring from a given string."""
    icon = "✂️"
    display_name = "Substring"
    description = "Extracts a portion of a string based on Start and Length (or End if Length is 0 or omitted)."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text"),
        DataIn("Start", type_hint=int, default=0, widget="number"),
        DataIn("End", type_hint=int, default=-1, widget="number")
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Sub-string",
            "description": "Extrai parte de uma string com base no Início e Comprimento (ou Fim se o Comprimento for 0 ou omitido).",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Start": "Início",
                "End": "Fim",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Subcadena",
            "description": "Extrae una parte de una cadena según Inicio y Longitud (o Fin si la Longitud es 0 u omitida).",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Start": "Inicio",
                "End": "Fin",
                "Result": "Resultado"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            text = str(await context.pull(self.id, "Text") or "")
            start = int(await context.pull(self.id, "Start") or 0)
            end = int(await context.pull(self.id, "End") or -1)
            
            if end == -1 or end <= start:
                return text[start:]
            return text[start:end]
        return None

@register_block("string/split")
class StringSplitBlock(BaseBlock):
    """Splits a string into a list of strings."""
    icon = "➗"
    display_name = "Split String"
    description = "Splits a string into a list of strings based on a separator."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text"),
        DataIn("Separator", type_hint=str, default=",", widget="text")
    ]
    outputs_def = [DataOut("List", type_hint=list)]

    i18n = {
        "pt-BR": {
            "display_name": "Dividir String",
            "description": "Divide uma string em uma lista de strings com base em um separador.",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Separator": "Separador",
                "List": "Lista"
            }
        },
        "es": {
            "display_name": "Dividir Cadena",
            "description": "Divide una cadena en una lista de cadenas según un separador.",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Separator": "Separador",
                "List": "Lista"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "List":
            text = str(await context.pull(self.id, "Text") or "")
            sep = await context.pull(self.id, "Separator")
            
            if not sep:
                # If separator is completely empty, default python split() behavior (splits by whitespace)
                return text.split()
            return text.split(str(sep))
        return None

@register_block("string/join")
class StringJoinBlock(BaseBlock):
    """Joins a list of strings into a single string."""
    icon = "🔗"
    display_name = "Join Strings"
    description = "Joins a list of strings into a single string using a separator."
    
    inputs_def = [
        DataIn("List", type_hint=list),
        DataIn("Separator", type_hint=str, default=", ", widget="text")
    ]
    outputs_def = [DataOut("Text", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Juntar Strings",
            "description": "Junta uma lista de strings em uma única string usando um separador.",
            "category": "Strings",
            "pins": {
                "List": "Lista",
                "Separator": "Separador",
                "Text": "Texto"
            }
        },
        "es": {
            "display_name": "Unir Cadenas",
            "description": "Une una lista de cadenas en una sola cadena usando un separador.",
            "category": "Cadenas",
            "pins": {
                "List": "Lista",
                "Separator": "Separador",
                "Text": "Texto"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Text":
            lst = await context.pull(self.id, "List")
            sep = str(await context.pull(self.id, "Separator") or "")
            
            if not isinstance(lst, (list, tuple)):
                if hasattr(lst, "tolist"):
                    lst = lst.tolist()
                else:
                    return str(lst) if lst is not None else ""
            
            return sep.join(str(item) for item in lst)
        return None

@register_block("string/replace")
class StringReplaceBlock(BaseBlock):
    """Replaces occurrences of a substring with another."""
    icon = "🔄"
    display_name = "Replace String"
    description = "Replaces all occurrences of the 'Old' substring with the 'New' substring."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text"),
        DataIn("Old", type_hint=str, default="", widget="text"),
        DataIn("New", type_hint=str, default="", widget="text")
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Substituir String",
            "description": "Substitui todas as ocorrências da substring 'Velha' pela substring 'Nova'.",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Old": "Velha",
                "New": "Nova",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Reemplazar Cadena",
            "description": "Reemplaza todas las ocurrencias de la subcadena 'Vieja' por la subcadena 'Nueva'.",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Old": "Vieja",
                "New": "Nueva",
                "Result": "Resultado"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            text = str(await context.pull(self.id, "Text") or "")
            old_str = str(await context.pull(self.id, "Old") or "")
            new_str = str(await context.pull(self.id, "New") or "")
            
            if not old_str:
                return text
            return text.replace(old_str, new_str)
        return None

@register_block("string/concat")
class StringConcatBlock(BaseBlock):
    """Concatenates two strings together."""
    icon = "➕"
    display_name = "Concatenate"
    description = "Joins String A and String B together. Alternatively, pass a list to 'List' to concatenate many."
    
    inputs_def = [
        DataIn("String A", type_hint=str, default="", widget="text"),
        DataIn("String B", type_hint=str, default="", widget="text")
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Concatenar",
            "description": "Junta a String A e a String B. Opcionalmente, forneça uma lista em 'Lista' para concatenar várias.",
            "category": "Strings",
            "pins": {
                "String A": "String A",
                "String B": "String B",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Concatenar",
            "description": "Une la Cadena A y la Cadena B. Opcionalmente, pasa una lista a 'Lista' para concatenar varias.",
            "category": "Cadenas",
            "pins": {
                "String A": "Cadena A",
                "String B": "Cadena B",
                "Result": "Resultado"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            a = str(await context.pull(self.id, "String A") or "")
            b = str(await context.pull(self.id, "String B") or "")
            return a + b
        return None

@register_block("string/length")
class StringLengthBlock(BaseBlock):
    """Returns the number of characters in a string."""
    icon = "📏"
    display_name = "String Length"
    description = "Returns the length of the input text."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text")
    ]
    outputs_def = [DataOut("Length", type_hint=int)]

    i18n = {
        "pt-BR": {
            "display_name": "Tamanho da String",
            "description": "Retorna o comprimento do texto de entrada.",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Length": "Tamanho"
            }
        },
        "es": {
            "display_name": "Longitud de Cadena",
            "description": "Devuelve la longitud del texto de entrada.",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Length": "Longitud"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Length":
            text = str(await context.pull(self.id, "Text") or "")
            return len(text)
        return None

@register_block("string/case")
class StringCaseBlock(BaseBlock):
    """Changes the capitalization case of a string."""
    icon = "🔠"
    display_name = "Change Case"
    description = "Converts text to uppercase, lowercase, or title case."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text"),
        DataIn("Mode", type_hint=str, default="Upper", options=["Upper", "Lower", "Title"])
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Mudar Maiúsculas/Minúsculas",
            "description": "Converte o texto para maiúsculas, minúsculas ou capitalizado.",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Mode": "Modo",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Cambiar Mayúsculas/Minúsculas",
            "description": "Convierte el texto a mayúsculas, minúsculas o formato título.",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Mode": "Modo",
                "Result": "Resultado"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            text = str(await context.pull(self.id, "Text") or "")
            mode = await context.pull(self.id, "Mode")
            
            if mode == "Lower":
                return text.lower()
            elif mode == "Title":
                return text.title()
            return text.upper()
        return None

@register_block("string/trim")
class StringTrimBlock(BaseBlock):
    """Removes whitespace from a string."""
    icon = "🧹"
    display_name = "Trim String"
    description = "Removes leading and trailing whitespace from the text."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text")
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Aparar String",
            "description": "Remove os espaços em branco no início e no final do texto.",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Recortar Cadena",
            "description": "Elimina los espacios en blanco iniciales y finales del texto.",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Result": "Resultado"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            text = str(await context.pull(self.id, "Text") or "")
            return text.strip()
        return None


@register_block("string/format")
class FormatStringBlock(BaseBlock):
    """Templates a string replacing {0}, {1}, {2} etc. placeholders."""
    icon = "🖹"
    display_name = "Format String"
    description = "Templates a string replacing {0} style placeholders."
    
    inputs_def = [
        DataIn("Template", type_hint=str, default="Value is {0}", widget="text"),
        DataIn("Arg0", type_hint=Any, default="", widget="text", optional=True),
        DataIn("Arg1", type_hint=Any, default="", widget="text", optional=True),
        DataIn("Arg2", type_hint=Any, default="", widget="text", optional=True)
    ]
    outputs_def = [DataOut("Result", type_hint=str)]

    i18n = {
        "pt-BR": {
            "display_name": "Formatar String",
            "description": "Gera um texto substituindo espaços reservados do tipo {0}.",
            "category": "Strings",
            "pins": {
                "Template": "Modelo",
                "Arg0": "Arg0",
                "Arg1": "Arg1",
                "Arg2": "Arg2",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Formatear Cadena",
            "description": "Genera un texto reemplazando marcadores de posición estilo {0}.",
            "category": "Cadenas",
            "pins": {
                "Template": "Plantilla",
                "Arg0": "Arg0",
                "Arg1": "Arg1",
                "Arg2": "Arg2",
                "Result": "Resultado"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            template = str(await context.pull(self.id, "Template"))
            arg0 = await context.pull(self.id, "Arg0")
            arg1 = await context.pull(self.id, "Arg1")
            arg2 = await context.pull(self.id, "Arg2")
            
            try:
                return template.format(arg0, arg1, arg2, arg0=arg0, arg1=arg1, arg2=arg2)
            except Exception as e:
                return f"[Format Error: {e}]"
        return None


@register_block("string/contains")
class StringContainsBlock(BaseBlock):
    """Searches for occurrences of a substring within a string."""
    icon = "🔍"
    display_name = "String Contains"
    description = "Searches a string for occurrences of another string, returning whether it was found and the index of its last appearance."
    
    inputs_def = [
        DataIn("Text", type_hint=str, default="", widget="text"),
        DataIn("Search", type_hint=str, default="", widget="text")
    ]
    outputs_def = [
        DataOut("Found", type_hint=bool),
        DataOut("Index", type_hint=int)
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Contém String",
            "description": "Procura ocorrências de uma string em outra, indicando se foi encontrada e o índice de sua última aparição.",
            "category": "Strings",
            "pins": {
                "Text": "Texto",
                "Search": "Buscar",
                "Found": "Encontrado",
                "Index": "Índice"
            }
        },
        "es": {
            "display_name": "Contiene Cadena",
            "description": "Busca ocurrencias de una cadena en otra, devolviendo si fue encontrada y el índice de su última aparición.",
            "category": "Cadenas",
            "pins": {
                "Text": "Texto",
                "Search": "Buscar",
                "Found": "Encontrado",
                "Index": "Índice"
            }
        }
    }

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        text = str(await context.pull(self.id, "Text") or "")
        search = str(await context.pull(self.id, "Search") or "")
        
        if pin_name == "Found":
            return (search in text) if search else False
        elif pin_name == "Index":
            return text.find(search) if search else -1
        return None

