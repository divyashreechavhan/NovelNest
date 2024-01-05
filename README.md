# NovelNest
A Personlized Book recommendation System

Overview
This project implements a personalized book recommendation system using collaborative filtering and popularity-based filtering. The system is designed to provide users with tailored book recommendations based on their preferences and popular trends.

Features
1. Collaborative Filtering
User-Item Interaction Matrix: Construct a matrix representing user-book interactions.
Similarity Calculation: Utilize cosine similarity to identify similar books based on user ratings.
User-Based Recommendation: Recommend books to a user based on the similarity to their liked books.
2. Popularity-Based Filtering
Rating and Popularity Calculation: Calculate average ratings and total ratings for each book.
Filtering and Recommendation: Filter out less popular books and recommend popular ones.
How to Use
Dataset: The system uses a dataset with information on books, users, and ratings.
Collaborative Filtering: Recommends books based on user preferences.
Popularity-Based Filtering: Recommends popular books.
Implementation Details
Normalization: The collaborative filtering approach involves normalizing user ratings.
Algorithm: Collaborative filtering is implemented using a user-item interaction matrix and cosine similarity.
Strengths: The system provides both personalized and popular recommendations for diverse user preferences.
Limitations: Limited to available data and may not capture niche interests effectively.
Files
app.py: Main implementation of the recommendation system.
data/: Directory containing the dataset in CSV format.
models/: Directory storing serialized models for future use.
Dependencies
Python 3.x
pandas, numpy
scikit-learn
Usage
Clone the repository: git clone https://github.com/your-username/book-recommendation.git
Navigate to the project directory: cd book-recommendation
Run the recommendation system: python app.py
Feel free to explore and adapt the code to suit your needs. Happy reading!
