from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Global limiter instance (initialized without app; init_app called in create_app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"],  # Global default per-IP
    storage_uri="memory://"
)
