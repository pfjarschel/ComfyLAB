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
