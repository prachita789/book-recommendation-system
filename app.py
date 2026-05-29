from flask import Flask
from config import Config
from extensions import mysql 
import extensions
from ml.content_based import ContentBasedRecommender
from routes.onboarding_routes import onboarding_bp
import os
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

app = Flask(
    __name__,
    template_folder=os.path.join(base_path, 'templates'),
    static_folder=os.path.join(base_path, 'static')
)
app.config.from_object(Config)

mysql.init_app(app)

# LOAD CONTENT RECOMMENDER ONCE

with app.app_context():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            id,
            COALESCE(NULLIF(original_title, ''), title) AS title,
            author,
            genre,
            description,
            cover_url
        FROM books
    """)

    all_books = cur.fetchall()

    cur.close()

    extensions.content_recommender = ContentBasedRecommender(all_books)


from routes.auth_routes import auth
from routes.book_routes import books
from routes.recommendation_routes import recommendations
from routes.mood_routes import mood_bp
from routes.wishlist_routes import wishlist_bp

app.register_blueprint(auth)
app.register_blueprint(books)
app.register_blueprint(recommendations)
app.register_blueprint(mood_bp)
app.register_blueprint(wishlist_bp)
app.register_blueprint(onboarding_bp)
if __name__ == '__main__':
    app.run(debug=True)




