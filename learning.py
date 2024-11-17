# learning.py

from flask import session
from datetime import datetime, timedelta
import random

from user_management import get_current_user
from wordlist_utils import load_wordlist, save_wordlist

def start_learning_session():
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    wordlist = load_wordlist(username)
    unknown_words = [word for word in wordlist if not word['status']]
    if not unknown_words:
        return {'message': 'All words have been learned!'}

    session['learning_words'] = unknown_words[:5]
    session['learning_progress'] = {word['swahili'].strip().lower(): 0 for word in session['learning_words']}
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
    username = get_current_user()
    if not username:
        return {'error': 'No user selected.'}

    current_word = session.get('current_learning_word')
    if not current_word:
        return {'error': 'No word is currently being learned.'}

    learning_state = session.get('learning_state', 'testing')

    if learning_state == 'presentation':
        session['learning_state'] = 'testing'
        return {
            'english_word': current_word['english'],
            'state': 'testing'
        }
    elif learning_state == 'testing':
        correct_translation = current_word['swahili']
        user_input_clean = user_input.strip().lower()
        correct_answer = correct_translation.strip().lower()

        key = correct_answer  # Use the normalized correct answer as the key
        progress = session['learning_progress']

        if user_input_clean == correct_answer:
            progress[key] += 1

            if progress[key] >= 3:
                # Mark word as learned
                wordlist = load_wordlist(username)
                for word in wordlist:
                    if word['swahili'].strip().lower() == key:
                        word['status'] = 'h4'
                        now = datetime.now()
                        due_time = (now + timedelta(hours=4)).replace(second=0, microsecond=0)
                        word['due'] = due_time.isoformat()
                        break
                save_wordlist(username, wordlist)
                session['learning_words'] = [word for word in session['learning_words'] if word['swahili'].strip().lower() != key]
                progress.pop(key, None)
                message = 'New word learned!'
            else:
                message = 'Correct!'

            session['learning_state'] = 'correct'
            session['last_user_input'] = user_input

            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'message': message,
                'state': 'correct',
                'delay': True
            }
        else:
            # Reset progress counter
            progress[key] = 0

            session['learning_state'] = 'correction'
            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'correct_translation': correct_translation,
                'error': 'Incorrect.',
                'state': 'correction'
            }
    elif learning_state == 'correction':
        correct_translation = current_word['swahili']
        user_input_clean = user_input.strip().lower()
        correct_answer = correct_translation.strip().lower()

        if user_input_clean == correct_answer:
            session['learning_state'] = 'testing'
            return {
                'english_word': current_word['english'],
                'state': 'testing'
            }
        else:
            return {
                'english_word': current_word['english'],
                'user_input': user_input,
                'correct_translation': correct_translation,
                'error': 'Please type the correct translation to proceed.',
                'state': 'correction'
            }
    elif learning_state == 'correct':
        if session['learning_words']:
            if not session['learning_queue']:
                prepare_learning_queue()

            if session['learning_queue']:
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
        else:
            session.clear()
            return {
                'message': 'All words have been learned!',
                'state': 'completed'
            }
    else:
        session['learning_state'] = 'presentation'
        return {
            'english_word': current_word['english'],
            'swahili_word': current_word['swahili'],
            'state': 'presentation'
        }

def prepare_learning_queue():
    words = session.get('learning_words', [])
    random.shuffle(words)
    session['learning_queue'] = words.copy()
