"""
History routes: view past assessments with filtering
"""
import os
import json
from flask import Blueprint, render_template
from .auth import login_required

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
@login_required
def history():
    """Render assessment history page with filters"""
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('history.html', firebase_config=firebase_config)
