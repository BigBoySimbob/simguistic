from flask import Blueprint, render_template_string, redirect, url_for, request
from models import word_list, load_word_list, save_word_list, REVIEW_INTERVALS
from datetime import datetime, timedelta

learning_bp = Blueprint('learning', __name__)

LEARN_COUNT = 3
current_words = []
correct_count = {}

@learning_bp.route('/learn', methods=['POST', 'GET'])
def learn():
    global current_words, correct_count, introduced_words

    # Ensure the word list is loaded
    load_word_list()
    if not word_list:
        print("Word list is empty or not loaded. Ensure word_list.csv is accessible and has data.")
        return "<h1>No words found in the word list. Please check word_list.csv.</h1>"

    if request.method == 'POST':
        # Filter for words that have not been learned (status is empty)
        unknown_words = [word for word in word_list if word.get('status', '') == '']
        
        # Debug output to check if unknown words are being selected
        print(f"Unknown words selected for learning: {len(unknown_words)} words")

        if len(unknown_words) == 0:
            # No words left to learn
            print("No more words to learn.")
            return render_template_string('''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>No More Words to Learn</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                        h1 { color: #2c3e50; font-size: 2em; }
                        p { margin-top: 10px; font-size: 1.2em; color: #666; }
                        a.button { background-color: #3498db; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 1em; margin-top: 20px; transition: background-color 0.3s; }
                        a.button:hover { background-color: #2980b9; }
                    </style>
                </head>
                <body>
                    <h1>No More Words to Learn</h1>
                    <p>You have learned all the available words.</p>
                    <a href="/simguistic" class="button">Back to Home</a>
                </body>
                </html>
            ''')

        # Initialize unlearned words for learning session
        current_words = [{'english': w['english'], 'swahili': w['swahili'], 'introduced': False} for w in unknown_words[:LEARN_COUNT]]
        correct_count = {word['english']: 0 for word in current_words}
        introduced_words = set()  # Reset introduced words for the session
        
        # Debug output to verify current_words and correct_count initialization
        print(f"Current session words initialized with {len(current_words)} words.")
        print(f"Initial correct_count: {correct_count}")

    return redirect(url_for('learning.show_translation'))


@learning_bp.route('/show_translation', methods=['GET', 'POST'])
def show_translation():
    global current_words

    # Check if there are no more words to learn
    if len(current_words) == 0:
        return "<h1>You have learned all selected words!</h1><a href='/'>Back to Home</a>"

    # Select the first unintroduced word
    word = next((w for w in current_words if not w.get('introduced', False)), None)
    
    if word:
        word['introduced'] = True  # Mark word as introduced
        return render_template_string('''
            <html>
            <head>
                <title>Learning</title>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    h1 { color: #2c3e50; }
                </style>
            </head>
            <body>
                <h1>English: '{{ word['english'] }}', Swahili: '{{ word['swahili'] }}'</h1>
                <form action="/simguistic/next_word" method="get">
                    <button type="submit" id="continue-button">Continue</button>
                </form>
                <script>
                    document.addEventListener('keydown', function(event) {
                        if (event.key === 'Enter') {
                            document.getElementById('continue-button').click();
                        }
                    });
                </script>
            </body>
            </html>
        ''', word=word)

    # If all words have been introduced, proceed to testing
    return redirect(url_for('next_word'))

@learning_bp.route('/next_word', methods=['GET', 'POST'])
def next_word():
    global current_words, correct_count

    if request.method == 'POST':
        word = request.form.get('word')
        user_translation = request.form.get('translation').strip().lower()
        correct_word = next((w for w in current_words if w['english'] == word), None)
        
        if correct_word and user_translation == correct_word['swahili'].lower():
            # Increment correct count for the word
            correct_count[word] += 1
            learned_message = "Correct"
            
            # Check if the word has been learned by answering correctly three times in a row
            if correct_count[word] >= 3:
                # Mark the word as "learned" and update its status and due date
                correct_word['status'] = 'h4'
                due_time = datetime.now() + REVIEW_INTERVALS['']
                correct_word['due'] = due_time.replace(second=0, microsecond=0).isoformat()
                
                # Save the updated status and due time
                save_word_list()
                
                # Remove the learned word from current_words
                current_words = [w for w in current_words if w['english'] != word]
                learned_message = "Correct - New word added to review"

                # Check if there are no more words left to learn
                if not current_words:
                    return "<h1>You have learned all selected words!</h1><a href='/'>Back to Home</a>"

            # Display the correct answer message and proceed to the next word
            return render_template_string('''
                <html>
                <head>
                    <title>Simguistic - Learning</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                        h1 { color: #2c3e50; }
                        .correct { color: green; font-size: 1.2em; margin-top: 10px; }
                    </style>
                </head>
                <body>
                    <h1>Correct! - Translate '{{ correct_word['english'] }}' to Swahili</h1>
                    <p class="correct">{{ learned_message }}</p>
                    <form method="get" action="{{ url_for('show_translation') }}">
                        <button type="submit">Continue</button>
                    </form>
                </body>
                </html>
            ''', correct_word=correct_word, learned_message=learned_message)

        else:
            # Reset correct count if the answer is incorrect
            correct_count[word] = 0
            return render_template_string('''
                <html>
                <head>
                    <title>Simguistic - Learning</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                        h1 { color: #2c3e50; }
                        .incorrect { color: red; }
                        .correct { color: green; }
                    </style>
                </head>
                <body>
                    <h1>Your answer: <span class="incorrect">{{ user_translation }}</span></h1>
                    <h1>Correct answer: <span class="correct">{{ correct_word['swahili'] }}</span></h1>
                    <p>Please type the correct answer to proceed.</p>
                    <form method="post">
                        <input type="hidden" name="word" value="{{ correct_word['english'] }}">
                        <input type="text" name="translation" placeholder="Enter the correct word" required autofocus>
                        <button type="submit">Submit</button>
                    </form>
                </body>
                </html>
            ''', user_translation=user_translation, correct_word=correct_word)

    # If there are no more words to test, display a completion message
    if not current_words:
        return "<h1>You have learned all selected words!</h1><a href='/'>Back to Home</a>"
    
    # Otherwise, continue testing with the next word
    word = current_words[0]
    return render_template_string('''
        <html>
        <head>
            <title>Simguistic - Learning</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                h1 { color: #2c3e50; }
            </style>
        </head>
        <body>
            <h1>Translate '{{ word['english'] }}' to Swahili</h1>
            <form method="post">
                <input type="hidden" name="word" value="{{ word['english'] }}">
                <input type="text" name="translation" autofocus required>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''', word=word)