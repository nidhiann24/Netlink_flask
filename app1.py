from flask import Flask, jsonify, make_response, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
import jwt as pyjwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '004f2af45d3a4e161a7dd2d17fdae47f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///MoviesAndDirectors.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)  # Fixed: String instead of Integer
    name = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(255))
    admin = db.Column(db.Boolean, default=False)

class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    movies = db.relationship('Movie', backref='director',cascade='all, delete')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('director.id'), nullable=False)


with app.app_context():
    db.create_all()

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('x-access-tokens')
        if not token:
            return jsonify({'message': 'A valid token is missing'}), 401
        
        try:
            data = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Users.query.filter_by(public_id=data['public_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)  # Pass user
    return decorator

def accesss(f):
    @wraps(f)
    def decorator(current_user, *args, **kwargs):
        if not current_user.admin:
            return jsonify({'message': 'You do not have permission to access this resource'}), 403
        return f(current_user, *args, **kwargs)
    return decorator

@app.route('/register', methods=['POST'])
def signup_user(): 
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    new_user = Users(
        public_id=str(uuid.uuid4()), 
        name=data['name'], 
        password=hashed_password, 
        admin=bool(data.get('admin', False))  # Fixed: Ensure Boolean
    )
    db.session.add(new_user) 
    db.session.commit()   
    return jsonify({'message': 'Registered successfully'})

@app.route('/login', methods=['POST'])
def login_user():
    auth = request.authorization  
    user = Users.query.filter_by(name=auth.username).first()
    if user and check_password_hash(user.password, auth.password):
        token = pyjwt.encode(
            {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},
            app.config['SECRET_KEY'], algorithm="HS256"
        )
        return jsonify({'token': token, 'admin': user.admin})  # Fixed: Return admin status
    return make_response('Could not verify', 401)

# CRUD Routes

# Create Director
@app.route('/Director', methods=['POST'])
@token_required
@accesss
def add_director(current_user):  # Accept current_user as an argument
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
@token_required
@accesss
def add_movie(current_user):  # Accept current_user as an argument
    data = request.get_json()
    director = db.session.query(Director).get(data['director_id'])
    if not director:
        return jsonify({"message": "Director not found"}), 404

    new_movie = Movie(title=data['title'], director_id=data['director_id'])
    if not new_movie.title or not new_movie.director_id:
        return jsonify({'message': 'Movie title and director_id are required'}), 400
    if new_movie.title:
        if not db.session.query(Movie).filter(Movie.title == new_movie.title).count():
            db.session.add(new_movie)
            db.session.commit()
            return jsonify({"message": "Movie added successfully", "Movie": {"id": new_movie.id, "title": new_movie.title, "director_id": new_movie.director_id}}), 201
        else:
            return jsonify({'message': 'Movie already exists'}), 400
# Read all Directors
@app.route('/Director', methods=['GET'])
@token_required
def get_directors(current_user):  # Accept current_user as an argument
    directors = db.session.query(Director).all()
    director_list = [{"id": d.id, "name": d.name} for d in directors]
    return jsonify({"Directors": director_list})

# Read single Director
@app.route('/Director/<int:director_id>', methods=['GET'])
@token_required
def get_director(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404
    return jsonify({"id": director.id, "name": director.name})

# Read all Movies
@app.route('/Movie', methods=['GET'])
@token_required
def get_movies(current_user):  # Accept current_user as an argument
    movies = db.session.query(Movie).all()
    movie_list = [{"id": m.id, "title": m.title, "director_id": m.director_id, "director_name": m.director.name} for m in movies]
    return jsonify({"Movies": movie_list})

# Read single Movie
@app.route('/Movie/<int:movie_id>', methods=['GET'])
@token_required
def get_movie(current_user,movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404
    return jsonify({"id": movie.id, "title": movie.title, "director_id": movie.director_id, "director_name": movie.director.name})

@app.route('/Director/<int:director_id>/Movies', methods=['GET'])
@token_required
def get_director_movies(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    movies = Movie.query.filter_by(director_id=director_id).all()
    movie_list = [{"id": m.id, "title": m.title, "director_id": m.director_id, "director_name": m.director.name} for m in movies]
    return jsonify({"Movies": movie_list})

# Update Director
@app.route('/Director/<int:director_id>', methods=['PUT'])
@token_required
@accesss
def update_director(current_user,director_id):
    director = db.session.query(Director).get(director_id)
    if not director:
        return jsonify({"message": "Director not found"}), 404

    data = request.get_json()
    director.name = data.get("name", director.name)
    db.session.commit()
    return jsonify({"message": "Director updated successfully!", "Director": {"id": director.id, "name": director.name}})

# Update Movie
@app.route('/Movie/<int:movie_id>', methods=['PUT'])
@token_required
@accesss
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

# Delete Director (only if no movies exist)
@app.route('/Director/<int:director_id>', methods=['DELETE'])
@token_required
@accesss
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

# Delete Movie
@app.route('/Movie/<int:movie_id>', methods=['DELETE'])
@token_required
@accesss
def delete_movie(current_user,movie_id):
    movie = db.session.query(Movie).get(movie_id)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Movie deleted successfully!"})

@app.route('/Director/<int:director_id>/Movies', methods=['DELETE'])
@token_required
@accesss
def delete_director_movies(current_user,director_id):
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
