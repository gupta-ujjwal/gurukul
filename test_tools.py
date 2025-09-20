#!/usr/bin/env python3
"""
Test script to verify that the LangGraph tools are properly integrated with the PostgreSQL database.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing Tool Database Integration...")
    print("=" * 50)
    
    print("\n📋 Testing Imports...")
    try:
        from ContextClass import LearningContext, LearningState
        from ToolFactory import LEARNING_TOOLS, get_current_context, set_current_context
        from config.database import get_db
        from models import Student, Progress, Course, Section
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_database_connection():
    """Test database connection."""
    print("\n📋 Testing Database Connection...")
    try:
        from config.database import get_db
        from sqlalchemy import text
        
        # get_db() is a generator, so we need to get the session from it
        db_generator = get_db()
        db = next(db_generator)
        
        # Test basic query
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("✅ Database connection successful")
            # Don't close here - the generator will handle it
            return True
        else:
            print("❌ Database query failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False

def test_context_class():
    """Test LearningContext with database integration."""
    print("\n📋 Testing LearningContext Database Integration...")
    try:
        from ContextClass import LearningContext
        
        # Create a test context
        context = LearningContext(
            user_id="test_user",
            session_id="test_session"
        )
        
        # Test progress update (should save to database)
        context.update_progress("Chapter 1", "Section 1", 85)
        print("✅ Progress update successful")
        
        # Test progress summary (should read from database)
        summary = context.get_progress_summary()
        if "Your Progress" in summary:
            print("✅ Progress summary successful")
            return True
        else:
            print("❌ Progress summary failed")
            return False
            
    except Exception as e:
        print(f"❌ LearningContext test error: {str(e)}")
        return False

def test_tools():
    """Test that tools can be invoked with database integration."""
    print("\n📋 Testing Tools Database Integration...")
    try:
        from ToolFactory import LEARNING_TOOLS, set_current_context
        from ContextClass import LearningContext
        
        # Set up context
        context = LearningContext(
            user_id="test_user", 
            session_id="test_session"
        )
        set_current_context(context)
        
        # Test get_course tool
        get_course_tool = None
        for tool in LEARNING_TOOLS:
            if hasattr(tool, 'name') and tool.name == "get_course":
                get_course_tool = tool
                break
        
        if get_course_tool:
            result = get_course_tool.invoke({})
            if "Course:" in result:
                print("✅ get_course tool working")
            else:
                print("❌ get_course tool failed")
                return False
        
        # Test view_progress tool
        view_progress_tool = None
        for tool in LEARNING_TOOLS:
            if hasattr(tool, 'name') and tool.name == "view_progress":
                view_progress_tool = tool
                break
        
        if view_progress_tool:
            result = view_progress_tool.invoke({})
            if "Your Progress" in result or "No progress" in result:
                print("✅ view_progress tool working")
            else:
                print("❌ view_progress tool failed")
                return False
        
        # Test update_progress tool
        update_progress_tool = None
        for tool in LEARNING_TOOLS:
            if hasattr(tool, 'name') and tool.name == "update_progress":
                update_progress_tool = tool
                break
        
        if update_progress_tool:
            result = update_progress_tool.invoke({
                "chapter": "Chapter 1",
                "section": "Section 1", 
                "score": 90
            })
            if "Progress updated" in result:
                print("✅ update_progress tool working")
            else:
                print("❌ update_progress tool failed")
                return False
        
        print("✅ All tools working with database integration")
        return True
        
    except Exception as e:
        print(f"❌ Tools test error: {str(e)}")
        return False

def main():
    """Run all tests."""
    tests = [
        test_imports,
        test_database_connection,
        test_context_class,
        test_tools
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Tools are properly integrated with the database.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)