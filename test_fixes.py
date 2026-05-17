#!/usr/bin/env python3
"""Test script to verify code review fixes."""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_json_parser():
    """Test the shared JSON parser utility."""
    from app.utils.json_parser import parse_llm_json_response
    
    print("\n" + "="*60)
    print("Testing JSON Parser Utility")
    print("="*60)
    
    # Test 1: Direct JSON
    test1 = '{"workout_days": [{"day_number": 1}]}'
    result1 = parse_llm_json_response(test1, save_on_error=False)
    assert "workout_days" in result1
    print("✅ Test 1 passed: Direct JSON parsing")
    
    # Test 2: JSON in markdown
    test2 = '```json\n{"workout_days": [{"day_number": 1}]}\n```'
    result2 = parse_llm_json_response(test2, save_on_error=False)
    assert "workout_days" in result2
    print("✅ Test 2 passed: Markdown code block parsing")
    
    # Test 3: JSON with extra text
    test3 = 'Here is the plan: {"workout_days": [{"day_number": 1}]} Hope this helps!'
    result3 = parse_llm_json_response(test3, save_on_error=False)
    assert "workout_days" in result3
    print("✅ Test 3 passed: JSON extraction from text")
    
    print("\n✅ All JSON parser tests passed!")


def test_validators():
    """Test input validation utilities."""
    from app.utils.validators import (
        validate_n_results,
        validate_exercise_id,
        sanitize_query_string,
        validate_equipment_list,
        sanitize_user_data_for_logging
    )
    
    print("\n" + "="*60)
    print("Testing Input Validators")
    print("="*60)
    
    # Test n_results validation
    assert validate_n_results(10) == 10
    assert validate_n_results("20") == 20
    print("✅ Test 1 passed: n_results validation")
    
    try:
        validate_n_results(200)  # Should fail
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Test 2 passed: n_results bounds checking")
    
    # Test exercise ID validation
    assert validate_exercise_id("0001") == "0001"
    assert validate_exercise_id("ex-123_test") == "ex-123_test"
    print("✅ Test 3 passed: Exercise ID validation")
    
    try:
        validate_exercise_id("bad@id!")  # Should fail
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Test 4 passed: Exercise ID format checking")
    
    # Test query sanitization
    query = sanitize_query_string("  chest exercises  ")
    assert query == "chest exercises"
    print("✅ Test 5 passed: Query sanitization")
    
    # Test equipment list validation
    equipment = validate_equipment_list("barbell, dumbbell, cable")
    assert len(equipment) == 3
    assert "barbell" in equipment
    print("✅ Test 6 passed: Equipment list validation")
    
    # Test PII sanitization
    user_data = {
        "age": 25,
        "weight": 70,
        "fitness_level": "intermediate",
        "goals": ["muscle_gain"]
    }
    sanitized = sanitize_user_data_for_logging(user_data)
    assert sanitized["age"] == "[REDACTED]"
    assert sanitized["weight"] == "[REDACTED]"
    assert sanitized["fitness_level"] == "intermediate"
    print("✅ Test 7 passed: PII sanitization for logging")
    
    print("\n✅ All validator tests passed!")


def test_constants():
    """Test that magic numbers are now constants."""
    from app.services.mlx_agent_service import MLXAgentService
    
    print("\n" + "="*60)
    print("Testing Constants")
    print("="*60)
    
    assert hasattr(MLXAgentService, 'MAX_ITERATIONS')
    assert hasattr(MLXAgentService, 'MAX_TOOL_CALLS')
    assert hasattr(MLXAgentService, 'MAX_CONVERSATION_LENGTH')
    
    assert MLXAgentService.MAX_ITERATIONS == 3
    assert MLXAgentService.MAX_TOOL_CALLS == 3
    assert MLXAgentService.MAX_CONVERSATION_LENGTH == 30000
    
    print("✅ All constants defined correctly!")


def test_imports():
    """Test that all new modules can be imported."""
    print("\n" + "="*60)
    print("Testing Module Imports")
    print("="*60)
    
    try:
        from app.utils.json_parser import parse_llm_json_response
        print("✅ json_parser module imported")
        
        from app.utils.validators import (
            validate_n_results,
            validate_exercise_id,
            sanitize_query_string
        )
        print("✅ validators module imported")
        
        from app.services.mlx_agent_service import MLXAgentService
        print("✅ mlx_agent_service module imported")
        
        from app.services.llm_service import LLMService
        print("✅ llm_service module imported")
        
        from app.services.rag_pipeline import RAGPipeline
        print("✅ rag_pipeline module imported")
        
        print("\n✅ All modules imported successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Code Review Fix Tests")
    print("="*60)
    
    try:
        # Test imports first
        if not test_imports():
            print("\n❌ Import tests failed. Cannot continue.")
            sys.exit(1)
        
        # Test utilities
        test_json_parser()
        test_validators()
        test_constants()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nKey fixes verified:")
        print("  ✅ Shared JSON parser utility (DRY)")
        print("  ✅ Input validation and sanitization (Security)")
        print("  ✅ PII protection in logging (Security)")
        print("  ✅ Magic numbers replaced with constants (Maintainability)")
        print("  ✅ All modules import correctly")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob