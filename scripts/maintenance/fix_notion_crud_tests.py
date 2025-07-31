#!/usr/bin/env python3
"""Fix test_notion_crud.py patch decorators and indentation"""

import re
from pathlib import Path

def fix_notion_crud_tests():
    """Fix all the patch decorators and indentation in test_notion_crud.py"""
    
    file_path = Path("/home/mike/development/task-management/tests/integration/test_notion_crud.py")
    content = file_path.read_text()
    
    # First pass: Remove all @patch decorators and their parameters from function signatures
    # Pattern to match @patch decorator and the corresponding parameter in function
    content = re.sub(r'    @patch\([\'"]requests\.(post|patch|get)[\'"]\)\n', '', content)
    
    # Remove mock parameters from function signatures
    content = re.sub(r', mock_(post|patch|get)(?=,|\))', '', content)
    content = re.sub(r'mock_(post|patch|get), ', '', content)
    
    # Second pass: Fix the with statements and indentation
    # This is more complex, we need to find patterns and fix them
    
    # Pattern for fixing mock_post.return_value = mock_response followed by code
    def fix_mock_usage(match):
        indent = match.group(1)
        mock_type = match.group(2)
        response_var = match.group(3)
        code_block = match.group(4)
        
        # Add proper indentation to the code block
        indented_code = '\n'.join(f"    {line}" if line.strip() else line 
                                  for line in code_block.strip().split('\n'))
        
        return f"""{indent}
{indent}with patch.object(notion_client.session, '{mock_type}', return_value={response_var}) as mock_{mock_type}:
{indent}    {indented_code}"""
    
    # Fix patterns where mock_x.return_value = mock_response is followed by code
    pattern = r'(\s+)mock_(post|patch|get)\.return_value = (mock_response)\s*\n\s*\n((?:(?!\n\s*@|\n\s*def|\n\s*#).*\n)*)'
    content = re.sub(pattern, fix_mock_usage, content)
    
    # Third pass: Fix assert_called_once indentation
    content = re.sub(r'^(\s+)mock_(post|patch|get)\.assert_called_once\(\)$', 
                     r'        \1mock_\2.assert_called_once()', 
                     content, flags=re.MULTILINE)
    
    # Save the fixed content
    file_path.write_text(content)
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    fix_notion_crud_tests()