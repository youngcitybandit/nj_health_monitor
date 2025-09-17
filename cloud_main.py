#!/usr/bin/env python3
"""
Cloud Run compatible main file for NJ Health Facility Monitor.
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "NJ Health Facility Monitor",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint."""
    return jsonify({
        "status": "test_successful",
        "message": "PolicyEdge AI Monitor is running!",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/check', methods=['POST'])
def run_check():
    """Main check endpoint."""
    return jsonify({
        "status": "success",
        "message": "Check endpoint working",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
