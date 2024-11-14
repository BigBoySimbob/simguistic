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
                due_words.append(word)

    if not due_words:
        return {'message': 'No words are due for review!'}

    session['review_words'] = due_words
    session['review_queue'] = []
    session['review_state'] = 'testing'

    prepare_review_queue()

    current_word = session['review_queue'].pop(0)
    session['current_review_word'] = current_word

    return {
        'english_word': current_word['english'],
        'state': 'testing'
    }

def process_review_input(user_input):
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    current_word = session.get('current_review_word')
    if not current_word:
        return {'error': 'No word is currently being reviewed.'}

    review_state = session.get('review_state', 'testing')
    correct_translation = current_word['swahili']
    user_input_clean = user_input.strip().lower()
    correct_answer = correct_translation.strip().lower()

    wordlist = load_wordlist(username)
    now = datetime.now()

    if review_state == 'testing':
        if user_input_clean == correct_answer:
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

            # Remove word from review_words
            session['review_words'] = [word for word in session['review_words'] if word['swahili'] != current_word['swahili']]

            message = 'Correct!'
            session['review_state'] = 'correct'
            session['last_user_input'] = user_input

            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'message': message,
                'state': 'correct',
                'delay': True
            }
        else:
            # Incorrect input
            # Reset the word's status to 'h4' and update 'due' date
            current_word['status'] = 'h4'
            current_word['due'] = (now + TIME_DELTAS['h4']).isoformat()

            # Update the word in the wordlist
            update_word_in_wordlist(wordlist, current_word)
            save_wordlist(username, wordlist)

            # Add the word back into the queue at a random position
            insert_index = random.randint(1, len(session['review_queue']))
            session['review_queue'].insert(insert_index, current_word)

            session['review_state'] = 'incorrect'
            session['last_user_input'] = user_input
            session['correct_translation'] = correct_translation

            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'correct_translation': correct_translation,
                'error': 'Incorrect.',
                'state': 'incorrect',
                'delay': True
            }

    elif review_state == 'incorrect':
        # Move on to next word
        if session['review_words'] or session['review_queue']:
            if not session['review_queue']:
                prepare_review_queue()
            next_word = session['review_queue'].pop(0)
            session['current_review_word'] = next_word
            session['review_state'] = 'testing'
            return {
                'english_word': next_word['english'],
                'state': 'testing'
            }
        else:
            session.clear()
            return {
                'message': 'Review session completed!',
                'state': 'completed'
            }

    elif review_state == 'correct':
        # Move on to next word
        if session['review_words'] or session['review_queue']:
            if not session['review_queue']:
                prepare_review_queue()
            next_word = session['review_queue'].pop(0)
            session['current_review_word'] = next_word
            session['review_state'] = 'testing'
            return {
                'english_word': next_word['english'],
                'state': 'testing'
            }
        else:
            session.clear()
            return {
                'message': 'Review session completed!',
                'state': 'completed'
            }

def prepare_review_queue():
    words = session.get('review_words', [])
    random.shuffle(words)
    session['review_queue'] = words.copy()

def get_next_status(current_status):
    if current_status in TIME_INTERVALS:
        index = TIME_INTERVALS.index(current_status)
        if index + 1 < len(TIME_INTERVALS):
            return TIME_INTERVALS[index + 1]
        else:
            return TIME_INTERVALS[-1]
    else:
        return 'h4'

def update_word_in_wordlist(wordlist, updated_word):
    for word in wordlist:
        if word['swahili'] == updated_word['swahili']:
            word['status'] = updated_word['status']
            word['due'] = updated_word['due']
            break
