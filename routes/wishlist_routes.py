from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session
)

from extensions import mysql

import re

wishlist_bp = Blueprint(
    'wishlist',
    __name__
)


# ADD TO WISHLIST

@wishlist_bp.route("/wishlist/add/<int:book_id>", methods=["POST"])
def add_to_wishlist(book_id):

    from extensions import mysql

    # LOGIN REQUIRED
    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    cur = mysql.connection.cursor()

    # CHECK EXISTING
    cur.execute("""
        SELECT id
        FROM wishlist
        WHERE user_id = %s
        AND book_id = %s
    """, (
        user_id,
        book_id
    ))

    existing = cur.fetchone()

    if existing:

        flash(
            "Book already in wishlist.",
            "info"
        )

    else:

        cur.execute("""
            INSERT INTO wishlist (
                user_id,
                book_id
            )
            VALUES (%s, %s)
        """, (
            user_id,
            book_id
        ))

        mysql.connection.commit()

        flash(
            "Added to wishlist successfully!",
            "success"
        )

    cur.close()

    return redirect(
        url_for(
            "books.book_detail",
            book_id=book_id
        )
    )

# WISHLIST PAGE

@wishlist_bp.route("/wishlist")
def wishlist():

    from extensions import mysql

    # LOGIN REQUIRED
    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            books.id,
            COALESCE(
                NULLIF(books.original_title, ''),
                books.title
            ) AS display_title,
            books.author,
            books.cover_url,
            books.avg_rating
        FROM wishlist
        JOIN books
            ON wishlist.book_id = books.id
        WHERE wishlist.user_id = %s
        ORDER BY wishlist.id DESC
    """, (user_id,))

    wishlist_books = cur.fetchall()

    # CLEAN DATA
    for b in wishlist_books:

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
        "wishlist.html",
        wishlist_books=wishlist_books
    )

# REMOVE FROM WISHLIST

@wishlist_bp.route(
    "/wishlist/remove/<int:book_id>",
    methods=["POST"]
)
def remove_from_wishlist(book_id):

    from extensions import mysql

    # LOGIN REQUIRED
    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    cur = mysql.connection.cursor()

    cur.execute("""
        DELETE FROM wishlist
        WHERE user_id = %s
        AND book_id = %s
    """, (
        user_id,
        book_id
    ))

    mysql.connection.commit()

    cur.close()

    flash(
        "Book removed from wishlist.",
        "success"
    )

    return redirect(
        url_for("wishlist.wishlist")
    )
