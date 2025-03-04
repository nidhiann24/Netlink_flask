from flask import Blueprint, request, jsonify
from app import db
from app.models import Movie, Director
from app.utils.auth_middleware import token_required, admin_required

movie_bp = Blueprint('movie', __name__)

@movie_bp.route('/Movie', methods=['POST'])
@token_required
@admin_required
def add_movie(current_user):
    data = request.get_json()
    director = db.session.query(Director).get(data['director_id'])
    if not director:
        return jsonify({"message": "Director not found"}), 404

    new_movie = Movie(title=data['title'], director_id=data['director_id'])
    if db.session.query(Movie).filter_by(title=new_movie.title).count() == 0:
        db.session.add(new_movie)
        db.session.commit()
        return jsonify({"message": "Movie added successfully"}), 201
    return jsonify({'message': 'Movie already exists'}), 400

# Read all Movies
@movie_bp.route('/Movie', methods=['GET'])
@token_required
def get_movies(current_user):  # Accept current_user as an argument
    movies = db.session.query(Movie).all()
    movie_list = [{"id": m.id, "title": m.title, "director_id": m.director_id, "director_name": m.director.name} for m in movies]
    return jsonify({"Movies": movie_list})

# Read single Movie
@movie_bp.route('/Movie/<int:movie_id>', methods=['GET'])
@token_required
def get_movie(current_user,movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404
    return jsonify({"id": movie.id, "title": movie.title, "director_id": movie.director_id, "director_name": movie.director.name})

@movie_bp.route('/Director/<int:director_id>/Movies', methods=['GET'])
@token_required
def get_director_movies(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    movies = Movie.query.filter_by(director_id=director_id).all()
    movie_list = [{"id": m.id, "title": m.title, "director_id": m.director_id, "director_name": m.director.name} for m in movies]
    return jsonify({"Movies": movie_list})

# Update Movie
@movie_bp.route('/Movie/<int:movie_id>', methods=['PUT'])
@token_required
@admin_required
def update_movie(current_user,movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404

    data = request.get_json()
    movie.title = data.get("title", movie.title)
    movie.director_id = data.get("director_id", movie.director_id)

    director = db.session.query(Director).get(movie.director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    db.session.commit()
    return jsonify({"message": "Movie updated successfully!", "Movie": {"id": movie.id, "title": movie.title, "director_id": movie.director_id}})

# Delete Movie
@movie_bp.route('/Movie/<int:movie_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_movie(current_user,movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movie deleted successfully!"})

@movie_bp.route('/Director/<int:director_id>/Movies', methods=['DELETE'])
@token_required
@admin_required
def delete_director_movies(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    movies = db.session.query(Movie).filter(Movie.director_id == director_id).all()
    for movie in movies:
        db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movies deleted successfully!"})
