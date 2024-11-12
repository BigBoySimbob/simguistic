# learning.py

from flask import session
from datetime import datetime
import random

from user_management import get_current_user
from wordlist_utils import load_wordlist, save_wordlist

def start_learning_session():
    """
    Initializes a new learning session for the current user.
    Selects the first 3 unknown words and stores session data.
    """
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    wordlist = load_wordlist(username)
    unknown_words = [word for word in wordlist if not word['status']]
    if not unknown_words:
        return {'message': 'All words have been learned!'}

    # Select the first 3 unknown words
    session['learning_words'] = unknown_words[:3]
    session['learning_progress'] = {word['swahili']: 0 for word in session['learning_words']}
    session['learning_queue'] = []

    # Prepare the initial word to display
    prepare_learning_queue()

    current_word = session['learning_queue'].pop(0)
    session['current_learning_word'] = current_word

    return {
        'english_word': current_word['english'],
        'swahili_word': current_word['swahili'],
        'message': 'New Learning Session Started'
    }

def process_learning_input(user_input):
    """
    Processes the user's input during the learning session.
    Updates the word's progress and status accordingly.
    """
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    current_word = session.get('current_learning_word')
    if not current_word:
        return {'error': 'No word is currently being learned.'}

    correct_translation = current_word['swahili']
    user_input = user_input.strip().lower()
    correct_answer = correct_translation.strip().lower()

    if user_input == correct_answer:
        # Increment the correct count
        progress = session['learning_progress']
        progress[correct_translation] += 1

        if progress[correct_translation] >= 3:
            # Update the word's status to 'h4' in the wordlist
            wordlist = load_wordlist(username)
            for word in wordlist:
                if word['swahili'] == correct_translation:
                    word['status'] = 'h4'
                    word['due'] = ''
                    break
            save_wordlist(username, wordlist)
            message = 'New word learned!'
        else:
            message = 'Correct!'
        
        # Move on to the next word
        if not session['learning_queue']:
            prepare_learning_queue()

        if session['learning_queue']:
            next_word = session['learning_queue'].pop(0)
            session['current_learning_word'] = next_word
            return {
                'english_word': next_word['english'],
                'message': message
            }
        else:
            # Session completed
            session.pop('learning_words', None)
            session.pop('learning_progress', None)
            session.pop('current_learning_word', None)
            return {
                'message': 'Learning session completed!'
            }
    else:
        # Incorrect input
        return {
            'english_word': current_word['english'],
            'correct_translation': correct_translation,
            'error': 'Incorrect. Please try again.'
        }

def prepare_learning_queue():
    """
    Prepares a randomized queue of words for the learning session,
    ensuring words are not repeated consecutively.
    """
    words = session.get('learning_words', [])
    random.shuffle(words)
    session['learning_queue'] = words.copy()
