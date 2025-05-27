"""
Routes package initialization.

This package contains all the route definitions for the application.
"""
from flask import Blueprint

# Create a Blueprint for the API routes
bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes after creating the blueprint to avoid circular imports
from . import verteil_flights
