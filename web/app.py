from flask import Flask, send_from_directory, request, abort, jsonify
import os


app = Flask(__name__)

# Simple token-based auth (replace with your preferred method)
VALID_TOKENS = {
    "your-secret-token",
    "campaign-admin-2024",
    "protected-access-key"
}


def is_authenticated():
    """Check if the request has a valid authentication token."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    
    # Support both "Bearer token" and "token" formats
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
    else:
        token = auth_header
    return token in VALID_TOKENS


# Serve static files from the www subdirectory
@app.route('/')
def index():
    return send_from_directory('www', 'index.html')


@app.route('/images/public/<path:filename>')
def public_images(filename):
    """Serve public images - no authentication required."""
    return send_from_directory('www/images/public', filename)


@app.route('/images/protected/<path:filename>')
def protected_images(filename):
    """Serve protected images only to authenticated users."""
    if not is_authenticated():
        abort(401, description="Authentication required.")
    
    protected_path = os.path.join('www', 'images', 'protected', filename)
    if not os.path.exists(protected_path):
        abort(404, description="Protected image not found.")
    
    return send_from_directory('www/images/protected', filename)


@app.route('/<path:filename>')
def other_static_files(filename):
    """Serve other static files (CSS, JS, etc.) but block direct access to images directories."""
    # Block direct access to images directories - use specific endpoints instead
    if filename.startswith('images/'):
        abort(403, description="Access denied. Use /images/public/ or /images/protected/ endpoints.")
    
    return send_from_directory('www', filename)


@app.route('/auth/verify')
def verify_token():
    """Endpoint to verify if a token is valid."""
    if is_authenticated():
        return jsonify({"status": "valid", "message": "Token is valid"})
    else:
        return jsonify({
            "status": "invalid",
            "message": "Invalid or missing token"
        }), 401


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "error": "Unauthorized",
        "message": "Authentication required. Include valid token in Authorization header.",
        "example": "Authorization: Bearer your-secret-token"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "error": "Forbidden",
        "message": "Access denied to protected resources.",
        "hint": "Use /protected/images/ endpoint with authentication."
    }), 403


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
