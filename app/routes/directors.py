from flask import Blueprint, request, jsonify
from app import db
from app.models import db, Director, Movie
from app.utils.auth_middleware import token_required, admin_required

director_bp = Blueprint('director', __name__)

@director_bp.route('/Director', methods=['POST'])
@token_required
@admin_required
def add_director(current_user):
    data = request.get_json()
    new_director = Director(name=data['name'])
    if db.session.query(Director).filter_by(name=new_director.name).count() == 0:
        db.session.add(new_director)
        db.session.commit()
        return jsonify({'message': 'Director added successfully'}), 201
    return jsonify({'message': 'Director already exists'}), 400

@director_bp.route('/Director', methods=['GET'])
@token_required
def get_directors(current_user):  # Accept current_user as an argument
    directors = db.session.query(Director).all()
    director_list = [{"id": d.id, "name": d.name} for d in directors]
    return jsonify({"Directors": director_list})

@director_bp.route('/Director/<int:director_id>', methods=['GET'])
@token_required
def get_director(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404
    return jsonify({"id": director.id, "name": director.name})

@director_bp.route('/Director/<int:director_id>', methods=['PUT'])
@token_required
@admin_required
def update_director(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    data = request.get_json()
    director.name = data.get("name", director.name)
    db.session.commit()
    return jsonify({"message": "Director updated successfully!", "Director": {"id": director.id, "name": director.name}})

@director_bp.route('/Director/<int:director_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_director(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    if db.session.query(Movie).filter(Movie.director_id == director_id).count():
        db.session.delete(director)
        db.session.commit()
        return jsonify({"message": "Director has movies, both director and movie deleted"}), 400
        

    db.session.delete(director)
    db.session.commit()
    return jsonify({"message": "Director deleted successfully!"})
