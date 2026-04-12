import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='myNewpass@26',
    database='book_recommendation_db'
)
cursor = conn.cursor()
print("Connected to database successfully!")

print("Loading CSV file...")
books_df = pd.read_csv(
    'dataset/Books.csv',
    encoding='latin-1',
    on_bad_lines='skip',
    sep=',',
    quotechar='"'
)

print(f"Total books found: {len(books_df)}")
print("Columns:", books_df.columns.tolist())
print(books_df.head(2))

# Clean column names
books_df.columns = books_df.columns.str.strip()

# Rename columns
books_df = books_df.rename(columns={
    'ISBN': 'isbn',
    'Book-Title': 'title',
    'Book-Author': 'author',
    'Year-Of-Publication': 'year',
    'Publisher': 'publisher',
    'Image-URL-M': 'cover_url'
})

print("Renamed columns:", books_df.columns.tolist())

# Add cover_url if missing
if 'cover_url' not in books_df.columns:
    books_df['cover_url'] = ''

# Clean data
books_df['title'] = books_df['title'].fillna('Unknown Title').astype(str)
books_df['author'] = books_df['author'].fillna('Unknown Author').astype(str)
books_df['publisher'] = books_df['publisher'].fillna('Unknown').astype(str)
books_df['cover_url'] = books_df['cover_url'].fillna('').astype(str)
books_df['isbn'] = books_df['isbn'].fillna('').astype(str)

# Insert into MySQL
print("\nInserting books into database...")

insert_query = """
    INSERT IGNORE INTO books
    (isbn, title, author, year, publisher, cover_url)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

success = 0
errors = 0
batch = []
batch_size = 1000

for index, row in books_df.iterrows():
    try:
        isbn = str(row['isbn']).strip()[:20] if str(row['isbn']) != 'nan' else ''
        title = str(row['title']).strip()[:200] if str(row['title']) != 'nan' else 'Unknown Title'
        author = str(row['author']).strip()[:100] if str(row['author']) != 'nan' else 'Unknown Author'
        publisher = str(row['publisher']).strip()[:100] if str(row['publisher']) != 'nan' else 'Unknown'
        cover_url = str(row['cover_url']).strip()[:500] if str(row['cover_url']) != 'nan' else ''

        try:
            year = int(float(row['year'])) if str(row['year']) != 'nan' else None
            if year and not (1800 <= year <= 2026):
                year = None
        except:
            year = None

        batch.append((isbn, title, author, year, publisher, cover_url))

        if len(batch) >= batch_size:
            cursor.executemany(insert_query, batch)
            conn.commit()
            success += len(batch)
            print(f"Inserted {success} books...")
            batch = []

    except Exception as e:
        errors += 1

# Insert remaining
if batch:
    cursor.executemany(insert_query, batch)
    conn.commit()
    success += len(batch)

print(f"\n✅ Done!")
print(f"Successfully inserted: {success} books")
print(f"Errors skipped: {errors}")

cursor.close()
conn.close()