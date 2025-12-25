"""
Other routes: about, settings, landing page
"""
import os
import json
from flask import Blueprint, render_template
from .auth import login_required

other_bp = Blueprint('other', __name__)

@other_bp.route('/about')
@login_required
def about():
    """Render about/help page"""
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('about.html', firebase_config=firebase_config)

@other_bp.route('/settings')
@login_required
def settings():
    """Render user settings page"""
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('settings.html', firebase_config=firebase_config)

@other_bp.route('/landing')
def landing():
    """Render marketing landing page (public - no auth required)"""
    return render_template('landing.html')
