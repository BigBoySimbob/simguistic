# learning.py

from flask import session
from datetime import datetime, timedelta
import random
import string  # Import string module

from user_management import get_current_user
from wordlist_utils import load_wordlist, save_wordlist

def normalize(text):
    # Helper function to remove punctuation and convert to lowercase
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator).strip().lower()

def start_learning_session():
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    wordlist = load_wordlist(username)
    unknown_words = [word for word in wordlist if not word['status']]
    if not unknown_words:
        return {'message': 'All words have been learned!'}

    session['learning_words'] = unknown_words[:5]
    # Use normalized keys for learning_progress
    session['learning_progress'] = {normalize(word['swahili']): 0 for word in session['learning_words']}
    session['learning_queue'] = []
    session['presented_words'] = []
    session['learning_state'] = 'start'

    prepare_learning_queue()

    next_word = session['learning_queue'].pop(0)
    session['current_learning_word'] = next_word

    if next_word['swahili'] not in session['presented_words']:
        session['learning_state'] = 'presentation'
        session['presented_words'].append(next_word['swahili'])
        return {
            'english_word': next_word['english'],
            'swahili_word': next_word['swahili'],
            'state': 'presentation'
        }
    else:
        session['learning_state'] = 'testing'
        return {
            'english_word': next_word['english'],
            'state': 'testing'
        }

def process_learning_input(user_input):
    """
    Processes the learning input based on the current learning state and session context.

    Parameters:
        user_input (str): The input provided by the user.

    Returns:
        dict: A result indicating the current learning state and any relevant data or errors.
    """
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    current_word = session.get('current_learning_word')
    if not current_word:
        return {'error': 'No word is currently being learned.'}

    learning_state = session.get('learning_state', 'presentation')
    progress = session.get('learning_progress', {})

    # Ensure progress dictionary is initialized for the current word
    key = normalize(current_word['swahili'])
    progress.setdefault(key, 0)

    if learning_state == 'presentation':
        return handle_presentation_state(current_word)
    elif learning_state == 'testing':
        return handle_testing_state(user_input, current_word, progress, username)
    elif learning_state == 'correction':
        return handle_correction_state(user_input, current_word)
    elif learning_state == 'correct':
        return handle_correct_state(username)
    else:
        # Default to 'presentation' state if invalid state
        session['learning_state'] = 'presentation'
        return handle_presentation_state(current_word)


def handle_presentation_state(current_word):
    """Handles the 'presentation' state."""
    session['learning_state'] = 'testing'
    return {
        'english_word': current_word['english'],
        'state': 'testing'
    }


def handle_testing_state(user_input, current_word, progress, username):
    """Handles the 'testing' state."""
    correct_translation = normalize(current_word['swahili'])
    user_input_clean = normalize(user_input)

    if user_input_clean == correct_translation:
        progress[correct_translation] += 1

        if progress[correct_translation] >= 3:
            mark_word_as_learned(username, current_word, progress)
            session['learning_state'] = 'correct'
            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'message': 'New word learned!',
                'state': 'correct',
                'delay': True
            }
        else:
            session['learning_state'] = 'correct'
            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'message': 'Correct!',
                'state': 'correct',
                'delay': True
            }
    else:
        progress[correct_translation] = 0
        session['learning_state'] = 'correction'
        return {
            'english_word': current_word['english'],
            'user_input': user_input,
            'correct_translation': current_word['swahili'],
            'error': 'Incorrect.',
            'state': 'correction'
        }


def handle_correction_state(user_input, current_word):
    """Handles the 'correction' state."""
    correct_translation = normalize(current_word['swahili'])
    user_input_clean = normalize(user_input)

    if user_input_clean == correct_translation:
        session['learning_state'] = 'testing'
        return {
            'english_word': current_word['english'],
            'state': 'testing'
        }
    else:
        return {
            'english_word': current_word['english'],
            'user_input': user_input,
            'correct_translation': current_word['swahili'],
            'error': 'Please type the correct translation to proceed.',
            'state': 'correction'
        }


def handle_correct_state(username):
    """Handles the 'correct' state."""
    if session['learning_words']:
        if not session.get('learning_queue'):
            prepare_learning_queue()

        if session['learning_queue']:
            next_word = session['learning_queue'].pop(0)
            session['current_learning_word'] = next_word

            if next_word['swahili'] not in session.get('presented_words', []):
                session['presented_words'] = session.get('presented_words', []) + [next_word['swahili']]
                session['learning_state'] = 'presentation'
                return {
                    'english_word': next_word['english'],
                    'swahili_word': next_word['swahili'],
                    'state': 'presentation'
                }
            else:
                session['learning_state'] = 'testing'
                return {
                    'english_word': next_word['english'],
                    'state': 'testing'
                }
    else:
        session.clear()
        return {
            'message': 'All words have been learned!',
            'state': 'completed'
        }


def mark_word_as_learned(username, current_word, progress):
    """Marks a word as learned and updates the word list."""
    key = normalize(current_word['swahili'])
    wordlist = load_wordlist(username)
    now = datetime.now()
    due_time = (now + timedelta(hours=4)).replace(second=0, microsecond=0)

    for word in wordlist:
        if normalize(word['swahili']) == key:
            word['status'] = 'h4'
            word['due'] = due_time.isoformat()
            break

    save_wordlist(username, wordlist)
    session['learning_words'] = [
        word for word in session['learning_words'] if normalize(word['swahili']) != key
    ]
    progress.pop(key, None)


def prepare_learning_queue():
    words = session.get('learning_words', [])
    random.shuffle(words)
    session['learning_queue'] = words.copy()
