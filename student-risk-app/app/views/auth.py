"""
Authentication routes: login, signup, logout
"""
import os
import json
from flask import Blueprint, render_template, redirect, url_for, session, request
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, we rely on Firebase client-side auth
        # In production, validate Firebase ID tokens server-side
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    """Render login page"""
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('auth/login.html', firebase_config=firebase_config)

@auth_bp.route('/signup')
def signup():
    """Render signup page"""
    firebase_config = {
        'apiKey': os.getenv("FIREBASE_API_KEY"),
        'authDomain': os.getenv("FIREBASE_AUTH_DOMAIN"),
        'projectId': os.getenv("FIREBASE_PROJECT_ID"),
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET"),
        'messagingSenderId': os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        'appId': os.getenv("FIREBASE_APP_ID"),
        'measurementId': os.getenv("FIREBASE_MEASUREMENT_ID")
    }
    return render_template('auth/signup.html', firebase_config=firebase_config)

@auth_bp.route('/logout')
def logout():
    """Handle logout (Firebase client-side handles actual logout)"""
    return redirect(url_for('auth.login'))
