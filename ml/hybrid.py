from collections import defaultdict

from extensions import mysql
import extensions


# Weights for the four signals when a user HAS ratings.
# They should sum to ~1.0. Mood gets a real seat at the table.
W_CONTENT    = 0.40
W_MOOD       = 0.20
W_RATING     = 0.20
W_POPULARITY = 0.20

# Books with fewer ratings than this don't get a popularity boost.
POPULARITY_FLOOR = 100


def _normalize_rating(r):
    """0..5 stars -> 0..1"""
    if not r:
        return 0.0
    return min(max(float(r) / 5.0, 0.0), 1.0)


def _normalize_popularity(count):
    """Log-scale 0..1 — log10(count) capped at 6 (1M ratings)."""
    if not count or count < POPULARITY_FLOOR:
        return 0.0
    import math
    return min(math.log10(count) / 6.0, 1.0)


def _normalize_content(score, max_score):
    """The content recommender returns weighted scores in arbitrary
    ranges (we multiplied by user's rating). Normalize against the
    highest score we saw in this batch."""
    if not max_score:
        return 0.0
    return min(score / max_score, 1.0)


def _get_user_moods(cur, user_id):
    cur.execute("""
        SELECT preference_value
        FROM user_preferences
        WHERE user_id = %s
          AND preference_type = 'mood'
    """, (user_id,))
    return {row["preference_value"].lower() for row in cur.fetchall()}


def _cold_start(cur, user_moods, top_n):
    """User has no ratings. Recommend by mood + quality."""
    if not user_moods:
        # No moods either — return empty so the route falls through to
        # global popular books.
        return []

    placeholders = ", ".join(["%s"] * len(user_moods))
    cur.execute(f"""
        SELECT
            id, original_title, title, author, genre,
            cover_url, avg_rating, ratings_count, mood_tag
        FROM books
        WHERE LOWER(mood_tag) IN ({placeholders})
          AND avg_rating IS NOT NULL
          AND ratings_count >= %s
        ORDER BY avg_rating DESC, ratings_count DESC
        LIMIT 200
    """, (*user_moods, POPULARITY_FLOOR))

    candidates = cur.fetchall()

    # De-duplicate by clean title (drop subtitles after the colon).
    seen, unique = set(), []
    for b in candidates:
        key = (b["title"] or "").split(":")[0].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(b)

    # Score = normalized rating + normalized popularity.
    for b in unique:
        rating_n = _normalize_rating(b.get("avg_rating"))
        pop_n = _normalize_popularity(b.get("ratings_count"))
        b["hybrid_score"] = round(0.7 * rating_n + 0.3 * pop_n, 4)

    unique.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return unique[:top_n]


def get_hybrid_recommendations(user_id, top_n=8):
    cur = mysql.connection.cursor()

    user_moods = _get_user_moods(cur, user_id)

    # User's highly-rated books drive content-based scoring.
    cur.execute("""
        SELECT book_id, rating
        FROM ratings
        WHERE user_id = %s
          AND rating >= 4
          AND source = 'app'
    """, (user_id,))
    rated_books = cur.fetchall()

    # ---------- COLD START ----------
    if not rated_books:

        # Get onboarding-selected books
        cur.execute("""
        SELECT book_id
        FROM reading_history
        WHERE user_id = %s
          AND status = 'interested'
        """, (user_id,))

        selected_books = cur.fetchall()

        # If no selected books, fallback to mood-based cold start
        if not selected_books:
            result = _cold_start(cur, user_moods, top_n)
            cur.close()
            return result

        # Generate similarity scores from onboarding selections
        raw_scores = defaultdict(float)

        for item in selected_books:

            for rec in extensions.content_recommender.recommend(
                    item["book_id"], top_n=15):

                raw_scores[rec["id"]] += rec["score"]

        # Remove already selected books
        selected_ids = {
            item["book_id"]
            for item in selected_books
        }

        candidates = [
            {"book_id": bid, "raw_content": s}
            for bid, s in raw_scores.items()
            if bid not in selected_ids
        ]

        if not candidates:
            result = _cold_start(cur, user_moods, top_n)
            cur.close()
            return result

        # Sort by similarity
        candidates.sort(
            key=lambda x: x["raw_content"],
            reverse=True
        )

        candidates = candidates[: top_n * 3]

        max_content = candidates[0]["raw_content"] or 1.0

        # Fetch book details
        ids = [c["book_id"] for c in candidates]

        placeholders = ", ".join(["%s"] * len(ids))

        cur.execute(f"""
            SELECT
                id, original_title, title, author, genre,
                cover_url, avg_rating, ratings_count, mood_tag
            FROM books
            WHERE id IN ({placeholders})
        """, tuple(ids))

        by_id = {
            row["id"]: row
            for row in cur.fetchall()
        }

        # Final scoring
        final = []

        for c in candidates:

            book = by_id.get(c["book_id"])

            if not book:
                continue

            content_n = _normalize_content(
                c["raw_content"],
                max_content
            )

            rating_n = _normalize_rating(
                book.get("avg_rating")
            )

            pop_n = _normalize_popularity(
                book.get("ratings_count")
            )

            mood_tag = (
                book.get("mood_tag") or ""
            ).lower()

            mood_n = (
                1.0 if mood_tag in user_moods
                else 0.3
            )

            score = (
                W_CONTENT * content_n +
                W_MOOD * mood_n +
                W_RATING * rating_n +
                W_POPULARITY * pop_n
            )

            book["hybrid_score"] = round(score, 4)

            final.append(book)

        final.sort(
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        cur.close()

        return final[:top_n]

    # ---------- WARM USER ----------
    # 1) Collect content-similarity scores from each rated book.
    raw_scores = defaultdict(float)
    for item in rated_books:
        for rec in extensions.content_recommender.recommend(
                item["book_id"], top_n=15):
            raw_scores[rec["id"]] += rec["score"] * item["rating"]

    # 2) Drop books the user already rated.
    rated_ids = {item["book_id"] for item in rated_books}
    candidates = [
        {"book_id": bid, "raw_content": s}
        for bid, s in raw_scores.items()
        if bid not in rated_ids
    ]

    if not candidates:
        cur.close()
        return _cold_start(cur, user_moods, top_n)

    # 3) Take the top ~3x for fetching, then re-rank with full signal.
    candidates.sort(key=lambda x: x["raw_content"], reverse=True)
    candidates = candidates[: top_n * 3]
    max_content = candidates[0]["raw_content"] or 1.0

    # 4) Batch-fetch book details (one query, not N).
    ids = [c["book_id"] for c in candidates]
    placeholders = ", ".join(["%s"] * len(ids))
    cur.execute(f"""
        SELECT
            id, original_title, title, author, genre,
            cover_url, avg_rating, ratings_count, mood_tag
        FROM books
        WHERE id IN ({placeholders})
    """, tuple(ids))
    by_id = {row["id"]: row for row in cur.fetchall()}

    # 5) Score every candidate on normalized 0-1 signals, then combine.
    final = []
    for c in candidates:
        book = by_id.get(c["book_id"])
        if not book:
            continue

        content_n = _normalize_content(c["raw_content"], max_content)
        rating_n  = _normalize_rating(book.get("avg_rating"))
        pop_n     = _normalize_popularity(book.get("ratings_count"))

        mood_tag = (book.get("mood_tag") or "").lower()
        mood_n   = 1.0 if mood_tag in user_moods else 0.0

        score = (W_CONTENT    * content_n +
                 W_MOOD       * mood_n    +
                 W_RATING     * rating_n  +
                 W_POPULARITY * pop_n)

        book["hybrid_score"] = round(score, 4)
        final.append(book)

    final.sort(key=lambda x: x["hybrid_score"], reverse=True)
    cur.close()
    return final[:top_n]
