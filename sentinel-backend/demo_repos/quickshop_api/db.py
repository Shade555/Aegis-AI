import sqlite3


def get_user(user_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    # SQL Injection
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
