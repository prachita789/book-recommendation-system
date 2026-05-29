from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)

from extensions import mysql
from ml.hybrid import get_hybrid_recommendations
from utils.book_utils import prepare_books


recommendations = Blueprint("recommendations", __name__)


@recommendations.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    cur = mysql.connection.cursor()

    # --- STATS ---
    cur.execute("""
        SELECT COUNT(*) AS total
        FROM ratings
        WHERE user_id = %s AND source = 'app'
    """, (user_id,))
    ratings_count = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM wishlist
        WHERE user_id = %s
    """, (user_id,))
    wishlist_count = cur.fetchone()["total"]

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM reading_history
        WHERE user_id = %s
        AND status = 'explored'
    """, (user_id,))
    reading_count = cur.fetchone()["total"]

    # --- HYBRID RECOMMENDATIONS ---
    recommended_books = get_hybrid_recommendations(user_id)

    # Fallback if hybrid returns nothing (no ratings AND no moods).
    if not recommended_books:
        cur.execute("""
            SELECT
                id, original_title, title, author, genre,
                cover_url, avg_rating, ratings_count, mood_tag
            FROM books
            WHERE avg_rating IS NOT NULL
              AND ratings_count >= 100
            ORDER BY avg_rating DESC, ratings_count DESC
            LIMIT 8
        """)
        recommended_books = cur.fetchall()

    # Run every book through prepare_books so clean_title / clean author /
    # cover fallback are all set consistently for the template.
    recommended_books = prepare_books(recommended_books)

    # Add a `display_rating` field the template uses.
    for b in recommended_books:
        b["display_rating"] = round(float(b.get("avg_rating") or 0), 1)

    # --- RECENTLY VIEWED ---
    cur.execute("""
        SELECT
            b.id, b.original_title, b.title, b.author,
            b.cover_url, b.avg_rating
        FROM viewed_books v
        JOIN books b ON v.book_id = b.id
        WHERE v.user_id = %s
        GROUP BY b.id
        ORDER BY MAX(v.viewed_at) DESC
        LIMIT 6
    """, (user_id,))
    recently_viewed = prepare_books(cur.fetchall())

    for b in recently_viewed:
        b["display_rating"] = round(float(b.get("avg_rating") or 0), 1)

    cur.close()

    return render_template(
        "dashboard.html",
        ratings_count=ratings_count,
        wishlist_count=wishlist_count,
        reading_count=reading_count,
        recommended_books=recommended_books,
        recently_viewed=recently_viewed,
    )
