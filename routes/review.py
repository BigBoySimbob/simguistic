from flask import Blueprint, render_template_string, redirect, url_for, request
from models import word_list, save_word_list, REVIEW_INTERVALS
from datetime import datetime, timedelta

review_bp = Blueprint('review', __name__)

@review_bp.route('/review', methods=['GET', 'POST'])
def review():
    global current_words, correct_count

    if request.method == 'POST':
        word = request.form.get('word')
        user_translation = request.form.get('translation').strip().lower()
        correct_word = next((w for w in current_words if w['english'] == word), None)

        if correct_word:
            if user_translation == correct_word['swahili'].lower():
                # Update to the next interval
                current_status = correct_word.get('status', '')
                next_status = next((s for s in REVIEW_INTERVALS if REVIEW_INTERVALS[s] > REVIEW_INTERVALS.get(current_status, timedelta(0))), 'd180')
                correct_word['status'] = next_status
                correct_word['due'] = (datetime.now() + REVIEW_INTERVALS[next_status]).isoformat()
            else:
                # Reset to smallest interval
                correct_word['status'] = 'h4'
                correct_word['due'] = (datetime.now() + timedelta(hours=4)).isoformat()  # Reset due date to 4 hours later
                current_words.append(correct_word)  # Re-add for re-testing in the session

            
            save_word_list()
            current_words = [w for w in current_words if w != correct_word]  # Remove word from current session if correct

        if not current_words:
            return render_template_string('''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>No More Words to Review</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                        h1 { color: #2c3e50; font-size: 2em; }
                        p { margin-top: 10px; font-size: 1.2em; color: #666; }
                        a.button { background-color: #3498db; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 1em; margin-top: 20px; transition: background-color 0.3s; }
                        a.button:hover { background-color: #2980b9; }
                    </style>
                </head>
                <body>
                    <h1>No More Words to Review</h1>
                    <p>All due words have been reviewed.</p>
                    <a href="/simguistic" class="button">Back to Home</a>
                </body>
                </html>
            ''')


        return redirect(url_for('review'))

    # Retrieve words due for review
    current_words = [word for word in word_list if word.get('due') and datetime.fromisoformat(word['due']) <= datetime.now()]

    if not current_words:
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>No Words Due for Review</title>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    h1 { color: #2c3e50; font-size: 2em; }
                    p { margin-top: 10px; font-size: 1.2em; color: #666; }
                    a.button { background-color: #3498db; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 1em; margin-top: 20px; transition: background-color 0.3s; }
                    a.button:hover { background-color: #2980b9; }
                </style>
            </head>
            <body>
                <h1>No Words Due for Review</h1>
                <p>There are currently no words that need reviewing.</p>
                <a href="/simguistic" class="button">Back to Home</a>
            </body>
            </html>
        ''')


    word = current_words[0]
    return render_template_string('''
        <html>
        <head>
            <title>Review Session</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                h1 { color: #2c3e50; }
            </style>
        </head>
        <body>
            <h1>Review: Translate '{{ word['english'] }}' to Swahili</h1>
            <form method="post">
                <input type="hidden" name="word" value="{{ word['english'] }}">
                <input type="text" name="translation" autofocus required>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''', word=word)