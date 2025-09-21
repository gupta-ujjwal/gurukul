#!/usr/bin/env python3
"""
Test script for the course ingestion functionality.
Uses the virtual environment and tests the regex-based parsing.
"""
import os
import sys
import json
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ingestion_service():
    """Test the ingestion service directly."""
    logger.info("Testing ingestion service directly...")
    
    try:
        from src.services.ingestion import extract_text_from_pdf, parse_chapter_with_regex
        
        # Test with one of the sample PDFs
        pdf_path = "learning_materials/Class 11/Physics/keph101.pdf"
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return False
        
        # Extract text
        logger.info("Extracting text from PDF...")
        raw_text = extract_text_from_pdf(pdf_path)
        logger.info(f"Extracted {len(raw_text)} characters")
        
        # Parse with regex
        logger.info("Parsing chapter with regex...")
        parsed_chapter = parse_chapter_with_regex(raw_text)
        
        logger.info(f"Successfully parsed chapter {parsed_chapter.chapter_number}: {parsed_chapter.title}")
        logger.info(f"Found {len(parsed_chapter.sections)} sections")
        
        for i, section in enumerate(parsed_chapter.sections[:3]):  # Show first 3 sections
            logger.info(f"  Section {i+1}: {section.section_number} - {section.title}")
            logger.info(f"    Text length: {len(section.text)} characters")
        
        logger.info("✓ Direct ingestion service test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Direct ingestion service test failed: {e}")
        return False

def test_api_endpoint():
    """Test the API endpoint with a real HTTP request."""
    logger.info("Testing API endpoint...")
    
    try:
        # Get admin key from environment
        admin_key = os.getenv("SUPER_ADMIN_KEY")
        if not admin_key:
            logger.error("SUPER_ADMIN_KEY not found in environment")
            return False
        
        # API endpoint
        url = "http://localhost:5000/admin/ingest_course"
        
        # Request data
        data = {
            "course_name": "Physics",
            "board": "CBSE",
            "grade": 11,
            "pdf_paths": [
                "learning_materials/Class 11/Physics/keph101.pdf",
                "learning_materials/Class 11/Physics/keph102.pdf"
            ]
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Key": admin_key
        }
        
        logger.info("Sending request to API endpoint...")
        
        # Make request (this will fail if server is not running)
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✓ API endpoint test passed")
            logger.info(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error(f"✗ API endpoint test failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.warning("API endpoint test skipped - server not running")
        logger.info("Start the server with: source .venv/bin/activate && python src/apis/app.py")
        return None
    except Exception as e:
        logger.error(f"✗ API endpoint test failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("Starting course ingestion tests...")
    
    # Test 1: Direct service test
    service_test_passed = test_ingestion_service()
    
    # Test 2: API endpoint test
    api_test_passed = test_api_endpoint()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"Direct Service Test: {'✓ PASSED' if service_test_passed else '✗ FAILED'}")
    
    if api_test_passed is None:
        logger.info("API Endpoint Test: ⚠ SKIPPED (server not running)")
    else:
        logger.info(f"API Endpoint Test: {'✓ PASSED' if api_test_passed else '✗ FAILED'}")
    
    if service_test_passed:
        logger.info("\n✓ Core ingestion functionality is working!")
        if api_test_passed is None:
            logger.info("To test the API endpoint, start the server and run this script again.")
    else:
        logger.info("\n✗ Core ingestion functionality has issues.")
    
    return service_test_passed and (api_test_passed or api_test_passed is None)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)