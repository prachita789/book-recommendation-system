import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeRecommender:

    def __init__(self, ratings):

        self.ratings_df = pd.DataFrame(ratings)

        self.prepare()

    def prepare(self):

        if self.ratings_df.empty:

            self.user_book_matrix = None
            return

        self.user_book_matrix = (
            self.ratings_df.pivot_table(
                index='user_id',
                columns='book_id',
                values='rating'
            ).fillna(0)
        )

        self.similarity_matrix = cosine_similarity(
            self.user_book_matrix
        )

    def recommend(self, user_id, top_n=5):

        if self.user_book_matrix is None:
            return []

        if user_id not in self.user_book_matrix.index:
            return []

        user_index = list(
            self.user_book_matrix.index
        ).index(user_id)

        similarity_scores = list(
            enumerate(
                self.similarity_matrix[user_index]
            )
        )

        similarity_scores = sorted(
            similarity_scores,
            key=lambda x: x[1],
            reverse=True
        )

        similar_users = similarity_scores[1:6]

        recommended_books = set()

        for sim_user in similar_users:

            sim_user_id = (
                self.user_book_matrix.index[
                    sim_user[0]
                ]
            )

            books = self.user_book_matrix.loc[
                sim_user_id
            ]

            liked_books = books[
                books >= 4
            ].index.tolist()

            recommended_books.update(
                liked_books
            )

        return list(recommended_books)[:top_n]