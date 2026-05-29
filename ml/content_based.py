import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContentBasedRecommender:

    def __init__(self, books):

        self.books_df = pd.DataFrame(books)

        self.prepare_data()

    def prepare_data(self):

        # Fill missing values
        self.books_df['genre'] = self.books_df['genre'].fillna('')
        self.books_df['description'] = self.books_df['description'].fillna('')
        self.books_df['title'] = self.books_df['title'].fillna('')

        # Combine features
        self.books_df['features'] = (
            self.books_df['title'] + ' ' +
            self.books_df['genre'] + ' ' +
            self.books_df['description']
        )

        # TF-IDF
        self.vectorizer = TfidfVectorizer(
            stop_words='english'
        )

        self.feature_matrix = self.vectorizer.fit_transform(
            self.books_df['features']
        )

        # Similarity matrix
        self.similarity = cosine_similarity(
            self.feature_matrix
        )

    def recommend(self, book_id, top_n=5):

        # Find index
        indices = self.books_df.index[
            self.books_df['id'] == book_id
        ]

        if len(indices) == 0:
            return []

        idx = indices[0]

        similarity_scores = list(
            enumerate(self.similarity[idx])
        )

        similarity_scores = sorted(
            similarity_scores,
            key=lambda x: x[1],
            reverse=True
        )

        # Remove same book
        similarity_scores = similarity_scores[1:top_n+1]

        recommended_books = []

        for i, score in similarity_scores:

            book = self.books_df.iloc[i]

            recommended_books.append({
                'id': int(book['id']),
                'title': book['title'],
                'author': book['author'],
                'cover_url': book['cover_url'],
                'score': round(float(score), 3)
            })

        return recommended_books