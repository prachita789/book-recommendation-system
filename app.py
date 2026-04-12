from flask import Flask
from flask_mysqldb import MySQL
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)


from routes.auth_routes import auth
from routes.book_routes import books
from routes.recommendation_routes import recommendations

app.register_blueprint(auth)
app.register_blueprint(books)
app.register_blueprint(recommendations)

if __name__ == '__main__':
    app.run(debug=True)