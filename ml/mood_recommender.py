from textblob import TextBlob


# Moods where positive sentiment in the description is a GOOD signal.
POSITIVE_MOODS = {"romance", "inspirational", "self help", "adventure"}

# Moods where negative / heavy sentiment is the right signal.
NEGATIVE_MOODS = {"dark", "mystery", "thoughtful"}

# Moods where sentiment doesn't help much either way.
NEUTRAL_MOODS  = {"fantasy", "fiction"}


def _normalize_rating(r):
    if not r:
        return 0.0
    return min(max(float(r) / 5.0, 0.0), 1.0)


def calculate_mood_score(book, selected_mood):
    
    mood = (selected_mood or "").lower().strip()
    book_mood = (book.get("mood_tag") or "").lower().strip()

    # --- Mood tag match (0 or 1) ---
    mood_match = 1.0 if book_mood == mood else 0.0

    # --- Sentiment alignment (0..1) ---
    description = book.get("description") or ""
    sentiment = 0.0
    if description:
        try:
            polarity = TextBlob(description).sentiment.polarity
        except Exception:
            polarity = 0.0

        if mood in POSITIVE_MOODS:
            # Want positive polarity (0..1)
            sentiment = max(polarity, 0.0)
        elif mood in NEGATIVE_MOODS:
            # Want negative polarity (we flip the sign so it becomes 0..1)
            sentiment = max(-polarity, 0.0)
        else:
            # Neutral moods — sentiment doesn't matter, give half credit
            # to avoid penalizing books just because they're neutral.
            sentiment = 0.5

    # --- Quality ---
    rating = _normalize_rating(book.get("avg_rating"))

    score = (0.60 * mood_match +
             0.20 * sentiment +
             0.20 * rating)

    return round(score, 4)
