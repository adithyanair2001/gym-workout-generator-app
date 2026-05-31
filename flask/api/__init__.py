"""
API Blueprint for Gym Workout RAG
Handles all API endpoints for workout generation
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import routes

# Made with Bob
