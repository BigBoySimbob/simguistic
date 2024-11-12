import csv
from datetime import datetime, timedelta

word_list = []

REVIEW_INTERVALS = {
    '': timedelta(hours=4),         
    'h4': timedelta(hours=24),     
    'h24': timedelta(days=6),     
    'd6': timedelta(days=12),    
    'd12': timedelta(days=24),   
    'd24': timedelta(days=48),    
    'd48': timedelta(days=96),    
    'd96': timedelta(days=180)    
}

import os

def load_word_list(file_path='word_list.csv'):
    global word_list
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            word_list = [row for row in reader]
            if word_list:
                print(f"Loaded {len(word_list)} words from {file_path}")
            else:
                print(f"File {file_path} is empty or has invalid data.")
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")


def save_word_list(file_path='word_list.csv'):
    global word_list
    with open(file_path, mode='w', newline='') as file:
        fieldnames = ['english', 'swahili', 'status', 'due']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for word in word_list:
            writer.writerow(word)