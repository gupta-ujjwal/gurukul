"""
Admin routes for course ingestion and management.
"""
import logging
from flask import Blueprint, request, jsonify
from typing import List, Dict, Any

from ..services.ingestion import ingest_course_from_pdfs, validate_admin_key

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/ingest_course', methods=['POST'])
def ingest_course():
    """
    Admin endpoint to ingest course content from PDF files.
    
    Expected JSON body:
    {
        "course_name": "Physics",
        "board": "CBSE", 
        "grade": 11,
        "pdf_paths": ["/path/to/keph101.pdf", "/path/to/keph102.pdf"]
    }
    
    Returns:
        JSON response with ingestion results
    """
    try:
        # Validate admin key
        admin_key = request.headers.get('X-Admin-Key')
        if not admin_key:
            logger.warning("Missing X-Admin-Key header")
            return jsonify({
                'success': False,
                'message': 'Admin key required'
            }), 401
        
        if not validate_admin_key(admin_key):
            logger.warning("Invalid admin key provided")
            return jsonify({
                'success': False,
                'message': 'Invalid admin key'
            }), 403
        
        # Parse request data
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided")
            return jsonify({
                'success': False,
                'message': 'JSON data required'
            }), 400
        
        # Validate required fields
        required_fields = ['course_name', 'board', 'grade', 'pdf_paths']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        course_name = data['course_name'].strip()
        board = data['board'].strip()
        grade = data['grade']
        pdf_paths = data['pdf_paths']
        
        # Validate field values
        if not course_name:
            return jsonify({
                'success': False,
                'message': 'Course name cannot be empty'
            }), 400
        
        if not board:
            return jsonify({
                'success': False,
                'message': 'Board cannot be empty'
            }), 400
        
        if not isinstance(grade, int) or grade < 1 or grade > 12:
            return jsonify({
                'success': False,
                'message': 'Grade must be an integer between 1 and 12'
            }), 400
        
        if not isinstance(pdf_paths, list) or len(pdf_paths) == 0:
            return jsonify({
                'success': False,
                'message': 'pdf_paths must be a non-empty list'
            }), 400
        
        # Validate each PDF path
        for pdf_path in pdf_paths:
            if not isinstance(pdf_path, str) or not pdf_path.strip():
                return jsonify({
                    'success': False,
                    'message': 'All PDF paths must be non-empty strings'
                }), 400
        
        logger.info(f"Starting course ingestion: {course_name} ({board} Grade {grade})")
        logger.info(f"PDF files to process: {len(pdf_paths)}")
        
        # Perform ingestion
        results = ingest_course_from_pdfs(
            course_name=course_name,
            board=board,
            grade=grade,
            pdf_paths=pdf_paths
        )
        
        logger.info(f"Course ingestion completed: {results}")
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Course ingestion completed',
            'data': {
                'course_id': results['course_id'],
                'chapters_ingested': results['chapters_ingested'],
                'sections_ingested': results['sections_ingested'],
                'failed_files': results['failed_files']
            }
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in course ingestion: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@admin_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for admin routes.
    """
    return jsonify({
        'success': True,
        'message': 'Admin routes are operational'
    })