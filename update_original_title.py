import pandas as pd
import MySQLdb

db = MySQLdb.connect(
    host="127.0.0.1", user="root", passwd="myNewpass@26", db="book_recommendation_db"
)

cur = db.cursor()

df = pd.read_csv("dataset/books_enriched.csv")

updated = 0

for _, row in df.iterrows():
    title = str(row["title"]).strip()
    original = row.get("original_title")

    if pd.notna(original) and original.strip() != "":
        cur.execute("""
            UPDATE books
            SET original_title = %s
            WHERE title LIKE %s
        """,(original.strip(), f"%{title}%"))

        updated += 1

db.commit()
cur.close()
db.close()

print("Script started...")



if updated % 500 == 0:
        print(f"Updated {updated} rows...")
