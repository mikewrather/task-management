#!/usr/bin/env python3
"""Check and enforce project structure standards"""

import os
import sys
from pathlib import Path
from typing import List, Tuple


class ProjectStructureChecker:
    """Verify project follows Python best practices"""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.issues: List[str] = []
        self.warnings: List[str] = []
    
    def check_root_cleanliness(self) -> None:
        """Ensure no Python scripts in root directory"""
        root_files = list(self.root.glob("*.py"))
        allowed_root_files = {"notion_mcp_server.py"}  # MCP server is special
        
        for file in root_files:
            if file.name not in allowed_root_files:
                self.issues.append(f"Python script in root: {file.name}")
    
    def check_package_structure(self) -> None:
        """Verify src layout is used"""
        src_dir = self.root / "src" / "voice_task_manager"
        
        if not src_dir.exists():
            self.issues.append("Missing src/voice_task_manager package directory")
            return
        
        # Check for __init__.py files
        for subdir in ["adapters", "core", "integrations", "models", "processors", "utils"]:
            init_file = src_dir / subdir / "__init__.py"
            if not init_file.exists():
                self.issues.append(f"Missing __init__.py in {subdir}")
    
    def check_test_structure(self) -> None:
        """Verify test organization"""
        test_dir = self.root / "tests"
        
        if not test_dir.exists():
            self.issues.append("Missing tests directory")
            return
        
        # Check for proper test subdirectories
        for subdir in ["unit", "integration", "e2e"]:
            sub_path = test_dir / subdir
            if not sub_path.exists():
                self.warnings.append(f"Missing tests/{subdir} directory")
    
    def check_scripts_organization(self) -> None:
        """Verify scripts are properly organized"""
        scripts_dir = self.root / "scripts"
        
        if not scripts_dir.exists():
            self.issues.append("Missing scripts directory")
            return
        
        # Check for proper subdirectories
        for subdir in ["debug", "analysis", "maintenance"]:
            sub_path = scripts_dir / subdir
            if not sub_path.exists():
                self.warnings.append(f"Missing scripts/{subdir} directory")
            elif not (sub_path / "README.md").exists():
                self.warnings.append(f"Missing README.md in scripts/{subdir}")
    
    def check_dependencies(self) -> None:
        """Verify modern dependency management"""
        # Should use pyproject.toml, not requirements.txt
        if (self.root / "requirements.txt").exists():
            self.issues.append("Found requirements.txt - should use pyproject.toml with uv")
        
        if not (self.root / "pyproject.toml").exists():
            self.issues.append("Missing pyproject.toml")
        
        if not (self.root / "uv.lock").exists():
            self.warnings.append("Missing uv.lock file")
    
    def check_type_hints(self) -> None:
        """Check for type hint configuration"""
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.mypy]" not in content:
                self.warnings.append("No mypy configuration in pyproject.toml")
    
    def run_all_checks(self) -> Tuple[List[str], List[str]]:
        """Run all structure checks"""
        self.check_root_cleanliness()
        self.check_package_structure()
        self.check_test_structure()
        self.check_scripts_organization()
        self.check_dependencies()
        self.check_type_hints()
        
        return self.issues, self.warnings


def main():
    """Run structure checks and report results"""
    project_root = Path(__file__).parent.parent.parent
    checker = ProjectStructureChecker(project_root)
    
    issues, warnings = checker.run_all_checks()
    
    if issues:
        print("❌ Project Structure Issues:")
        for issue in issues:
            print(f"  - {issue}")
        print()
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ Project structure follows Python best practices!")
        return 0
    
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())