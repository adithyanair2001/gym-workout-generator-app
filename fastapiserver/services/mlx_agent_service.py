"""MLX-based LLM Agent service for agent-based RAG with direct model loading."""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import mlx.core as mx
from mlx_lm import generate, load

from fastapiserver.models.user_profile import UserProfile
from fastapiserver.services.database_tools import DatabaseTools
from fastapiserver.utils.json_parser import parse_llm_json_response
from fastapiserver.utils.validators import (
    validate_n_results,
    validate_exercise_id,
    sanitize_query_string,
    validate_equipment_list
)

logger = logging.getLogger(__name__)


class MLXAgentService:
    """Service for MLX-based LLM agent that can query the database using tools."""
    
    # Agent configuration constants
    MAX_ITERATIONS = 10  # Increased to allow more iterations for complex plans
    MAX_TOOL_CALLS = 25  # Increased to 25 to search through many exercises
    MAX_CONVERSATION_LENGTH = 100000  # Increased for longer conversations with many tool calls
    
    def __init__(
        self,
        model_path: str,
        database_tools: DatabaseTools,
        temperature: float = 0.7,
        max_tokens: int = 32000
    ):
        """Initialize the MLX agent service.
        
        Args:
            model_path: Path to MLX model directory
            database_tools: Database tools instance
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.model_path = model_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.database_tools = database_tools
        self._is_loaded = False
        
        # Load MLX model
        logger.info(f"Loading MLX model from {model_path}...")
        load_result = load(model_path)
        if len(load_result) == 3:
            self.model, self.tokenizer, self.config = load_result
        else:
            self.model, self.tokenizer = load_result
            self.config = None
        
        # Validate model loaded successfully
        if self.model is None or self.tokenizer is None:
            raise RuntimeError(f"Failed to load MLX model from {model_path}")
        
        self._is_loaded = True
        logger.info("MLX model loaded successfully")
        
        # Get tools
        self.tools = {
            "search_exercises": database_tools.search_exercises,
            "filter_by_equipment": database_tools.filter_by_equipment,
            "get_exercise_details": database_tools.get_exercise_details
        }
        
        logger.info(f"MLX Agent service initialized with {len(self.tools)} tools")
    
    def cleanup(self):
        """Clean up MLX model resources.
        
        This method unloads the model from memory and clears references.
        Should be called when the service is no longer needed.
        """
        if self._is_loaded:
            logger.info(f"Cleaning up MLX model from {self.model_path}")
            try:
                # Clear model references
                self.model = None
                self.tokenizer = None
                self.config = None
                
                # Force garbage collection to free memory
                import gc
                gc.collect()
                
                self._is_loaded = False
                logger.info("MLX model cleanup completed")
            except Exception as e:
                logger.error(f"Error during MLX model cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        self.cleanup()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent.
        
        Returns:
            System prompt string
        """
        return """You are an expert personal trainer AI assistant with access to an exercise database.
You can use the following tools to query the database:

1. search_exercises(query: str, n_results: int = 10) - Search for exercises using natural language
   Example: search_exercises("chest exercises for beginners", 10)

2. filter_by_equipment(equipment_list: list, n_results: int = 20) - Filter exercises by equipment
   Example: filter_by_equipment(["barbell", "dumbbell"], 20)

3. get_exercise_details(exercise_id: str) - Get detailed information about a specific exercise
   Example: get_exercise_details("0001")

IMPORTANT RULES:
1. ALWAYS use tools to search for exercises - DO NOT invent exercises
2. When you need to use a tool, output: TOOL_CALL: tool_name(arguments)
3. After receiving tool results, continue your reasoning
4. Create a complete workout plan with proper JSON structure
5. Consider the user's fitness level, goals, and available time
6. When providing Final Answer, output ONLY the JSON workout plan - NO explanatory text before or after
7. The Final Answer must start with { and end with } - nothing else

Use this format:
Thought: [your reasoning]
TOOL_CALL: tool_name(arguments)
[Tool results will be provided]
Thought: [continue reasoning with results]
Final Answer: {
  "workout_days": [...]
}

CRITICAL: Your Final Answer must be ONLY valid JSON with no additional text, explanations, or comments."""
    
    def _parse_tool_call(self, text: str) -> Optional[tuple]:
        """Parse tool call from model output.
        
        Args:
            text: Model output text
            
        Returns:
            Tuple of (tool_name, arguments) or None
        """
        import json
        
        # Look for TOOL_CALL: pattern with proper bracket/parenthesis matching
        match = re.search(r'TOOL_CALL:\s*(\w+)\(', text)
        if match:
            tool_name = match.group(1)
            start_pos = match.end()
            
            # Find matching closing parenthesis
            paren_count = 1
            bracket_count = 0
            in_quotes = False
            quote_char = None
            end_pos = start_pos
            
            for i in range(start_pos, len(text)):
                char = text[i]
                
                # Handle quotes
                if char in ('"', "'") and (i == 0 or text[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                
                # Count brackets and parentheses only outside quotes
                if not in_quotes:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                        if paren_count == 0:
                            end_pos = i
                            break
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
            
            if paren_count != 0:
                logger.error(f"Unmatched parentheses in tool call")
                return None
            
            args_str = text[start_pos:end_pos].strip()
            
            # Parse arguments
            try:
                # Parse named parameters (e.g., query="...", n_results=10, equipment_list=["barbell", "dumbbell"])
                args_dict = {}
                
                # Split by comma, but handle quoted strings and brackets
                parts = []
                current = ""
                in_quotes = False
                in_brackets = 0
                for char in args_str:
                    if char == '"' or char == "'":
                        in_quotes = not in_quotes
                    elif char == '[' and not in_quotes:
                        in_brackets += 1
                    elif char == ']' and not in_quotes:
                        in_brackets -= 1
                    elif char == ',' and not in_quotes and in_brackets == 0:
                        parts.append(current.strip())
                        current = ""
                        continue
                    current += char
                if current.strip():
                    parts.append(current.strip())
                
                # Parse each part as key=value
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Try to parse as JSON (handles lists, numbers, etc.)
                        try:
                            # Replace single quotes with double quotes for JSON parsing
                            value_json = value.replace("'", '"')
                            parsed_value = json.loads(value_json)
                            args_dict[key] = parsed_value
                        except json.JSONDecodeError:
                            # Fall back to string parsing
                            args_dict[key] = value.strip('"').strip("'")
                    else:
                        # Positional argument
                        value = part.strip()
                        try:
                            value_json = value.replace("'", '"')
                            parsed_value = json.loads(value_json)
                            args_dict[f'arg_{len(args_dict)}'] = parsed_value
                        except json.JSONDecodeError:
                            args_dict[f'arg_{len(args_dict)}'] = value.strip('"').strip("'")
                
                return (tool_name, args_dict)
            except Exception as e:
                logger.error(f"Error parsing tool arguments: {e}")
                return None
        
        return None
    
    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool with given arguments and input validation.
        
        Args:
            tool_name: Name of the tool
            arguments: Dictionary of arguments
            
        Returns:
            Tool execution result as string
        """
        try:
            if tool_name not in self.tools:
                return f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
            
            tool_func = self.tools[tool_name]
            
            # Call tool with appropriate arguments and validation
            if tool_name == "search_exercises":
                query = arguments.get('query', arguments.get('arg_0', ''))
                n_results_raw = arguments.get('n_results', arguments.get('arg_1', 10))
                
                # Validate inputs
                query = sanitize_query_string(query)
                n_results = validate_n_results(n_results_raw, min_val=1, max_val=50)
                
                result = tool_func(query, n_results)
                
            elif tool_name == "filter_by_equipment":
                equipment = arguments.get('equipment_list', arguments.get('equipment', arguments.get('arg_0', '')))
                n_results_raw = arguments.get('n_results', arguments.get('arg_1', 20))
                
                # Validate inputs
                equipment_list = validate_equipment_list(equipment)
                n_results = validate_n_results(n_results_raw, min_val=1, max_val=50)
                
                result = tool_func(equipment_list, n_results)
                
            elif tool_name == "get_exercise_details":
                exercise_id = arguments.get('exercise_id', arguments.get('id', arguments.get('arg_0', '')))
                
                # Validate input
                exercise_id = validate_exercise_id(exercise_id)
                
                result = tool_func(exercise_id)
            else:
                result = f"Error: Unknown tool '{tool_name}'"
            
            return result
            
        except ValueError as e:
            # Input validation errors
            logger.warning(f"Validation error in tool {tool_name}: {e}")
            return f"Error: Invalid input - {str(e)}"
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return f"Error executing tool: {str(e)}"
    
    def build_user_request(self, user_profile: UserProfile) -> str:
        """Build the user request for the agent.
        
        Args:
            user_profile: User profile information
            
        Returns:
            Formatted request string
        """
        goals_text = ', '.join([g.value.replace('_', ' ') for g in user_profile.goals])
        equipment_text = ', '.join(user_profile.available_equipment)
        
        request = f"""Create a personalized {user_profile.gym_days_per_week}-day workout plan for:

USER PROFILE:
- Age: {user_profile.age}, Gender: {user_profile.gender}
- Height: {user_profile.height}cm, Weight: {user_profile.weight}kg
- Fitness Level: {user_profile.fitness_level.value}
- Goals: {goals_text}
- Days per week: {user_profile.gym_days_per_week}
- Session duration: {user_profile.workout_duration_minutes} minutes
- Available equipment: {equipment_text}
- Injuries/Limitations: {', '.join(user_profile.injuries_limitations or ['None'])}
- Preferred split: {user_profile.preferred_split.value}

REQUIREMENTS:
1. Use search_exercises tool to find appropriate exercises
2. Use filter_by_equipment to ensure exercises match available equipment
3. Create {user_profile.gym_days_per_week} workout days
4. Each workout should be approximately {user_profile.workout_duration_minutes} minutes
5. Assign appropriate sets/reps based on {user_profile.fitness_level.value} level:
   - Beginner: 2-3 sets, 12-15 reps, 60-90s rest
   - Intermediate: 3-4 sets, 8-12 reps, 60s rest
   - Advanced: 4-5 sets, 6-10 reps, 45-60s rest

OUTPUT FORMAT (JSON):
{{
  "workout_days": [
    {{
      "day_number": 1,
      "day_name": "Day 1: Upper Body Push",
      "focus": "Chest, Shoulders, Triceps",
      "main_workout": [
        {{
          "exercise_id": "0001",
          "name": "barbell bench press",
          "target_muscles": ["pectorals"],
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "notes": "Keep shoulder blades retracted"
        }}
      ],
      "estimated_duration_minutes": 60
    }}
  ],
  "progression_notes": "Increase weight by 2.5-5% when you can complete all sets with good form",
  "nutrition_tips": "Aim for 1.6-2.2g protein per kg bodyweight"
}}

Start by using the tools to search for exercises, then create the complete workout plan."""
        
        return request
    
    def generate_workout_plan(self, user_profile: UserProfile) -> str:
        """Generate workout plan using the MLX agent.
        
        Args:
            user_profile: User profile information
            
        Returns:
            Generated workout plan as raw string
            
        Raises:
            Exception: If generation fails
        """
        if not self._is_loaded:
            raise RuntimeError("MLX model has been unloaded. Cannot generate workout plan.")
        
        try:
            logger.info(f"Generating workout plan with MLX agent for {user_profile.fitness_level.value} user...")
            
            # Build prompts
            system_prompt = self._create_system_prompt()
            user_request = self.build_user_request(user_profile)
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\nUser Request:\n{user_request}\n\nThought:"
            
            # Agent loop
            conversation_history = full_prompt
            tool_calls_made = 0
            
            for iteration in range(self.MAX_ITERATIONS):
                logger.info(f"Agent iteration {iteration + 1}/{self.MAX_ITERATIONS}")
                
                # Check conversation history size to prevent memory issues
                if len(conversation_history) > self.MAX_CONVERSATION_LENGTH:
                    logger.warning(f"Conversation history exceeding {self.MAX_CONVERSATION_LENGTH} chars, truncating")
                    # Keep only recent context
                    conversation_history = conversation_history[-20000:]
                
                # After max tool calls, force final answer
                if tool_calls_made >= self.MAX_TOOL_CALLS:
                    logger.info(f"Reached max tool calls ({self.MAX_TOOL_CALLS}), requesting final answer")
                    conversation_history += "\n\nYou have gathered enough information. Now provide the Final Answer with the complete workout plan in JSON format."
                
                # Generate response
                response = generate(
                    self.model,
                    self.tokenizer,
                    prompt=conversation_history,
                    max_tokens=self.max_tokens,
                    verbose=False
                )
                
                logger.info(f"Model response: {response[:200]}...")
                
                # Check for tool call
                tool_call = self._parse_tool_call(response)
                
                if tool_call and tool_calls_made < self.MAX_TOOL_CALLS:
                    tool_name, arguments = tool_call
                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")
                    
                    # Execute tool
                    tool_result = self._execute_tool(tool_name, arguments)
                    logger.info(f"Tool result length: {len(tool_result)} characters")
                    tool_calls_made += 1
                    
                    # Add to conversation
                    conversation_history += f"{response}\n\nTool Result:\n{tool_result}\n\nThought:"
                else:
                    # No more tool calls, check if we have final answer
                    if "Final Answer:" in response or "{" in response:
                        logger.info("Agent completed - found final answer")
                        # Extract only the JSON part after "Final Answer:"
                        return self._extract_final_answer(response)
                    else:
                        # Continue conversation
                        conversation_history += response + "\n\nThought:"
            
            raise ValueError("Agent exceeded maximum iterations without producing final answer")
            
        except Exception as e:
            logger.error(f"Error generating workout plan with MLX agent: {e}")
            raise
    
    def _extract_final_answer(self, response: str) -> str:
        """Extract only the JSON content after 'Final Answer:' marker.
        
        Args:
            response: Raw agent response containing 'Final Answer:' and JSON
            
        Returns:
            Extracted JSON string (everything after 'Final Answer:')
        """
        # Look for "Final Answer:" marker
        if "Final Answer:" in response:
            # Extract everything after "Final Answer:"
            final_answer_start = response.find("Final Answer:") + len("Final Answer:")
            json_content = response[final_answer_start:].strip()
            logger.info(f"Extracted content after 'Final Answer:' ({len(json_content)} chars)")
            return json_content
        
        # If no "Final Answer:" marker, try to find JSON directly
        start = response.find("{")
        if start != -1:
            json_content = response[start:].strip()
            logger.info(f"No 'Final Answer:' marker found, extracted JSON from first '{{' ({len(json_content)} chars)")
            return json_content
        
        # Return as-is if no markers found
        logger.warning("No 'Final Answer:' marker or JSON found, returning full response")
        return response
    
    def parse_json_response(self, response: str) -> Dict:
        """Extract and parse JSON from agent response using shared utility.
        
        Args:
            response: Raw agent response text
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If JSON parsing fails
        """
        return parse_llm_json_response(response, save_on_error=True)
    
    def test_connection(self) -> bool:
        """Test MLX model loading.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if not self._is_loaded:
            logger.warning("MLX model has been unloaded")
            return False
        
        try:
            # Test with a simple generation
            response = generate(
                self.model,
                self.tokenizer,
                prompt="Hello, how are you?",
                max_tokens=20,
                verbose=False
            )
            logger.info(f"MLX model test successful. Response: {response[:50]}")
            return True
        except Exception as e:
            logger.error(f"MLX model test failed: {e}")
            return False


# Made with Bob