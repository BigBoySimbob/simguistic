# wordlist_utils.py

import csv
import os

def load_wordlist(username):
    filepath = os.path.join('users', f'{username}_wordlist.csv')
    wordlist = []
    with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            wordlist.append(row)
    return wordlist

def save_wordlist(username, wordlist):
    filepath = os.path.join('users', f'{username}_wordlist.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['english', 'swahili', 'status', 'due']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for word in wordlist:
            writer.writerow(word)
