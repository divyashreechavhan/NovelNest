from flask import Flask, render_template , request
import numpy as np
from flask_sqlalchemy import SQLAlchemy
import pickle
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user , UserMixin
from Model.model import db, User
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import distinct


app = Flask(__name__)


popular_df = pickle.load(open('top50.pkl' , 'rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))



app.config['SECRET_KEY'] = 'thisiskey'  # Change this to a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# db.init_app(app)

class User(db.Model , UserMixin):
    id  = db.Column(db.Integer , primary_key = True)
    username = db.Column(db.String(20) , nullable = False)
    password = db.Column(db.String(80) , nullable = False)
    interactions = db.relationship('Interaction', backref='user', lazy=True)
    preferred_genres = db.Column(db.String(100))
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_title = db.Column(db.String(100), nullable=False)
    book_image = db.Column(db.String(255))
    interaction_type = db.Column(db.String(20), nullable=False)  # e.g., 'saved', 'liked', 'saved'
    rating = db.Column(db.Float)


@app.route('/record_interaction', methods=['POST'])
@login_required
def record_interaction():
    book_title = request.form.get('book_title')
    book_image = request.form.get('book_image')
    interaction_type = request.form.get('interaction_type')
    rating = float(request.form.get('rating', 0))
    
    # Create an Interaction record based on interaction type
    interaction = Interaction(
        user=current_user,
        book_title=book_title,
        book_image=book_image,
        interaction_type=interaction_type,
        rating=rating if interaction_type == 'saved' else None
    )
    
    db.session.add(interaction)
    db.session.commit()
    
    return redirect(url_for('home'))  # Or wherever you want to redirect


@app.route('/profile')
@login_required
def profile():
    # Query user's interactions and preferences
    interactions = Interaction.query.filter_by(user_id=current_user.id).all()
    preferred_genres = current_user.preferred_genres
    
    # Generate live recommendations based on user's interactions and preferences
    recommended_books = generate_live_recommendations(interactions, preferred_genres)
    
    return render_template('profile.html', interactions=interactions, preferred_genres=preferred_genres, recommended_books=recommended_books)
 
def generate_live_recommendations(interactions, preferred_genres):
    recommended_books_set = set()
    saved_books = []  # To store the most recent saved book

    # Filter out only the saved interactions
    saved_interactions = [interaction for interaction in interactions if interaction.interaction_type == 'saved']
    
    # Find the most recent saved book
    if saved_interactions:
        most_recent_interaction = max(saved_interactions, key=lambda interaction: interaction.id)
        saved_books.append(most_recent_interaction.book_title)

    for interaction in interactions:
        if interaction.interaction_type == 'saved':
            book_title = interaction.book_title
            similar_books = get_similar_books(book_title)
            if book_title in saved_books:
                recommended_books_set.update([(book['book_name'], book['author'], book['image']) for book in similar_books])
            else:
                recommended_books_set.update([(book['book_name'], book['author'], book['image']) for book in similar_books][:2])  # Choose a smaller number of recommendations for older saved books
    
    recommended_books = list(recommended_books_set)
    return recommended_books


def get_similar_books(book_title):
    index = np.where(pt.index == book_title)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[0:5]
    
    recommended_books = []
    for i in similar_items:
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        recommended_books.append({
            'book_name': temp_df['Book-Title'].values[0],
            'author': temp_df['Book-Author'].values[0],
            'image': temp_df['Image-URL-M'].values[0]
        })
    
    return recommended_books

def remove_related_recommended_books(book_title, recommended_books):
    similar_books = get_similar_books(book_title)
    related_recommended_books = [book['book_name'] for book in similar_books]
    
    # Remove related recommended books from the list
    recommended_books = [book for book in recommended_books if book not in related_recommended_books]
    
    return recommended_books


@app.route('/remove_saved_book', methods=['POST'])
@login_required
def remove_saved_book():
    book_title = request.form.get('book_title')
    interaction = Interaction.query.filter_by(user=current_user, book_title=book_title, interaction_type='saved').first()
    if interaction:
        db.session.delete(interaction)
        db.session.commit()
        
        # Remove related recommended books from live recommendations
        recommended_books = generate_live_recommendations(current_user.interactions, current_user.preferred_genres)
        recommended_books = remove_related_recommended_books(book_title, recommended_books)
        
        # Update the user's live recommendations in the database
        user = User.query.get(current_user.id)
        user.live_recommendations = recommended_books
        db.session.commit()
        
    return redirect(url_for('profile'))



@app.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    preferred_genres = request.form.get('preferred_genres')
    current_user.preferred_genres = preferred_genres
    db.session.commit()
    return redirect(url_for('profile'))  # Or wherever you want to redirect


@app.route('/')
def base():
    return render_template('login.html')




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
     if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
     return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Modify the popular_df DataFrame to include a column for user ratings
popular_df['user_rating'] = 0.0
@app.route('/rate_book', methods=['POST'])
@login_required
def rate_book():
    book_title = request.form.get('book_title')
    rating = float(request.form.get('rating'))
    
    # Update user rating in the popular_df DataFrame
    index = popular_df[popular_df['Book-Title'] == book_title].index
    popular_df.at[index, 'user_rating'] = rating
    
    # Update user rating in the interactions table
    interaction = Interaction.query.filter_by(user=current_user, book_title=book_title).first()
    if interaction:
        interaction.rating = rating
        db.session.commit()
    
    return redirect(url_for('home'))

@app.route('/popular')
def popular():
    # Sort the popular_df DataFrame by user ratings in descending order
    book_names = list(popular_df['Book-Title'].values)
    authors = list(popular_df['Book-Author'].values)
    images = list(popular_df['Image-URL-M'].values)
    votes = list(popular_df['num_Ratings'].values)
    avg_ratings = list(popular_df['avg_Ratings'].values)
    user_ratings = []

    for book_name in book_names:
        # Retrieve all user ratings for the book
        interactions = Interaction.query.filter_by(book_title=book_name, interaction_type='rated').all()
        ratings = [interaction.rating for interaction in interactions]
        user_ratings.append(ratings)
    
    avg_user_ratings = []
    for ratings in user_ratings:
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            avg_rating = sum(valid_ratings) / len(valid_ratings)
            avg_user_ratings.append(avg_rating)
        else:
            avg_user_ratings.append(0)  
    return render_template('popular.html', book_name=book_names, author=authors, image=images, votes=votes, avg_rating=avg_ratings,    avg_user_ratings = avg_user_ratings
                           
, user_ratings=user_ratings)


@app.route('/home')
def home():
    
    return render_template('home.html' , 
                book_name = list(popular_df['Book-Title'].values),
                author = list(popular_df['Book-Author'].values),
                image = list(popular_df['Image-URL-M'].values),
                votes = list(popular_df['num_Ratings'].values),
                rating = list(popular_df['avg_Ratings'].values)
                )




# @app.route('/recommend')
# def recommend_ui():
#     interactions = Interaction.query.filter_by(user_id=current_user.id).all()
#     recommended_books = generate_live_recommendations(interactions, current_user.preferred_genres)

#     user_input = request.args.get('user_input')  # Retrieve user input from query parameter
#     data = []

#     if user_input:
#         index = np.where(pt.index == user_input)[0]
#         if len(index) > 0:
#             index = index[0]
#             similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

#             for i in similar_items:
#                 item = []
#                 temp_df = books[books['Book-Title'] == pt.index[i[0]]]
#                 item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
#                 item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
#                 item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
#                 data.append(item)

#     return render_template('recommendations.html', recommended_books=recommended_books, data=data)







@app.route('/recommend', methods=['GET', 'POST'])
def recommend_ui():
    interactions = Interaction.query.filter_by(user_id=current_user.id).all()
    recommended_books = generate_live_recommendations(interactions, current_user.preferred_genres)
    
    data = None
    
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

            data.append(item)

    return render_template('recommendations.html', recommended_books=recommended_books, data=data)




@app.route('/recommend_books',methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    print(data)

    return render_template('recommendations.html',data=data)




migrate = Migrate(app, db)
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'db':
        # Run the migration commands without starting the development server
        from flask_script import Manager
        from flask_migrate import Migrate, MigrateCommand

        migrate = Migrate(app, db)
        manager = Manager(app)

        manager.add_command('db', MigrateCommand)
        manager.run()
    else:
        with app.app_context():
            db.create_all()  # Create database tables
            app.run(debug=True)

# With this structure, when you run python app.py db init, python app.py db migrate, or python app.py db upgrade, the development server won't start. It will only start when you run python app.py without any additional arguments. Make sure you have the necessary Flask-Migrate and Flask-Script packages installed (flask-migrate and flask-script) for this to work.






