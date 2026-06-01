from flask import Flask, request, session, render_template, redirect, url_for, abort, flash
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

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/tools', methods=['GET'])
def tools():
    return render_template('tools.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        admin_pwHash = open('env/adminPasswordHash.txt', 'r').read().strip()
        pw = request.form.get('password')
        if ph.verify(admin_pwHash, pw):
            if session.get('is_admin') and session.get('is_admin') == True:
                flash('you already have permission!', 'message')
                return redirect(url_for('index'))
            else:
                session['is_admin'] = True
                return render_template('index.html', message = 'login success - Hello, admin!')
        else:
            return render_template('auth.html', message = 'wrong password')
    else:
        return render_template('auth.html')

app.route('/logout', methods=['POST'])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)