# Copyright (C) 2026 Paulo Felipe Jarschel

from typing import Any, Dict, Optional
from comfylab.engine.registry import register_node
from comfylab.nodes.base import BaseNode, DataIn, DataOut, ExecutionContext

@register_node("string/substring")
class StringSubstringNode(BaseNode):
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

@register_node("string/split")
class StringSplitNode(BaseNode):
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

@register_node("string/join")
class StringJoinNode(BaseNode):
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

@register_node("string/replace")
class StringReplaceNode(BaseNode):
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

@register_node("string/concat")
class StringConcatNode(BaseNode):
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

@register_node("string/length")
class StringLengthNode(BaseNode):
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

@register_node("string/case")
class StringCaseNode(BaseNode):
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

@register_node("string/trim")
class StringTrimNode(BaseNode):
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
