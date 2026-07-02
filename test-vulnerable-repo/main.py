import sqlite3
import os

def get_user_data(user_id):
    # Vulnerability 1: Hardcoded secret
    stripe_key = "sk_live_fake_key_for_testing"
    
    # Vulnerability 2: SQL Injection using f-string
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    
    return cursor.fetchall()
