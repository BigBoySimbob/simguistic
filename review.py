# review.py

from flask import session
from datetime import datetime, timedelta
import random

from user_management import get_current_user
from wordlist_utils import load_wordlist, save_wordlist

TIME_INTERVALS = ['h4', 'h24', 'd6', 'd12', 'd24', 'd48', 'd96', 'd180']
TIME_DELTAS = {
    'h4': timedelta(hours=4),
    'h24': timedelta(hours=24),
    'd6': timedelta(days=6),
    'd12': timedelta(days=12),
    'd24': timedelta(days=24),
    'd48': timedelta(days=48),
    'd96': timedelta(days=96),
    'd180': timedelta(days=180),
}

def start_review_session():
    """
    Initializes a new review session for the current user.
    Selects all words due for review and stores session data.
    """
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    wordlist = load_wordlist(username)
    now = datetime.now()
    due_words = []

    for word in wordlist:
        if word['status']:
            due_str = word.get('due', '')
            if due_str:
                due_datetime = datetime.fromisoformat(due_str)
                if due_datetime <= now:
                    due_words.append(word)
            else:
                # If 'due' is empty but 'status' exists, schedule for immediate review
                due_words.append(word)

    if not due_words:
        return {'message': 'No words are due for review!'}

    session['review_words'] = due_words
    session['incorrect_words'] = []
    session['review_queue'] = []

    # Prepare the initial queue
    prepare_review_queue()

    current_word = session['review_queue'].pop(0)
    session['current_review_word'] = current_word

    return {
        'english_word': current_word['english'],
        'message': 'New Review Session Started'
    }

def process_review_input(user_input):
    """
    Processes the user's input during the review session.
    Updates the word's status and due date accordingly.
    """
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    current_word = session.get('current_review_word')
    if not current_word:
        return {'error': 'No word is currently being reviewed.'}

    correct_translation = current_word['swahili']
    user_input = user_input.strip().lower()
    correct_answer = correct_translation.strip().lower()

    wordlist = load_wordlist(username)
    now = datetime.now()

    if user_input == correct_answer:
        # Correct input
        # Update the word's status to the next interval
        current_status = current_word['status']
        next_status = get_next_status(current_status)
        current_word['status'] = next_status

        # Update 'due' date
        current_word['due'] = (now + TIME_DELTAS[next_status]).isoformat()

        # Update the word in the wordlist
        update_word_in_wordlist(wordlist, current_word)
        save_wordlist(username, wordlist)

        message = 'Correct!'

        # Remove word from incorrect_words if it was there
        session['incorrect_words'] = [w for w in session['incorrect_words'] if w['swahili'] != current_word['swahili']]

        # Move on to the next word
        if not session['review_queue'] and not session['incorrect_words']:
            # Session completed
            session.pop('review_words', None)
            session.pop('current_review_word', None)
            return {
                'message': 'Review session completed!'
            }
        else:
            if not session['review_queue']:
                prepare_review_queue()
            next_word = session['review_queue'].pop(0)
            session['current_review_word'] = next_word
            return {
                'english_word': next_word['english'],
                'message': message
            }
    else:
        # Incorrect input
        # Reset the word's status to 'h4' and update 'due' date
        current_word['status'] = 'h4'
        current_word['due'] = (now + TIME_DELTAS['h4']).isoformat()

        # Update the word in the wordlist
        update_word_in_wordlist(wordlist, current_word)
        save_wordlist(username, wordlist)

        message = 'Incorrect. Please try again.'
        correct_translation = current_word['swahili']

        # Add the word to incorrect_words to repeat it
        if current_word not in session['incorrect_words']:
            session['incorrect_words'].append(current_word)

        # Continue with the same word
        return {
            'english_word': current_word['english'],
            'correct_translation': correct_translation,
            'error': message
        }

def prepare_review_queue():
    """
    Prepares a queue of words for the review session.
    Words are randomized and do not repeat consecutively.
    """
    words = session.get('review_words', [])
    random.shuffle(words)
    session['review_queue'] = words.copy()

    # Add incorrect words back into the queue
    incorrect_words = session.get('incorrect_words', [])
    session['review_queue'].extend(incorrect_words)

def get_next_status(current_status):
    """
    Returns the next status in the hierarchy or the same if at maximum.
    """
    if current_status in TIME_INTERVALS:
        index = TIME_INTERVALS.index(current_status)
        if index + 1 < len(TIME_INTERVALS):
            return TIME_INTERVALS[index + 1]
        else:
            # Maximum interval reached
            return TIME_INTERVALS[-1]
    else:
        # If current status is not recognized, start from 'h4'
        return 'h4'

def update_word_in_wordlist(wordlist, updated_word):
    """
    Updates a word in the wordlist with new status and due date.
    """
    for word in wordlist:
        if word['swahili'] == updated_word['swahili']:
            word['status'] = updated_word['status']
            word['due'] = updated_word['due']
            break
