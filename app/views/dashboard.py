"""
Dashboard routes: user home page with stats and recent activity
"""
import os
import json
from flask import Blueprint, render_template
from .auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Render user dashboard with stats and recent profiles"""
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('dashboard.html', firebase_config=firebase_config)
