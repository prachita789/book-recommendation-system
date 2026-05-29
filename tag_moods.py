
import re
import mysql.connector


# ----------------------------------------------------------------------
# MOOD RULES  --  order matters: first match wins.
# Specific / rare moods go FIRST so they can claim books before broader
# moods (Fantasy, Fiction) absorb everything.
# ----------------------------------------------------------------------

MOOD_RULES = [
    ("Self Help", {
        "self-help", "self help", "personal-development", "productivity",
        "leadership", "business", "management", "finance", "economics",
    }),
    ("Inspirational", {
        "biography", "memoir", "autobiography", "motivational",
        "spirituality", "religion", "christian", "faith", "inspirational",
    }),
    ("Dark", {
        "horror", "gothic", "dark", "zombies", "war",
        "psychological-thriller",
    }),
    ("Mystery", {
        "mystery", "detective", "crime", "thriller", "noir", "spy",
        "suspense",
    }),
    ("Adventure", {
        "adventure", "action", "survival", "western", "quest",
        "exploration", "dystopia", "dystopian", "post-apocalyptic",
        "science-fiction", "sci-fi", "space-opera",
    }),
    ("Fantasy", {
        "fantasy", "magic", "urban-fantasy", "epic-fantasy",
        "high-fantasy", "magical-realism", "mythology", "paranormal",
        "vampires", "witches", "werewolves", "fairy-tale", "fairies",
        "dragons",
    }),
    ("Romance", {
        "romance", "chick-lit", "chick lit", "contemporary-romance",
        "historical-romance", "love-story", "erotica",
    }),
    ("Thoughtful", {
        "philosophy", "poetry", "essays", "sociology", "politics",
        "history", "science", "academic", "classics",
        "literary-fiction", "literature", "education",
    }),
    # Fiction = catch-all. Anything not claimed above lands here.
    ("Fiction", {
        "fiction", "contemporary", "literary", "historical-fiction",
        "young-adult", "childrens",
    }),
]

FALLBACK_MOOD = "Fiction"


def parse_genres(raw):
   
    if not raw:
        return set()

    # Pull tokens out of either format. Quotes/brackets become noise.
    # Step 1: try Python-list-style extraction.
    quoted = re.findall(r"'([^']+)'", raw)
    if quoted:
        tokens = quoted
    else:
        # Step 2: plain comma-separated.
        tokens = raw.split(",")

    cleaned = set()
    for t in tokens:
        t = t.strip().strip("[]'\"").lower()
        if t:
            cleaned.add(t)
    return cleaned


def assign_mood(genre_tags):
   
    for mood, tags in MOOD_RULES:
        if genre_tags & tags:
            return mood
    return FALLBACK_MOOD


def main():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="myNewpass@26",
        database="book_recommendation_db",
    )
    cur = conn.cursor()

    # Pull every book. We re-tag ALL of them so rule changes propagate.
    cur.execute("SELECT id, genre FROM books")
    rows = cur.fetchall()

    print(f"Loaded {len(rows)} books. Re-tagging...")

    updates = []
    for book_id, genre in rows:
        tags = parse_genres(genre)
        mood = assign_mood(tags)
        updates.append((mood, book_id))

    # Batched UPDATE so we don't hammer the server with 10k round trips.
    cur.executemany(
        "UPDATE books SET mood_tag = %s WHERE id = %s",
        updates,
    )
    conn.commit()

    # Report what we did.
    cur.execute("""
        SELECT mood_tag, COUNT(*) AS c
        FROM books
        GROUP BY mood_tag
        ORDER BY c DESC
    """)
    print("\nNew mood distribution:")
    for mood, count in cur.fetchall():
        print(f"  {mood:<15} {count}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
