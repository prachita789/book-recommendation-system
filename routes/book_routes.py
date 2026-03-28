from flask import Blueprint, render_template

books = Blueprint('books', __name__)

@books.route('/browse')
def browse():
    return render_template('browse.html')

@books.route('/mood')
def mood():
    return render_template('mood_filter.html')

@books.route('/compare')
def compare():
    return render_template('comparison.html')