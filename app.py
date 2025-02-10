from flask import Flask, render_template, request, jsonify, abort
import pickle
import pandas as pd
import numpy as np
import os
from difflib import get_close_matches

# Load the preprocessed data
try:
    popular_df = pickle.load(open('popular.pkl', 'rb'))
    pt = pickle.load(open('pt.pkl', 'rb'))
    books = pickle.load(open('books.pkl', 'rb'))
    similarity_score = pickle.load(open('similarity_score.pkl', 'rb'))
except Exception as e:
    print(f"Error loading pickles: {e}")
    popular_df, pt, books, similarity_score = None, None, None, None

app = Flask(__name__)

@app.route('/')
def index():
    if popular_df is None:
        return "<h1>Error: Data files could not be loaded.</h1>", 500

    try:
        return render_template('index.html',
                               book_name=list(popular_df['Book-Title'].values),
                               book_authr=list(popular_df['Book-Author'].values),
                               book_year=list(popular_df['Year-Of-Publication'].values),
                               book_image=list(popular_df['Image-URL-M'].values),
                               book_ratings=list(popular_df['num_ratings'].values),
                               book_avg_ratings=list(popular_df['avg_ratings'].values))
    except Exception as e:
        print(f"Error in index route: {e}")
        abort(500)

@app.route('/recommend')
def recommend_ui():
    return render_template('recomend.html', data=[], message="Enter a book title to get recommendations.")

@app.route('/recommend_books', methods=['POST'])
def recommend():
    if pt is None or similarity_score is None:
        return render_template('recomend.html', data=[], message="Error: Data files could not be loaded.")

    user_input = request.form.get('user_input', "").strip().lower()
    if not user_input:
        return render_template('recomend.html', data=[], message="Please enter a book title.")

    book_titles = [title.lower() for title in pt.index]
    matches = get_close_matches(user_input, book_titles, n=1, cutoff=0.6)

    if not matches:
        return render_template('recomend.html', data=[], message="No books found for the input.")

    matched_title = matches[0].title()

    if matched_title not in pt.index:
        return render_template('recomend.html', data=[], message="No books found for the input.")

    index = np.where(pt.index == matched_title)[0][0]
    similar_items = sorted(list(enumerate(similarity_score[index])), key=lambda x: x[1], reverse=True)[0:10]

    data = []
    for i in similar_items:
        temp_df = books[books['Book-Title'] == pt.index[i[0]]].drop_duplicates('Book-Title')
        if not temp_df.empty:
            item = [
                temp_df.iloc[0]['Book-Title'],
                temp_df.iloc[0]['Book-Author'],
                temp_df.iloc[0]['Image-URL-M'],
                temp_df.iloc[0]['Year-Of-Publication']
            ]
            data.append(item)

    return render_template('recomend.html', data=data, message="Recommendations found!")

# Ensure correct PORT usage for Vercel or other platforms
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
