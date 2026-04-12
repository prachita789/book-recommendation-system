from flask import Blueprint, render_template, request
from flask_mysqldb import MySQL


books = Blueprint('books', __name__)

@books.route('/browse')
def browse():
    from app import mysql
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    genre = request.args.get('genre', '')
    per_page = 12

    cur = mysql.connection.cursor()

    # Build query based on search and filter
    if search:
        query = """SELECT * FROM books 
                   WHERE title LIKE %s 
                   OR author LIKE %s
                   LIMIT %s OFFSET %s"""
        search_term = f'%{search}%'
        cur.execute(query, (search_term, search_term, 
                           per_page, (page-1)*per_page))
    else:
        query = """SELECT * FROM books 
                   LIMIT %s OFFSET %s"""
        cur.execute(query, (per_page, (page-1)*per_page))

    books_list = cur.fetchall()

    # Get total count for pagination
    if search:
        cur.execute("""SELECT COUNT(*) as total FROM books 
                      WHERE title LIKE %s OR author LIKE %s""",
                   (f'%{search}%', f'%{search}%'))
    else:
        cur.execute("SELECT COUNT(*) as total FROM books")

    total = cur.fetchone()['total']
    cur.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template('browse.html',
                         books=books_list,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         total=total)