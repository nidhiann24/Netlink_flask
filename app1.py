from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure a single SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MoviesAndDirectors.db'  # Single DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)

# Director Model
class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    movies = db.relationship('Movie', backref='director', cascade='all, delete')  # One-to-Many Relationship

# Movie Model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('director.id'), nullable=False)

# Initialize Database
with app.app_context():
    db.create_all()

# CRUD Routes

# Create Director
@app.route('/Director', methods=['POST'])
def add_director():
    data = request.get_json()
    new_director = Director(name=data['name'])
    if new_director.name:
        if not db.session.query(Director).filter(Director.name == new_director.name).count():
            db.session.add(new_director)
            db.session.commit()
            return jsonify({'message': 'Director added successfully'}), 201
        else:
            return jsonify({'message': 'Director already exists'}), 400
    else:
        return jsonify({'message': 'Director name is required'}), 400
    
# Create Movie
@app.route('/Movie', methods=['POST'])
def add_movie():
    data = request.get_json()
    director = db.session.query(Director).get(data['director_id'])
    if not director:
        return jsonify({"message": "Director not found"}), 404

    new_movie = Movie(title=data['title'], director_id=data['director_id'])
    db.session.add(new_movie)
    db.session.commit()
    return jsonify({"message": "Movie added successfully", "Movie": {"id": new_movie.id, "title": new_movie.title, "director_id": new_movie.director_id}}), 201

# Read all Directors
@app.route('/Director', methods=['GET'])
def get_directors():
    directors = db.session.query(Director).all()
    director_list = [{"id": d.id, "name": d.name} for d in directors]
    return jsonify({"Directors": director_list})

# Read single Director
@app.route('/Director/<int:director_id>', methods=['GET'])
def get_director(director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404
    return jsonify({"id": director.id, "name": director.name})

# Read all Movies
@app.route('/Movie', methods=['GET'])
def get_movies():
    movies = db.session.query(Movie).all()
    movie_list = [{"id": m.id, "title": m.title, "director_id": m.director_id, "director_name": m.director.name} for m in movies]
    return jsonify({"Movies": movie_list})

# Read single Movie
@app.route('/Movie/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404
    return jsonify({"id": movie.id, "title": movie.title, "director_id": movie.director_id, "director_name": movie.director.name})

@app.route('/Director/<int:director_id>/Movies', methods=['GET'])
def get_director_movies(director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    movies = Movie.query.filter_by(director_id=director_id).all()
    movie_list = [{"id": m.id, "title": m.title, "director_id": m.director_id, "director_name": m.director.name} for m in movies]
    return jsonify({"Movies": movie_list})

# Update Director
@app.route('/Director/<int:director_id>', methods=['PUT'])
def update_director(director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    data = request.get_json()
    director.name = data.get("name", director.name)
    db.session.commit()
    return jsonify({"message": "Director updated successfully!", "Director": {"id": director.id, "name": director.name}})

# Update Movie
@app.route('/Movie/<int:movie_id>', methods=['PUT'])
def update_movie(movie_id):
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

# Delete Director (only if no movies exist)
@app.route('/Director/<int:director_id>', methods=['DELETE'])
def delete_director(director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    #if db.session.query(Movie).filter(Movie.director_id == director_id).count():
    #    return jsonify({"message": "Director has movies, cannot delete"}), 400
    db.session.delete(director)
    db.session.commit()
    return jsonify({"message": "Director deleted successfully!"})

# Delete Movie
@app.route('/Movie/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movie deleted successfully!"})

@app.route('/Director/<int:director_id>/Movies', methods=['DELETE'])
def delete_director_movies(director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    movies = db.session.query(Movie).filter(Movie.director_id == director_id).all()
    for movie in movies:
        db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movies deleted successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
