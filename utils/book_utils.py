import re


def clean_title(title):

    if not title:
        return "Untitled"

    return re.sub(
        r"\s*\(.*?\)",
        "",
        title
    ).strip()


def clean_author(author):

    if not author:
        return "Unknown"

    return re.sub(
        r"[\[\]']",
        "",
        author
    )


def clean_cover(cover_url):

    if (
        not cover_url
        or any(
            x in str(cover_url).lower()
            for x in [
                'nophoto',
                'no_cover',
                'default'
            ]
        )
    ):
        return None

    return cover_url


def prepare_book(book):

    if not book:
        return None

    # ORIGINAL TITLE PRIORITY
    title = (
        book.get('original_title')
        or book.get('display_title')
        or book.get('title')
        or "Untitled"
    )

    book['clean_title'] = clean_title(
        title
    )

    book['author'] = clean_author(
        book.get('author')
    )

    book['cover_url'] = clean_cover(
        book.get('cover_url')
    )

    return book

def prepare_books(books):

    return [
        prepare_book(book)
        for book in books
    ]