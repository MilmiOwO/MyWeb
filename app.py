import os
from flask import Flask, request, session, render_template
from argon2 import PasswordHasher
import subprocess

app = Flask(__name__)
app.secret_key = open('env/secret_key.txt').read().strip()
port = 5000

ph = PasswordHasher()

result = subprocess.run(
    ['ipconfig'],
    capture_output=True,
    text=True
)
lines = result.stdout.split('\n')
idx = lines.index('Wireless LAN adapter Wi-Fi:')
line = lines[idx + 4]
ip = line.split()[-1]
print(ip + ':' + str(port))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/requestbin')
def requestbin():
    return "coming soon"

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        admin_pwHash = open('env/adminPasswordHash.txt', 'r').read().strip()
        pw = request.form.get('password')
        hash = ph.hash(pw)
        print(pw)
        print(hash)
        print(admin_pwHash)
        if hash == admin_pwHash:
            session['is_admin'] = True
            return render_template('index.html', alert = 'login success - Hello, admin!')
        else:
            return render_template('auth.html', error = 'wrong password')
    else:
        if session.get('is_admin') == True:
            return render_template('index.html', alert = 'you already have a permission!')
        else:
            return render_template('auth.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)