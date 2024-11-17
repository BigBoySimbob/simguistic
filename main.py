# main.py

from flask import Flask, render_template, request, redirect, url_for, send_file, abort
from datetime import datetime
import os

from user_management import get_users, set_current_user, get_current_user
from learning import start_learning_session, process_learning_input
from review import start_review_session, process_review_input
from wordlist_utils import get_word_counts, get_wordlist_filepath  # Import the new function

app = Flask(
    __name__,
    template_folder='simguistic/templates',
    static_folder='simguistic/static',
    static_url_path='/simguistic/static'
)
app.secret_key = 'your_secret_key'  # Use a secure random key in production

@app.route('/simguistic')
def home():
    users = get_users()
    current_user = get_current_user()
    user_stats = {}
    for user in users:
        total_learned, due_for_review = get_word_counts(user)
        user_stats[user] = {
            'total_learned': total_learned,
            'due_for_review': due_for_review
        }
    return render_template('home.html', users=users, current_user=current_user, user_stats=user_stats)

@app.route('/simguistic/change_user', methods=['POST'])
def change_user():
    username = request.form['username']
    set_current_user(username)
    return redirect(url_for('home'))

@app.route('/simguistic/learn', methods=['GET', 'POST'])
def learn():
    if request.method == 'POST':
        user_input = request.form['user_input']
        result = process_learning_input(user_input)
        return render_template('learn.html', **result)
    else:
        result = start_learning_session()
        return render_template('learn.html', **result)

@app.route('/simguistic/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        user_input = request.form['user_input']
        result = process_review_input(user_input)
        return render_template('review.html', **result)
    else:
        result = start_review_session()
        return render_template('review.html', **result)

@app.route('/simguistic/download_wordlist', methods=['POST'])
def download_wordlist():
    """
    Serves the wordlist CSV file for the current user.
    """
    username = get_current_user()
    if not username:
        # Redirect to home if no user is selected
        return redirect(url_for('home'))

    # Get the filepath for the user's wordlist
    filepath = get_wordlist_filepath(username)
    if not os.path.exists(filepath):
        # Return a 404 error if the file does not exist
        abort(404, description="Wordlist file not found")

    # Serve the file for download
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f'{username}_wordlist.csv'
    )



if __name__ == '__main__':
    app.run(debug=True)