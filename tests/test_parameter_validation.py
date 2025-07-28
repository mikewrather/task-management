"""
Tests for parameter validation system

Tests the intelligent parameter validation and help system for query commands.
"""

import pytest
from unittest.mock import Mock, patch

from src.voice_task_manager.core.parameter_validator import (
    ParameterValidator, 
    ParameterValidationError
)


class TestParameterValidator:
    """Test parameter validation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = ParameterValidator()
    
    def test_validate_status_tasks_valid(self):
        """Test valid task status validation"""
        result = self.validator.validate_status("Inbox", "tasks")
        assert result == "Inbox"
        
        result = self.validator.validate_status("Next Action", "tasks")
        assert result == "Next Action"
    
    def test_validate_status_tasks_invalid(self):
        """Test invalid task status validation raises error with suggestions"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_status("invalid", "tasks")
        
        error = exc_info.value
        assert "invalid" in error.message
        assert "not a valid tasks status" in error.message
        assert "Inbox" in error.valid_options
        assert "Next Action" in error.valid_options
        assert len(error.examples) > 0
    
    def test_validate_status_projects_valid(self):
        """Test valid project status validation"""
        result = self.validator.validate_status("In Progress", "projects")
        assert result == "In Progress"
        
        result = self.validator.validate_status("Not Started", "projects")
        assert result == "Not Started"
    
    def test_validate_status_projects_invalid(self):
        """Test invalid project status validation"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_status("invalid", "projects")
        
        error = exc_info.value
        assert "not a valid projects status" in error.message
        assert "In Progress" in error.valid_options
        assert "Not Started" in error.valid_options
    
    def test_validate_priority_valid(self):
        """Test valid priority validation"""
        for priority in ["Low", "Medium", "High", "Urgent"]:
            result = self.validator.validate_priority(priority)
            assert result == priority
    
    def test_validate_priority_case_insensitive(self):
        """Test priority validation is case-insensitive"""
        result = self.validator.validate_priority("high")
        assert result == "High"
        
        result = self.validator.validate_priority("MEDIUM")
        assert result == "Medium"
    
    def test_validate_priority_invalid(self):
        """Test invalid priority validation"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_priority("invalid")
        
        error = exc_info.value
        assert "not a valid priority level" in error.message
        assert all(p in error.valid_options for p in ["Low", "Medium", "High", "Urgent"])
    
    def test_validate_energy_valid(self):
        """Test valid energy validation"""
        for energy in ["Low", "Medium", "High", "Extreme"]:
            result = self.validator.validate_energy(energy)
            assert result == energy
    
    def test_validate_energy_case_insensitive(self):
        """Test energy validation is case-insensitive"""
        result = self.validator.validate_energy("extreme")
        assert result == "Extreme"
    
    def test_validate_energy_invalid(self):
        """Test invalid energy validation"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_energy("invalid")
        
        error = exc_info.value
        assert "not a valid energy level" in error.message
        assert all(e in error.valid_options for e in ["Low", "Medium", "High", "Extreme"])
    
    def test_validate_context_valid(self):
        """Test valid context validation"""
        result = self.validator.validate_context("voice")
        assert result == "voice"
        
        result = self.validator.validate_context("Computer")
        assert result == "Computer"
    
    def test_validate_context_case_insensitive(self):
        """Test context validation is case-insensitive"""
        result = self.validator.validate_context("computer")
        assert result == "Computer"
        
        result = self.validator.validate_context("PHONE")
        assert result == "Phone"
    
    def test_validate_context_invalid(self):
        """Test invalid context validation"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_context("invalid")
        
        error = exc_info.value
        assert "not a valid context" in error.message
        assert "voice" in error.valid_options
        assert "Computer" in error.valid_options
    
    def test_validate_date_iso_format(self):
        """Test ISO date format validation"""
        from datetime import datetime
        
        result = self.validator.validate_date("2025-07-25")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 7
        assert result.day == 25
    
    def test_validate_date_natural_language(self):
        """Test natural language date parsing"""
        from datetime import datetime
        
        result = self.validator.validate_date("today")
        assert isinstance(result, datetime)
        
        result = self.validator.validate_date("yesterday")
        assert isinstance(result, datetime)
        
        result = self.validator.validate_date("7 days ago")
        assert isinstance(result, datetime)
    
    def test_validate_date_invalid(self):
        """Test invalid date validation"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_date("invalid date")
        
        error = exc_info.value
        assert "Could not parse date" in error.message
        assert "invalid date" in error.message
        assert any("ISO format" in opt for opt in error.valid_options)
    
    def test_fuzzy_matching_suggestions(self):
        """Test fuzzy matching provides close suggestions"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_status("inbox", "tasks")  # lowercase
        
        error = exc_info.value
        # Should suggest "Inbox" as close match
        assert "Did you mean 'Inbox'?" in error.message
        
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_priority("Hihg")  # typo close to "High"
        
        error = exc_info.value
        # Should suggest "High" as close match
        assert "Did you mean" in error.message
    
    def test_error_message_format(self):
        """Test error messages follow consistent format"""
        with pytest.raises(ParameterValidationError) as exc_info:
            self.validator.validate_status("invalid", "tasks")
        
        error = exc_info.value
        assert error.message.startswith("'invalid' is not a valid")
        assert len(error.valid_options) > 0
        assert len(error.examples) > 0
        
        # Check examples contain actual CLI command examples
        for example in error.examples:
            assert "vtm" in example
            assert "--status=" in example or "--priority=" in example or "--energy=" in example


class TestParameterValidationIntegration:
    """Integration tests for parameter validation in CLI context"""
    
    @patch('src.voice_task_manager.core.parameter_validator.Console')
    def test_display_validation_error_formatting(self, mock_console_class):
        """Test error display formatting uses Rich console properly"""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        validator = ParameterValidator()
        
        try:
            validator.validate_status("invalid", "tasks")
        except ParameterValidationError as e:
            validator.display_validation_error(e)
        
        # Should have called console.print for error message, options, and examples
        assert mock_console.print.call_count >= 3
        
        # Check that error styling was used
        calls = mock_console.print.call_args_list
        error_call = calls[0]
        assert "❌ Error:" in str(error_call)
        assert "style=\"red\"" in str(error_call) or "style='red'" in str(error_call)
    
    def test_option_descriptions_provided(self):
        """Test that help options include descriptive text"""
        validator = ParameterValidator()
        
        # Test that status descriptions are available
        description = validator._get_option_description("Inbox")
        assert description == "new, unprocessed items"
        
        description = validator._get_option_description("High", "priority")
        assert description == "important, soon"  # Priority High description
        
        description = validator._get_option_description("Extreme", "energy")
        assert description == "high focus, complex work"
    
    def test_grouped_context_display(self):
        """Test that contexts are grouped logically for display"""
        validator = ParameterValidator()
        
        contexts = ["Phone", "Computer", "Home", "Email", "voice", "auto-processed"]
        
        # This tests the internal grouping logic
        # We can't easily test the actual display without mocking Rich console
        # but we can verify the grouping data structure exists
        assert hasattr(validator, '_display_grouped_options')
        
        # The method should handle the common context groupings
        validator._display_grouped_options(contexts)  # Should not raise exception