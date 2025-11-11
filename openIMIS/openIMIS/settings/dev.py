import os

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Set ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://192.168.0.1',
    'http://localhost:8000',
    'http://192.168.0.1:8000',
    'http://localhost:3000',
    'http://192.168.0.1:3000',
]
# Set CORS_ALLOWED_ORIGINS to match CSRF_TRUSTED_ORIGINS
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS

# Note: CSRF settings are automatically managed in security.py based on ENVIRONMENT variable
# For development: ENVIRONMENT=dev (default)
# For production: ENVIRONMENT=prod

ASYNC = os.environ.get('ASYNC', False)
