from flask import Flask, render_template_string, request, redirect, url_for
from math import ceil
import csv
from datetime import datetime, timedelta

app = Flask(__name__)

word_list = []

# Review time intervals
REVIEW_INTERVALS = {
    '': timedelta(hours=4),         # h4 for initially incorrect answers
    'h4': timedelta(hours=24),      # h24
    'h24': timedelta(days=6),       # d6
    'd6': timedelta(days=12),       # d12
    'd12': timedelta(days=24),      # d24
    'd24': timedelta(days=48),      # d48
    'd48': timedelta(days=96),      # d96
    'd96': timedelta(days=180)      # d180
}

# Load word list from CSV file
def load_word_list():
    global word_list
    try:
        with open('word_list.csv', mode='r') as file:
            reader = csv.DictReader(file)
            word_list = [row for row in reader]
    except FileNotFoundError:
        print("Word list not found.")

# Save word list to CSV file
def save_word_list():
    global word_list
    with open('word_list.csv', mode='w', newline='') as file:
        fieldnames = ['english', 'swahili', 'status', 'due']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for word in word_list:
            writer.writerow(word)


load_word_list()

LEARN_COUNT = 3
current_words = []
correct_count = {}
introduced_words = set()

@app.route('/simguistic')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Simguistic</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; text-align: center; }
                header { padding: 20px; background-color: #3498db; color: #fff; font-size: 1.5em; }
                button { background-color: #3498db; color: #fff; border: none; padding: 10px 20px; margin: 10px; border-radius: 5px; font-size: 1em; cursor: pointer; transition: background-color 0.3s; }
                button:hover { background-color: #2980b9; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
                main { margin-top: 20px; }
            </style>
        </head>
        <body>
            <header>Simguistic</header>
            <main>
                <h1>Welcome to Simguistic</h1>
                <h2>This site is under development :)</h2>
                <form action="/simguistic/learn" method="post">
                    <button type="submit">Start Learning</button>
                </form>
                <form action="/simguistic/review" method="get">
                    <button type="submit">Review Due Words</button>  <!-- Review Button -->
                </form>
                <form action="/simguistic/word_list" method="get">
                    <button type="submit">View Word List</button>
                </form>
            </main>
        </body>
        </html>
    ''')

def format_due_time(due_str):
    if not due_str:
        return "Not scheduled"  # Display a message for empty due dates
    
    try:
        due_time = datetime.fromisoformat(due_str)
        time_diff = due_time - datetime.now()
        
        if time_diff.total_seconds() < 86400:  # If due time is less than 24 hours
            hours = ceil(time_diff.total_seconds() / 3600)  # Round to the nearest hour
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = ceil(time_diff.total_seconds() / 86400)  # Round to the nearest day
            return f"{days} day{'s' if days > 1 else ''}"
    except ValueError:
        return "Invalid date"  # In case of invalid date format


@app.route('/simguistic/word_list', methods=['GET', 'POST'])
def word_list_view():
    global word_list
    
    if request.method == 'POST':
        # Handle form submissions for editing, adding, and deleting words
        action = request.form.get('action')
        
        if action == 'edit':
            # Update the existing word entry
            index = int(request.form.get('index'))
            word_list[index]['english'] = request.form.get('english')
            word_list[index]['swahili'] = request.form.get('swahili')
            word_list[index]['due'] = request.form.get('due')
            save_word_list()
        
        elif action == 'add':
            # Add a new word entry with "unlearned" status and no due time
            new_word = {
                'english': request.form.get('new_english'),
                'swahili': request.form.get('new_swahili'),
                'status': '',  # Mark as unlearned
                'due': ''      # No initial review time
            }
            word_list.append(new_word)
            save_word_list()

        
        elif action == 'delete':
            # Delete a word entry
            index = int(request.form.get('index'))
            word_list.pop(index)
            save_word_list()
    
    # Separate words into learned and not learned
    learned_words = [word for word in word_list if word.get('status')]
    not_learned_words = [word for word in word_list if not word.get('status')]
    
    return render_template_string('''
        <html>
        <head>
            <title>Simguistic - Word List</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f7f8fa; color: #333; text-align: center; }
                ul { list-style-type: none; padding: 0; }
                li { padding: 8px; background: #ecf0f1; margin: 5px 0; border-radius: 5px; }
                .word-item { display: flex; justify-content: space-between; align-items: center; }
                .word-form { display: inline; margin: 0; }
                .button { background-color: #3498db; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 3px; }
                .button:hover { background-color: #2980b9; }
            </style>
        </head>
        <body>
            <h1>Simguistic Word List</h1>

            <h2>Words Learned</h2>
            <ul>
                {% for word in learned_words %}
                    <li class="word-item">
                        <form class="word-form" method="post">
                            <input type="text" name="english" value="{{ word['english'] }}">
                            <input type="text" name="swahili" value="{{ word['swahili'] }}">
                            <input type="text" name="due" value="{{ format_due_time(word['due']) }}" placeholder="Due date" readonly>
                            <input type="hidden" name="index" value="{{ loop.index0 }}">
                            <input type="hidden" name="action" value="edit">
                            <button type="submit" class="button">Save</button>
                        </form>
                        <form method="post" class="word-form">
                            <input type="hidden" name="index" value="{{ loop.index0 }}">
                            <input type="hidden" name="action" value="delete">
                            <button type="submit" class="button">Delete</button>
                        </form>
                    </li>
                {% endfor %}
            </ul>

            <h2>Words Not Learned</h2>
            <ul>
                {% for word in not_learned_words %}
                    <li class="word-item">
                        <form class="word-form" method="post">
                            <input type="text" name="english" value="{{ word['english'] }}">
                            <input type="text" name="swahili" value="{{ word['swahili'] }}">
                            <input type="hidden" name="index" value="{{ loop.index0 + learned_words|length }}">
                            <input type="hidden" name="action" value="edit">
                            <button type="submit" class="button">Save</button>
                        </form>
                        <form method="post" class="word-form">
                            <input type="hidden" name="index" value="{{ loop.index0 + learned_words|length }}">
                            <input type="hidden" name="action" value="delete">
                            <button type="submit" class="button">Delete</button>
                        </form>
                    </li>
                {% endfor %}
            </ul>

            <h2>Add a New Word</h2>
            <form method="post" class="word-form">
                <input type="text" name="new_english" placeholder="English word" required>
                <input type="text" name="new_swahili" placeholder="Swahili word" required>
                <input type="hidden" name="action" value="add">
                <button type="submit" class="button">Add Word</button>
            </form>
            
            <br><a href="/simguistic">Back to Home</a>
        </body>
        </html>
    ''', learned_words=learned_words, not_learned_words=not_learned_words, format_due_time=format_due_time)




@app.route('/simguistic/learn', methods=['POST', 'GET'])
def learn():
    global current_words, correct_count, introduced_words
    if request.method == 'POST':
        unknown_words = [word for word in word_list if word['status'] == '']
        if len(unknown_words) == 0:
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

        
        # Select a subset of unknown words to learn
        current_words = unknown_words[:LEARN_COUNT]
        correct_count = {word['english']: 0 for word in current_words}
        introduced_words = set()
        return redirect(url_for('show_translation'))

    return redirect(url_for('index'))

@app.route('/simguistic/show_translation', methods=['GET', 'POST'])
def show_translation():
    global current_words, introduced_words
    if len(current_words) == 0:
        return "<h1>You have learned all selected words!</h1><a href='/'>Back to Home</a>"
    
    # Show a word that hasn't been introduced yet
    word = next((w for w in current_words if w['english'] not in introduced_words), None)
    if word is None:
        return redirect(url_for('next_word'))

    introduced_words.add(word['english'])
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

    @app.route('/simguistic/next_word', methods=['GET', 'POST'])
    def next_word():
        global current_words, correct_count

        if request.method == 'POST':
            word = request.form.get('word')
            user_translation = request.form.get('translation').strip().lower()
            correct_word = next((w for w in current_words if w['english'] == word), None)
            
            if correct_word and user_translation == correct_word['swahili'].lower():
                correct_count[word] += 1
                learned_message = "Correct"
                
                # Check if the word has been learned
                if correct_count[word] >= 3:
                    correct_word['status'] = 'h4'
                    due_time = datetime.now() + REVIEW_INTERVALS['']
                    rounded_due_time = due_time.replace(second=0, microsecond=0)
                    if due_time.second >= 30:
                        rounded_due_time += timedelta(minutes=1)
                    correct_word['due'] = rounded_due_time.isoformat()
                    current_words = [w for w in current_words if w['english'] != word]
                    save_word_list()
                    learned_message = "Correct - New word added to review"

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
                        <h1>Translate '{{ correct_word['english'] }}' to Swahili:</h1>
                        <form method="post" id="answer-form">
                            <input type="hidden" name="word" value="{{ correct_word['english'] }}">
                            <input type="text" name="translation" value="{{ user_translation }}" readonly>
                        </form>
                        <div class="correct">{{ learned_message }}</div>
                        <script>
                            setTimeout(function() {
                                window.location.href = "/simguistic/show_translation";
                            }, 1000);
                        </script>
                    </body>
                    </html>
                ''', user_translation=user_translation, correct_word=correct_word, learned_message=learned_message)

            else:
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


        # Handle incorrect answer feedback (as previously modified)
        else:
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

    if len(current_words) == 0:
        return "<h1>You have learned all selected words!</h1><a href='/'>Back to Home</a>"
    
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
            <h1>Translate '{{ word['english'] }}' to Swahili:</h1>
            <form method="post">
                <input type="hidden" name="word" value="{{ word['english'] }}">
                <input type="text" name="translation" autofocus required>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''', word=word)

# Route to review words that are due for the day
@app.route('/simguistic/review', methods=['GET', 'POST'])
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

if __name__ == '__main__':
    app.run(debug=True)

# Function to calculate next review date based on the current status
def calculate_next_due(status):
    return datetime.now() + REVIEW_INTERVALS.get(status, timedelta(days=7))