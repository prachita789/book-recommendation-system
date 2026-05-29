import pandas as pd
import mysql.connector
from ast import literal_eval


def clean_text(value, max_len=None, default=''):
    if pd.isna(value):
        value = default
    value = str(value).strip()
    if value.lower() == 'nan':
        value = default
    if max_len:
        value = value[:max_len]
    return value


# Database connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='myNewpass@26',
    database='book_recommendation_db'
)

cursor = conn.cursor()
print("Connected!")

# Load CSV
books_df = pd.read_csv('dataset/books_enriched.csv')
# books_df = books_df.head(5000)

print(f"Total books to import: {len(books_df)}")

# Fill missing text columns
books_df['title'] = books_df['title'].fillna('Unknown').astype(str)
books_df['authors'] = books_df['authors'].fillna('Unknown').astype(str)
books_df['description'] = books_df['description'].fillna('').astype(str)
books_df['image_url'] = books_df['image_url'].fillna('').astype(str)
books_df['isbn'] = books_df['isbn'].fillna('').astype(str)


# Convert genres
def get_genre(genres):
    try:
        if isinstance(genres, str):
            g = literal_eval(genres)
            return ', '.join(g[:3]) if g else ''
        return ''
    except:
        return ''


books_df['genre_str'] = books_df['genres'].apply(get_genre)


insert_query = """
INSERT IGNORE INTO books (
    isbn, title, author, year, publisher,
    cover_url, description, genre,
    pages, avg_rating, ratings_count,
    goodreads_id, best_book_id
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

batch = []
batch_size = 500
success = 0
errors = 0

for index, row in books_df.iterrows():
    try:
        isbn = clean_text(row.get('isbn'), 20)
        title = clean_text(row.get('title'), 200, 'Unknown')
        author = clean_text(row.get('authors'), 100, 'Unknown')
        cover_url = clean_text(row.get('image_url'), 500)
        description = clean_text(row.get('description'), 5000)
        genre = clean_text(row.get('genre_str'), 500)

        # Pages
        pages = None
        if pd.notna(row.get('pages')):
            try:
                pages = int(float(row.get('pages')))
            except:
                pages = None

        # Ratings count
        ratings_count = 0
        if pd.notna(row.get('ratings_count')):
            try:
                ratings_count = int(float(row.get('ratings_count')))
            except:
                ratings_count = 0

        # Average rating
        avg_rating = 0.0
        if pd.notna(row.get('average_rating')):
            try:
                avg_rating = float(row.get('average_rating'))
            except:
                avg_rating = 0.0

        # Year
        year = None
        if pd.notna(row.get('publishDate')):
            try:
                year_str = str(row.get('publishDate')).split('/')[-1]
                year = int(float(year_str))
                if year < 1800 or year > 2026:
                    year = None
            except:
                year = None

        # Goodreads IDs
        goodreads_id = None
        if pd.notna(row.get('book_id')):
            try:
                goodreads_id = int(row.get('book_id'))
            except:
                goodreads_id = None

        best_book_id = None
        if pd.notna(row.get('best_book_id')):
            try:
                best_book_id = int(row.get('best_book_id'))
            except:
                best_book_id = None

        batch.append((
            isbn, title, author, year, None,
            cover_url, description, genre,
            pages, avg_rating, ratings_count,
            goodreads_id, best_book_id
        ))

        if len(batch) >= batch_size:
            cursor.executemany(insert_query, batch)
            conn.commit()
            success += len(batch)
            print(f"Inserted {success} books...")
            batch = []

    except Exception as e:
        errors += 1
        print(f"Error row {index}: {e}")

# Insert remaining
if batch:
    cursor.executemany(insert_query, batch)
    conn.commit()
    success += len(batch)

print("\n✅ Import complete!")
print(f"Inserted: {success}")
print(f"Errors: {errors}")

cursor.close()
conn.close()