# wordlist_utils.py

import csv
import os
from datetime import datetime

def load_wordlist(username):
    """
    Loads the user's wordlist from a CSV file.
    """
    filepath = os.path.join('users', f'{username}_wordlist.csv')
    wordlist = []
    if not os.path.exists(filepath):
        return wordlist  # Return empty list if file doesn't exist
    with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            word = {
                'english': row['english'],
                'swahili': row['swahili'],
                'status': row.get('status', ''),
                'due': row.get('due', '')
            }
            wordlist.append(word)
    return wordlist

def save_wordlist(username, wordlist):
    """
    Saves the user's wordlist to a CSV file.
    """
    filepath = os.path.join('users', f'{username}_wordlist.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['english', 'swahili', 'status', 'due']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for word in wordlist:
            writer.writerow(word)

def calculate_due_date(status):
    """
    Calculates the next due date based on the word's status.
    """
    from datetime import timedelta
    now = datetime.now()
    time_deltas = {
        'h4': timedelta(hours=4),
        'h24': timedelta(hours=24),
        'd6': timedelta(days=6),
        'd12': timedelta(days=12),
        'd24': timedelta(days=24),
        'd48': timedelta(days=48),
        'd96': timedelta(days=96),
        'd180': timedelta(days=180),
    }
    return (now + time_deltas.get(status, timedelta(hours=4))).isoformat()

def get_word_counts(username):
    """
    Returns the number of words learned and due for review.
    """
    wordlist = load_wordlist(username)
    total_learned = sum(1 for word in wordlist if word['status'])
    now = datetime.now()
    due_for_review = sum(1 for word in wordlist if word['status'] and word['due'] and datetime.fromisoformat(word['due']) <= now)
    not_learned = sum(
        1 for word in wordlist
        if not word.get('status') and not word.get('due'))
    return total_learned, due_for_review, not_learned

def get_wordlist_filepath(username):
    # Adjust the path according to where your wordlists are stored
    return os.path.join('users/', f'{username}_wordlist.csv')