from flask import Flask, request, session, render_template
from argon2 import PasswordHasher
import subprocess

app = Flask(__name__)
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
    return "미구현"

@app.route('/get_authority', methods=['GET', 'POST'])
def get_authority():
    if request.method == 'GET':
        return "auth.html"
    elif request.method == 'POST':
        admin_pwHash = open('adminPasswordHash.txt', 'r').read().strip()
        pw = request.form.get('password')
        hash = ph.hash(pw)
        if hash == admin_pwHash:
            session['is_admin'] = True
            return



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)