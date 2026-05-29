from flask import (
    Blueprint,
    render_template,
    request,
    session
)

from extensions import mysql

import re

from ml.mood_recommender import (
    calculate_mood_score
)

mood_bp = Blueprint(
    'mood',
    __name__
)


# MOOD FILTER PAGE

@mood_bp.route('/mood')
def mood():

    from extensions import mysql

    selected_mood = request.args.get(
        'mood',
        ''
    ).strip().lower()

    cur = mysql.connection.cursor()

    # AVAILABLE MOODS
    cur.execute("""
        SELECT DISTINCT mood_tag
        FROM books
        WHERE mood_tag IS NOT NULL
          AND mood_tag != ''
        ORDER BY mood_tag ASC
    """)

    mood_rows = cur.fetchall()

    moods = [
        row['mood_tag']
        for row in mood_rows
        if row['mood_tag']
    ]

    books_list = []

    # FILTERED BOOKS
    if selected_mood:
                # SAVE MOOD HISTORY
        if session.get('user_id'):

            cur.execute("""
                INSERT INTO mood_history (
                    user_id,
                    mood
                )
                VALUES (%s, %s)
            """, (
                session['user_id'],
                selected_mood
            ))

            mysql.connection.commit()

        cur.execute("""
            SELECT
                id,
                COALESCE(
                    NULLIF(original_title, ''),
                    title
                ) AS display_title,
                author,
                cover_url,
                avg_rating,
                mood_tag
            FROM books
            WHERE LOWER(mood_tag) = %s
            ORDER BY avg_rating DESC,
                     ratings_count DESC
            LIMIT 20
        """, (selected_mood,))

        books_list = cur.fetchall()

        # CLEAN DATA
        for b in books_list:

            # TITLE
            if b['display_title']:

                b['clean_title'] = re.sub(
                    r"\s*\(.*?\)",
                    "",
                    b['display_title']
                ).strip()

            else:
                b['clean_title'] = "Untitled"

            # AUTHOR
            if b['author']:

                b['author'] = re.sub(
                    r"[\[\]']",
                    "",
                    b['author']
                )

            else:
                b['author'] = "Unknown"

            # COVER
            if (
                not b['cover_url']
                or any(
                    x in str(b['cover_url']).lower()
                    for x in [
                        'nophoto',
                        'no_cover',
                        'default'
                    ]
                )
            ):

                b['cover_url'] = None

    cur.close()

    return render_template(
        'mood.html',
        moods=moods,
        selected_mood=selected_mood,
        books=books_list
    )
