from textblob import TextBlob
import extensions
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.book_utils import (
    prepare_book,
    prepare_books
)

books = Blueprint('books', __name__)


def clean_genre(genre_string):
    if not genre_string:
        return "Fiction"

    ignored = {
        "art",
        "books",
        "nonfiction",
        "fiction"
    }

    genres = [g.strip().lower() for g in genre_string.split(",")]

    for genre in genres:
        if genre not in ignored:
            return genre.title()

    return genres[0].title()


# HOME PAGE


@books.route('/')
def home():

    from extensions import mysql

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            id,
            COALESCE(NULLIF(original_title, ''), title) AS display_title,
            author,
            cover_url,
            genre,
            avg_rating,
            ratings_count
        FROM books
        WHERE avg_rating IS NOT NULL
        ORDER BY avg_rating DESC, ratings_count DESC
        LIMIT 12
    """)

    popular_books = cur.fetchall()

    for book in popular_books:
        book['display_genre'] = clean_genre(book['genre'])


    popular_books = prepare_books(popular_books)

    cur.close()

    return render_template(
        'home.html',
        popular_books=popular_books
    )



# BROWSE PAGE


@books.route('/browse')
def browse():

    from extensions import mysql

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    genre = request.args.get('genre', '').strip()
    sort = request.args.get('sort', '').strip()

    per_page = 20
    offset = (page - 1) * per_page

    cur = mysql.connection.cursor()

    base_query = """
        FROM books
        WHERE 1=1
    """

    params = []

    # SEARCH
    if search:

        base_query += """
            AND (
                LOWER(title) LIKE %s
                OR LOWER(author) LIKE %s
            )
        """

        search_term = f"%{search.lower()}%"

        params.extend([
            search_term,
            search_term
        ])

    # GENRE FILTER
    if genre:

        g = genre.lower().strip()

        base_query += """
        AND (
            LOWER(genre) = %s
            OR LOWER(genre) LIKE %s
            OR LOWER(genre) LIKE %s
            OR LOWER(genre) LIKE %s
        )
        """

        params.extend([
            g,
            f"{g},%",
            f"%,{g},%",
            f"%,{g}"
        ])

    # SORTING
    order_clause = " ORDER BY ratings_count DESC "

    if sort == "rating":
        order_clause = " ORDER BY avg_rating DESC "

    elif sort == "title":
        order_clause = " ORDER BY display_title ASC "

    elif sort == "popular":
        order_clause = " ORDER BY ratings_count DESC "

    # FETCH BOOKS
    books_query = f"""
        SELECT
            id,
            COALESCE(NULLIF(original_title, ''), title) AS display_title,
            author,
            cover_url,
            genre,
            avg_rating,
            ratings_count,
            year
        {base_query}
        {order_clause}
        LIMIT %s OFFSET %s
    """

    cur.execute(
        books_query,
        params + [per_page, offset]
    )

    books_list = cur.fetchall()

    for book in books_list:
        book['display_genre'] = clean_genre(book['genre'])

    books_list = prepare_books(books_list)

    # TOTAL COUNT
    count_query = f"""
        SELECT COUNT(*) as total
        {base_query}
    """

    cur.execute(count_query, params)

    total = cur.fetchone()['total']

    cur.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'browse.html',
        books=books_list,
        page=page,
        total_pages=total_pages,
        total=total,
        search=search,
        genre=genre,
        sort=sort
    )




# BOOK DETAIL PAGE
@books.route('/book/<int:book_id>')
def book_detail(book_id):

    from extensions import mysql

    cur = mysql.connection.cursor()

    # MAIN BOOK
    cur.execute("""
        SELECT
            id,
            COALESCE(NULLIF(original_title, ''), title) AS display_title,
            author,
            cover_url,
            description,
            genre,
            avg_rating,
            ratings_count,
            year,
            publisher
        FROM books
        WHERE id = %s
    """, (book_id,))

    book = cur.fetchone()

    # AUTO TRACK READING HISTORY

    if book and "user_id" in session:

        user_id = session["user_id"]

        # CHECK EXISTING
        cur.execute("""
            SELECT id
            FROM reading_history
            WHERE user_id = %s
            AND book_id = %s
        """, (
            user_id,
            book_id
        ))

        existing_history = cur.fetchone()

        # INSERT ONLY IF NOT EXISTS
        if not existing_history:

            cur.execute("""
                INSERT INTO reading_history (
                    user_id,
                    book_id,
                    status
                )
                VALUES (%s, %s, %s)
            """, (
                user_id,
                book_id,
                "explored"
            ))

        mysql.connection.commit()

    if book:
        book['display_genre'] = clean_genre(book['genre'])

    if not book:

        cur.close()

        return "Book not found", 404

    book = prepare_book(book)

        # TRACK VIEWED BOOKS

    if 'user_id' in session:

        # CHECK EXISTING VIEW

        cur.execute("""
            SELECT id
            FROM viewed_books
            WHERE user_id = %s
            AND book_id = %s
        """, (
            session['user_id'],
            book_id
        ))

        existing_view = cur.fetchone()

        if not existing_view:

            cur.execute("""
                INSERT INTO viewed_books (
                    user_id,
                    book_id
                )
                VALUES (%s, %s)
            """, (
                session['user_id'],
                book_id
            ))

            mysql.connection.commit()

            mysql.connection.commit()
    

    

    sentiment_label = "Neutral"
    sentiment_positive = 50
    sentiment_negative = 50

    recommended_books = []
    if book.get('description'):

        blob = TextBlob(book['description'])

        polarity = blob.sentiment.polarity

        sentiment_positive = round(
            ((polarity + 1) / 2) * 100
        )

        sentiment_negative = 100 - sentiment_positive

        if polarity > 0.1:
            sentiment_label = "Positive"

        elif polarity < -0.1:
            sentiment_label = "Negative"

        
        # ML RECOMMENDATION

        recommended_books = (
            extensions.content_recommender.recommend(book_id)
        )

        recommended_books = prepare_books(
            recommended_books
        )

    
    # SIMILAR BOOKS
    genre_value = ""

    if book['genre']:
        genre_value = clean_genre(book['genre'])

    cur.execute("""
        SELECT
            id,
            COALESCE(NULLIF(original_title, ''), title) AS display_title,
            author,
            cover_url,
            avg_rating
        FROM books
        WHERE id != %s
          AND LOWER(genre) LIKE %s
        ORDER BY avg_rating DESC, ratings_count DESC
        LIMIT 4
    """, (
        book_id,
        f"%{genre_value.lower()}%"
    ))

    similar_books = cur.fetchall()

    similar_books = prepare_books(similar_books)
    cur.close()

    return render_template(
    'book_detail.html',
    book=book,
    similar_books=similar_books,
    recommended_books=recommended_books,
    sentiment_label=sentiment_label,
    sentiment_positive=sentiment_positive,
    sentiment_negative=sentiment_negative,
   
)




# RATE BOOK

@books.route("/rate-book/<int:book_id>", methods=["POST"])
def rate_book(book_id):

    from extensions import mysql

    # LOGIN REQUIRED
    if "user_id" not in session:

        flash(
            "Please login to rate books.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    rating = request.form.get("rating")

    # VALIDATION
    if not rating or int(rating) not in [1, 2, 3, 4, 5]:

        flash(
            "Invalid rating.",
            "danger"
        )

        return redirect(
            url_for(
                "books.book_detail",
                book_id=book_id
            )
        )

    cur = mysql.connection.cursor()

    # CHECK EXISTING
    cur.execute("""
        SELECT id
        FROM ratings
        WHERE user_id = %s
          AND book_id = %s
    """, (
        user_id,
        book_id
    ))

    existing = cur.fetchone()

    # UPDATE
    if existing:

        cur.execute("""
            UPDATE ratings
            SET rating = %s
            WHERE user_id = %s
              AND book_id = %s
        """, (
            rating,
            user_id,
            book_id
        ))

    # INSERT
    else:

        cur.execute("""
            INSERT INTO ratings (
                user_id,
                book_id,
                rating,
                source
            )
            VALUES (%s, %s, %s, 'app')
        """, (
            user_id,
            book_id,
            rating
        ))

    mysql.connection.commit()

    cur.close()

    flash(
        "Rating saved successfully!",
        "success"
    )

    return redirect(
        url_for(
            "books.book_detail",
            book_id=book_id
        )
    )

