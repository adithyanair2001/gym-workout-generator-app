#!/usr/bin/env python3
"""Test script to verify utility modules (no heavy dependencies required)."""

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
    
    # Test 4: Incomplete JSON repair
    test4 = '{"workout_days": [{"day_number": 1}'  # Missing closing braces
    result4 = parse_llm_json_response(test4, save_on_error=False)
    assert "workout_days" in result4
    print("✅ Test 4 passed: Incomplete JSON repair")
    
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
        validate_n_results(200)  # Should fail (max 100)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Test 2 passed: n_results bounds checking")
    
    try:
        validate_n_results(-5)  # Should fail (min 1)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Test 3 passed: n_results minimum bounds")
    
    # Test exercise ID validation
    assert validate_exercise_id("0001") == "0001"
    assert validate_exercise_id("ex-123_test") == "ex-123_test"
    print("✅ Test 4 passed: Exercise ID validation")
    
    try:
        validate_exercise_id("bad@id!")  # Should fail
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Test 5 passed: Exercise ID format checking")
    
    try:
        validate_exercise_id("")  # Should fail
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Test 6 passed: Empty exercise ID rejection")
    
    # Test query sanitization
    query = sanitize_query_string("  chest exercises  ")
    assert query == "chest exercises"
    print("✅ Test 7 passed: Query sanitization (whitespace)")
    
    long_query = "a" * 600
    sanitized = sanitize_query_string(long_query)
    assert len(sanitized) == 500  # Should be truncated
    print("✅ Test 8 passed: Query length limiting")
    
    # Test equipment list validation
    equipment = validate_equipment_list("barbell, dumbbell, cable")
    assert len(equipment) == 3
    assert "barbell" in equipment
    assert "dumbbell" in equipment
    print("✅ Test 9 passed: Equipment list validation (string)")
    
    equipment2 = validate_equipment_list(["Barbell", "Dumbbell"])
    assert len(equipment2) == 2
    assert "barbell" in equipment2  # Should be normalized to lowercase
    print("✅ Test 10 passed: Equipment list validation (list) with normalization")
    
    # Test PII sanitization
    user_data = {
        "age": 25,
        "weight": 70,
        "height": 175,
        "gender": "male",
        "fitness_level": "intermediate",
        "goals": ["muscle_gain"]
    }
    sanitized = sanitize_user_data_for_logging(user_data)
    assert sanitized["age"] == "[REDACTED]"
    assert sanitized["weight"] == "[REDACTED]"
    assert sanitized["height"] == "[REDACTED]"
    assert sanitized["gender"] == "[REDACTED]"
    assert sanitized["fitness_level"] == "intermediate"
    assert sanitized["goals"] == ["muscle_gain"]
    print("✅ Test 11 passed: PII sanitization for logging")
    
    print("\n✅ All validator tests passed!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Testing Utility Modules")
    print("="*60)
    
    try:
        test_json_parser()
        test_validators()
        
        print("\n" + "="*60)
        print("✅ ALL UTILITY TESTS PASSED!")
        print("="*60)
        print("\nKey fixes verified:")
        print("  ✅ Shared JSON parser utility (DRY principle)")
        print("  ✅ Input validation and sanitization (Security)")
        print("  ✅ PII protection in logging (Security)")
        print("  ✅ Bounds checking and format validation")
        print("  ✅ Error handling with proper exceptions")
        
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Tests failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob