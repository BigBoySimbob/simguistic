# user_management.py

from flask import session
import os

def get_users():
    """
    Retrieves the list of users by scanning the 'users' directory
    for CSV files named '{username}_wordlist.csv'.
    """
    users = []
    users_dir = 'users'
    if not os.path.exists(users_dir):
        os.makedirs(users_dir)
    for filename in os.listdir(users_dir):
        if filename.endswith('_wordlist.csv'):
            username = filename[:-14]  # Removes '_wordlist.csv' from the filename
            users.append(username)
    return users

def set_current_user(username):
    """
    Sets the current user in the session.
    """
    session['current_user'] = username

def get_current_user():
    """
    Retrieves the current user from the session.
    """
    return session.get('current_user', None)
