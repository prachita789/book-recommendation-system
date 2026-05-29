from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for
)

from extensions import mysql

from utils.helpers import prepare_books

onboarding_bp = Blueprint(
    'onboarding',
    __name__
)


# STEP 1
@onboarding_bp.route(
    '/onboarding',
    methods=['GET', 'POST']
)
def onboarding():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # SEARCH
    search = request.args.get('search', '')

    if search:

        cur.execute("""
            SELECT
                id,
                title,
                original_title,
                author,
                cover_url,
                avg_rating
            FROM books
            WHERE
                title LIKE %s
                OR author LIKE %s
            LIMIT 12
        """, (
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cur.execute("""
            SELECT
                id,
                title,
                original_title,
                author,
                cover_url,
                avg_rating
            FROM books
            ORDER BY ratings_count DESC, RAND()
            LIMIT 12
        """)

    books = prepare_books(
        cur.fetchall()
    )

    # SAVE STEP 1
    if request.method == 'POST':

        selected_books = request.form.getlist(
            'selected_books'
        )

        for book_id in selected_books:

            # CHECK IF ALREADY EXISTS
            cur.execute("""
                SELECT id FROM reading_history
                WHERE user_id = %s
                AND book_id = %s
            """, (session['user_id'], book_id))

            existing = cur.fetchone()

            if not existing:

                cur.execute("""
                    INSERT INTO reading_history
                    (user_id, book_id, status)
                    VALUES (%s, %s, %s)
                """, (
                    session['user_id'],
                    book_id,
                    'interested'
                ))

        mysql.connection.commit()
        cur.close()

        return redirect(
            url_for('onboarding.preferences')
        )

    cur.close()

    return render_template(
        'onboarding.html',
        books=books,
        search=search,
        step=1
    )


# STEP 2
@onboarding_bp.route(
    '/onboarding/preferences',
    methods=['GET', 'POST']
)
def preferences():

    if 'user_id' not in session:
        return redirect('/login')

    moods = [
        'Adventure',
        'Romance',
        'Fantasy',
        'Mystery',
        'Self Help',
        'Fiction',
        'Dark',
        'Inspirational',
        'Thoughtful'
    ]

    if request.method == 'POST':

        selected_moods = request.form.getlist(
            'moods'
        )

        cur = mysql.connection.cursor()

        for mood in selected_moods:

            cur.execute("""
                INSERT INTO user_preferences
                (
                    user_id,
                    preference_type,
                    preference_value
                )
                VALUES (%s, %s, %s)
            """, (
                session['user_id'],
                'mood',
                mood
            ))

        mysql.connection.commit()
        cur.close()

        return redirect('/dashboard')

    return render_template(
        'onboarding.html',
        moods=moods,
        step=2
    )