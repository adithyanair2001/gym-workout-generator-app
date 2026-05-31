"""Shared JSON parsing utilities for LLM responses."""
import json
import json.decoder
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def parse_llm_json_response(response: str, save_on_error: bool = True) -> Dict:
    """Extract and parse JSON from LLM response with multiple fallback strategies.
    
    This function handles various formats that LLMs might return:
    - Direct JSON
    - JSON wrapped in markdown code blocks
    - JSON with extra text before/after
    - Incomplete JSON (attempts to fix)
    
    Args:
        response: Raw LLM response text
        save_on_error: If True, saves problematic responses to failed_parse.json for debugging
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If JSON parsing fails after all strategies
    """
    try:
        # Strategy 1: Try direct JSON parsing first
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.debug(f"Direct JSON parsing failed: {e}, trying extraction strategies")
        
        # Strategy 2: Look for JSON in markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            # Strategy 3: Try to find JSON object boundaries by matching braces
            start = response.find("{")
            if start == -1:
                logger.error("Could not find opening brace in response")
                if save_on_error:
                    _save_failed_parse(response)
                raise ValueError("Could not find JSON in response")
            
            # Find the matching closing brace by tracking depth
            json_str = _extract_complete_json_object(response, start)
            if not json_str:
                logger.error("Could not find matching closing brace")
                if save_on_error:
                    _save_failed_parse(response)
                raise ValueError("Could not extract complete JSON object")
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse extracted JSON: {e}")
            logger.error(f"Extracted text (first 500 chars): {json_str[:500]}...")
            logger.error(f"Extracted text (last 500 chars): ...{json_str[-500:]}")
            
            # Strategy 4: Handle "Extra data" error - JSON is valid but has text after it
            if "Extra data" in str(e):
                logger.info("Detected extra data after JSON, attempting to extract valid JSON only")
                decoder = json.JSONDecoder()
                try:
                    obj, idx = decoder.raw_decode(json_str)
                    logger.info(f"Successfully extracted valid JSON (stopped at char {idx})")
                    return obj
                except json.JSONDecodeError:
                    pass
            
            # Strategy 5: Try to fix incomplete JSON by adding missing braces/brackets
            json_str = _attempt_json_repair(json_str)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # All strategies failed
            if save_on_error:
                _save_failed_parse(response)
            raise ValueError(f"Invalid JSON in LLM response after all repair attempts: {e}")


def _extract_complete_json_object(text: str, start_pos: int) -> str:
    """Extract a complete JSON object by matching opening { with closing }.
    
    Tracks brace depth to find the exact position where the JSON object ends,
    ignoring any extra text or malformed braces after the valid JSON.
    
    Args:
        text: Text containing JSON object
        start_pos: Position of the opening {
        
    Returns:
        Complete JSON object string, or empty string if matching brace not found
    """
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(text)):
        char = text[i]
        
        # Handle escape sequences in strings
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
        
        # Track string boundaries
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        # Only count braces outside of strings
        if not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                # When depth returns to 0, we've found the matching closing brace
                if depth == 0:
                    json_str = text[start_pos:i+1]
                    logger.info(f"Extracted complete JSON object ({len(json_str)} chars, ending at position {i+1})")
                    return json_str
    
    # No matching closing brace found
    logger.warning(f"No matching closing brace found for opening brace at position {start_pos}")
    return ""


def _attempt_json_repair(json_str: str) -> str:
    """Attempt to repair incomplete JSON by adding missing closing characters.
    
    This function tracks the nesting order of braces and brackets to add
    closing characters in the correct sequence.
    
    Args:
        json_str: Potentially incomplete JSON string
        
    Returns:
        Repaired JSON string
    """
    # Track opening characters in order to close them properly
    stack = []
    in_string = False
    escape_next = False
    
    for char in json_str:
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}' and stack and stack[-1] == '}':
                stack.pop()
            elif char == ']' and stack and stack[-1] == ']':
                stack.pop()
    
    # Add missing closing characters in reverse order
    if stack:
        closing_chars = ''.join(reversed(stack))
        json_str += closing_chars
        logger.info(f"Added {len(stack)} closing characters: {closing_chars}")
    
    return json_str


def _save_failed_parse(response: str) -> None:
    """Save failed parse response to file for debugging.
    
    Args:
        response: The response that failed to parse
    """
    try:
        with open('failed_parse.json', 'w') as f:
            f.write(response)
        logger.info("Saved failed parse response to failed_parse.json for debugging")
    except Exception as e:
        logger.error(f"Failed to save debug file: {e}")


# Made with Bob