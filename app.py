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
def recommend_books():
    if pt is None or similarity_score is None:
        return render_template('recomend.html', data=[], message="Error: Data files could not be loaded.")

    user_input = request.form.get('user_input', "").strip().lower()
    if not user_input:
        return render_template('recomend.html', data=[], message="Please enter a book title.")

    # Convert index to lowercase for case-insensitive matching
    book_titles = {title.lower(): title for title in pt.index}

    # **Step 1: Check for exact match first**
    if user_input in book_titles:
        matched_title = book_titles[user_input]
    else:
        # **Step 2: Use fuzzy matching only if exact match isn't found**
        matches = get_close_matches(user_input, book_titles.keys(), n=3, cutoff=0.4)
        if matches:
            matched_title = book_titles[matches[0]]
        else:
            print(f"No matches found for input: {user_input}")
            return render_template('recomend.html', data=[], message="No books found for the input.")

    print(f"Matched Title: {matched_title}")

    # Get the index of the matched book
    if matched_title not in pt.index:
        return render_template('recomend.html', data=[], message="No books found for the input.")

    index = np.where(pt.index == matched_title)[0][0]
    similar_items = sorted(list(enumerate(similarity_score[index])), key=lambda x: x[1], reverse=True)[1:11]

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

    return render_template('recomend.html', data=data, message=f"Top 10 Recommended Books for {matched_title}")


# Ensure correct PORT usage for deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
