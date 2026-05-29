from utils.book_utils import prepare_book


def format_book_data(book):

    if not book:
        return None

    return {
        "id": book.get("id"),

        "title": (
            book.get("original_title")
            if book.get("original_title")
            else book.get("title")
        ),

        "author": (
            book.get("author")
            if book.get("author")
            else "Unknown Author"
        ),

        "genre": (
            book.get("genre")
            if book.get("genre")
            else "Unknown"
        ),

        "description": (
            book.get("description")
            if book.get("description")
            else ""
        ),

        "cover_url": (
            book.get("cover_url")
            if book.get("cover_url")
            else None
        ),

        "avg_rating": float(
            book.get("avg_rating", 0)
        ),

        "display_rating": round(
            float(book.get("avg_rating", 0)),
            1
        ),

        "ratings_count": int(
            book.get("ratings_count", 0)
        ),

        "mood_tag": (
            book.get("mood_tag")
            if book.get("mood_tag")
            else "General"
        )
    }

def prepare_books(books):

    return [
        prepare_book(book)
        for book in books
    ]