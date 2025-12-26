from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request, session

def get_user_identifier():
    """Get user identifier for rate limiting. Uses Firebase UID from session, falls back to IP."""
    # Try to get Firebase user ID from session or request headers
    user_id = session.get('user_id')
    if user_id:
        return f"user:{user_id}"
    
    # Check for Firebase ID token in Authorization header (for API calls)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        # Extract user ID from token (simplified - in production, verify token)
        return f"token:{auth_header[7:50]}"  # Use first 43 chars of token as ID
    
    # Fallback to IP address
    return f"ip:{get_remote_address()}"

# Global limiter instance (initialized without app; init_app called in create_app)
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["100 per minute"],  # Increased limit for authenticated users
    storage_uri="memory://"
)
