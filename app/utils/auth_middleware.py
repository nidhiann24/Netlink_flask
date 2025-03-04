from flask import request, jsonify
from functools import wraps
import jwt
from app.models import Users
from config import Config

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('x-access-tokens')
        if not token:
            return jsonify({'message': 'A valid token is missing'}), 401
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = Users.query.filter_by(public_id=data['public_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorator

def admin_required(f):
    @wraps(f)
    def decorator(current_user, *args, **kwargs):
        if not current_user.admin:
            return jsonify({'message': 'You do not have permission to access this resource'}), 403
        return f(current_user, *args, **kwargs)
    return decorator
