import os

base = 'sentinel-backend/demo_repos'
os.makedirs(base, exist_ok=True)

# 1. QuickShop API
quickshop = os.path.join(base, 'quickshop_api')
os.makedirs(quickshop, exist_ok=True)
with open(os.path.join(quickshop, 'db.py'), 'w', encoding='utf-8') as f:
    f.write('''import sqlite3
def get_user(user_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    # SQL Injection
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
''')
with open(os.path.join(quickshop, '.env'), 'w', encoding='utf-8') as f:
    f.write('STRIPE_SECRET_KEY=sk_test_1234567890abcdef1234567890\n')
with open(os.path.join(quickshop, 'requirements.txt'), 'w', encoding='utf-8') as f:
    f.write('Flask==1.1.2\nrequests==2.22.0\n')
with open(os.path.join(quickshop, 'auth.py'), 'w', encoding='utf-8') as f:
    f.write('''def validate_password(pwd):
    return True # weak validation
''')

# 2. HealthSync Portal
healthsync = os.path.join(base, 'healthsync_portal')
os.makedirs(healthsync, exist_ok=True)
with open(os.path.join(healthsync, 'config.js'), 'w', encoding='utf-8') as f:
    f.write('const JWT_SECRET = "super_secret_jwt_key_12345";\n')
with open(os.path.join(healthsync, 'index.html'), 'w', encoding='utf-8') as f:
    f.write('<!-- Stored XSS -->\n<div dangerouslySetInnerHTML={{ __html: userData.bio }}></div>\n')
with open(os.path.join(healthsync, 'upload.js'), 'w', encoding='utf-8') as f:
    f.write('''const exec = require('child_process').exec;
function processImage(filename) {
    exec("convert " + filename + " output.png"); // Command Injection
}''')

# 3. FinTrust Platform
fintrust = os.path.join(base, 'fintrust_platform')
os.makedirs(fintrust, exist_ok=True)
os.makedirs(os.path.join(fintrust, 'backend'), exist_ok=True)
with open(os.path.join(fintrust, 'backend', 'api.py'), 'w', encoding='utf-8') as f:
    f.write('''from fastapi import FastAPI
import requests
app = FastAPI()
@app.get("/fetch")
def fetch_url(url: str):
    # SSRF
    return requests.get(url).content
''')
os.makedirs(os.path.join(fintrust, 'frontend'), exist_ok=True)
with open(os.path.join(fintrust, 'frontend', 'app.tsx'), 'w', encoding='utf-8') as f:
    f.write('const AWS_KEY = "AKIAIOSFODNN7EXAMPLE";\n')

print("Created demo repos!")
