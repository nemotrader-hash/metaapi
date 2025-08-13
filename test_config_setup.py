#!/usr/bin/env python3
"""
Test script to verify configuration setup is working correctly.
"""

import json
import os
import sys
from pathlib import Path

def test_config_files():
    """Test that all configuration files are properly set up."""
    
    print("🧪 Testing Configuration Setup...")
    print("=" * 50)
    
    # Test 1: Check if template exists
    template_file = Path("config.template.json")
    if template_file.exists():
        print("✅ config.template.json exists")
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            print("✅ config.template.json is valid JSON")
            
            # Check for placeholder values
            if "YOUR_" in template_data.get("secret_key", ""):
                print("✅ Template contains placeholder values (safe)")
            else:
                print("⚠️  Template might contain real values")
                
        except json.JSONDecodeError:
            print("❌ config.template.json has invalid JSON")
    else:
        print("❌ config.template.json not found")
    
    # Test 2: Check if test config exists
    test_file = Path("config.test.json")
    if test_file.exists():
        print("✅ config.test.json exists")
        try:
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            print("✅ config.test.json is valid JSON")
            
            # Check for test values
            if "test" in test_data.get("secret_key", "").lower():
                print("✅ Test config contains test values (safe)")
            else:
                print("⚠️  Test config might contain real values")
                
        except json.JSONDecodeError:
            print("❌ config.test.json has invalid JSON")
    else:
        print("❌ config.test.json not found")
    
    # Test 3: Check if actual config exists
    config_file = Path("config.json")
    if config_file.exists():
        print("✅ config.json exists")
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            print("✅ config.json is valid JSON")
            
            # Check for required fields
            required_fields = ["secret_key", "telegram_bot_token", "telegram_chat_id"]
            missing_fields = [field for field in required_fields if not config_data.get(field)]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
        except json.JSONDecodeError:
            print("❌ config.json has invalid JSON")
    else:
        print("⚠️  config.json not found (create it from template)")
    
    # Test 4: Check gitignore
    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        with open(gitignore_file, 'r') as f:
            gitignore_content = f.read()
        
        if "config.json" in gitignore_content:
            print("✅ config.json is in .gitignore")
        else:
            print("❌ config.json is NOT in .gitignore (security risk!)")
    else:
        print("❌ .gitignore file not found")
    
    # Test 5: Check if config.json is tracked by git
    try:
        import subprocess
        result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
        if result.returncode == 0:
            tracked_files = result.stdout
            if "config.json" in tracked_files:
                print("❌ config.json is tracked by git (security risk!)")
            else:
                print("✅ config.json is NOT tracked by git")
        else:
            print("⚠️  Could not check git status")
    except Exception:
        print("⚠️  Git not available or not a git repository")
    
    print("\n🎯 Summary:")
    print("- Use config.template.json to create your config.json")
    print("- Use config.test.json for testing with dummy values")
    print("- Your config.json with real secrets is safely ignored by git")
    print("- See SETUP.md for detailed setup instructions")
    
def test_config_loading():
    """Test that the configuration manager can load configs."""
    
    print("\n🔧 Testing Configuration Loading...")
    print("=" * 50)
    
    try:
        sys.path.insert(0, '.')
        from config.config_manager import ConfigManager
        
        # Test loading test config
        try:
            config_manager = ConfigManager("config.test.json")
            config = config_manager.get_config()
            print("✅ Successfully loaded config.test.json")
            print(f"   - Secret key: {config.secret_key[:10]}..." if config.secret_key else "   - No secret key")
            print(f"   - Debug mode: {config.debug}")
            print(f"   - Port: {config.port}")
        except Exception as e:
            print(f"❌ Failed to load config.test.json: {e}")
        
        # Test loading actual config if it exists
        if Path("config.json").exists():
            try:
                config_manager = ConfigManager("config.json")
                config = config_manager.get_config()
                print("✅ Successfully loaded config.json")
                print(f"   - Secret key: {config.secret_key[:10]}..." if config.secret_key else "   - No secret key")
                print(f"   - Debug mode: {config.debug}")
                print(f"   - Port: {config.port}")
            except Exception as e:
                print(f"❌ Failed to load config.json: {e}")
        else:
            print("⚠️  config.json not found - create it from template")
            
    except ImportError as e:
        print(f"❌ Could not import config manager: {e}")

if __name__ == "__main__":
    test_config_files()
    test_config_loading()
    print("\n🎉 Configuration test complete!")
