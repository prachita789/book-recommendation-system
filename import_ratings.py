import pandas as pd
import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='myNewpass@26',
    database='book_recommendation_db'
)

cursor = conn.cursor()

print("✅ Connected to database")

# Load ratings CSV
ratings_df = pd.read_csv('dataset/ratings.csv')

print(f"Total ratings found: {len(ratings_df)}")



insert_query = """
INSERT INTO ratings (
    user_id,
    book_id,
    rating
)
VALUES (%s, %s, %s)
"""

batch = []
batch_size = 1000

success = 0
errors = 0

for index, row in ratings_df.iterrows():

    try:

        user_id = int(row['user_id'])
        book_id = int(row['book_id'])
        rating = float(row['rating'])

        batch.append((
            user_id,
            book_id,
            rating
        ))

        if len(batch) >= batch_size:

            cursor.executemany(insert_query, batch)
            conn.commit()

            success += len(batch)

            print(f"Inserted {success} ratings...")

            batch = []

    except Exception as e:

        errors += 1

        print(f"Error at row {index}: {e}")

# Insert remaining batch
if batch:

    cursor.executemany(insert_query, batch)
    conn.commit()

    success += len(batch)

print("\n✅ Ratings import complete!")
print(f"Inserted: {success}")
print(f"Errors: {errors}")

cursor.close()
conn.close()