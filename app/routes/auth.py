from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from app import db
from app.models import Users
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def signup_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    new_user = Users(
        public_id=str(uuid.uuid4()), 
        name=data['name'], 
        password=hashed_password, 
        admin=bool(data.get('admin', False))
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'})

@auth_bp.route('/login', methods=['POST'])
def login_user():
    auth = request.authorization  
    user = db.session.query(Users).filter_by(name=auth.username).first()
    if user and check_password_hash(user.password, auth.password):
        token = jwt.encode(
            {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},
            Config.SECRET_KEY, algorithm="HS256"
        )
        return jsonify({'token': token, 'admin': user.admin})
    return jsonify({'message': 'Could not verify'}), 401
