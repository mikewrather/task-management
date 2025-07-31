#!/usr/bin/env python3
"""Fix test imports after package reorganization"""

import os
import re
from pathlib import Path


def fix_imports_in_file(filepath: Path) -> bool:
    """Fix imports in a single file"""
    content = filepath.read_text()
    original_content = content
    
    # Fix patterns
    replacements = [
        # Fix src. prefix - we use package imports
        (r'from src\.voice_task_manager', 'from voice_task_manager'),
        (r'import src\.voice_task_manager', 'import voice_task_manager'),
        
        # Fix specific module names
        (r'\.integrations\.google_drive import GoogleDriveIntegration', 
         '.integrations.drive import GoogleDriveClient'),
        
        (r'\.core\.transcription import VoiceTranscriber',
         '.integrations.whisper import WhisperIntegration'),
         
        # Fix CLI test import
        (r'from voice_task_manager\.cli import main, status, analyze, setup, cleanup, test, process',
         'from voice_task_manager.cli import main, status, analyze, setup, cleanup, process'),
         
        # Fix test_integrations references
        (r'from test_integrations', 'from integration'),
        (r'import test_integrations', 'import integration'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        filepath.write_text(content)
        return True
    return False


def main():
    """Fix all test imports"""
    project_root = Path(__file__).parent.parent.parent
    test_dir = project_root / "tests"
    
    fixed_count = 0
    
    for test_file in test_dir.rglob("*.py"):
        if fix_imports_in_file(test_file):
            print(f"Fixed imports in: {test_file.relative_to(project_root)}")
            fixed_count += 1
    
    print(f"\n✅ Fixed imports in {fixed_count} files")


if __name__ == "__main__":
    main()