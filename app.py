from functools import wraps
import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import Flask, request, Response, session, render_template, url_for, jsonify, abort, send_file
from dotenv import load_dotenv
import sqlite3
import datetime
import queue
import uuid
import os
from werkzeug.utils import secure_filename

ph = PasswordHasher()
requests_store = []
announcers = []

load_dotenv()

admin_hash = os.getenv('ADMIN_HASH')
secret_key = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.secret_key = secret_key
port = 4000
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
DB_PATH = os.path.join(DATA_DIR, 'writeups.db')


def get_db_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    cur = sqlite3.connect(DB_PATH)
    cur.row_factory = sqlite3.Row
    return cur


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    cur = get_db_connection()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS writeups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            cover_image TEXT,
            pdf_file TEXT,
            pdf_original_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    info = cur.execute('PRAGMA table_info(writeups)').fetchall()
    columns = [row[1] for row in info]

    if 'pdf_file' not in columns:
        cur.execute('ALTER TABLE writeups ADD COLUMN pdf_file TEXT')
    if 'pdf_original_name' not in columns:
        cur.execute('ALTER TABLE writeups ADD COLUMN pdf_original_name TEXT')

    legacy_columns = {'slug', 'content'}
    if legacy_columns.intersection(columns):
        cur.execute('ALTER TABLE writeups RENAME TO writeups_old')
        cur.execute('''
            CREATE TABLE writeups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                cover_image TEXT,
                pdf_file TEXT,
                pdf_original_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            INSERT INTO writeups (id, title, summary, cover_image, pdf_file, pdf_original_name, created_at)
            SELECT id, title, summary, cover_image, pdf_file, pdf_original_name, created_at
            FROM writeups_old
        ''')
        cur.execute('DROP TABLE writeups_old')

    cur.execute('DELETE FROM writeups')
    cur.commit()
    cur.close()

init_db()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_admin'):
            return f(*args, **kwargs)
        if request.path.startswith('/api/'):
            abort(403)
        return render_template('no-permission.html', alert='Login required to access this feature.', redirect='/login')
    return decorated_function

@app.errorhandler(403)
def error_403(error):
    return render_template(
        "error.html",
        error_code=403,
        error_message="Unauthorized"
    ),403

@app.errorhandler(404)
def error_404(error):
    return render_template(
        "error.html",
        error_code=404,
        error_message="Not Found"
    ),404

@app.errorhandler(500)
def error_500(error):
    return render_template(
        "error.html",
        error_code=500,
        error_message="Internal Server Error"
    ),500

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/requestbin')
@admin_required
def requestbin():
    return render_template('requestbin.html')


@app.route('/q', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/q/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_request(subpath=None):
    headers_str = "\n".join([f"{k}: {v}" for k, v in request.headers.items()])
    body_str = request.get_data(as_text=True) or ""
    raw_http = f"{request.method} {request.path} HTTP/1.1\n{headers_str}\n\n{body_str}"

    req_data = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "method": request.method,
        "path": request.path,
        "args": dict(request.args),
        "headers": dict(request.headers),
        "body": request.get_data(as_text=True),
        "ip": request.remote_addr,
        "raw_http": raw_http
    }
    requests_store.insert(0, req_data)
    if len(requests_store) > 100:
        requests_store.pop()
    for i in reversed(range(len(announcers))):
        try:
            announcers[i].put("data: update\n\n")
        except:
            announcers.pop(i)
    return {'status': 'good'}, 200

@app.route('/api/requests')
@admin_required
def get_requests():
    return jsonify({"requests": requests_store})

@app.route('/api/requests/delete', methods=['POST'])
@admin_required
def delete_requests():
    global requests_store
    data = request.get_json()
    ids_to_delete = data.get('ids', [])
    requests_store = [req for req in requests_store if req['id'] not in ids_to_delete]
    return jsonify({
        "status": "success",
        "message": f"{len(ids_to_delete)} requests deleted from server"
    })

@app.route('/api/stream')
@admin_required
def stream():
    q = queue.Queue()
    announcers.append(q)
    def event_stream():
        while True:
            yield q.get()
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/writeups', methods=['GET'])
def writeups():
    cur = get_db_connection()
    writeups = cur.execute(
        'SELECT * FROM writeups ORDER BY created_at DESC'
    ).fetchall()
    cur.close()
    return render_template('writeups.html', writeups=writeups)


@app.route('/writeup/<int:writeup_id>', methods=['GET'])
def writeup(writeup_id):
    return render_template('writeup.html')


@app.route('/writeup/upload', methods=['GET', 'POST'])
@admin_required
def writeup_upload():
    if request.method == "POST":
        return jsonify({'status': 'success'})
    return render_template('writeup_upload.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not admin_hash:
            return render_template('login.html', error='Server configuration error: ADMIN_HASH is missing')

        pw = request.form.get('password')
        try:
            if ph.verify(admin_hash, pw):
                session['is_admin'] = True
                return render_template('login.html', alert='Login success', redirect=url_for('index'))
        except VerifyMismatchError:
            return render_template('login.html', error='Wrong password')
        except Exception as e:
            return render_template('login.html', error='An error occurred while verifying the password ({e})'.format(e=e))
    else:
        if session.get('is_admin'):
            return render_template('login.html', alert='You already have permission', redirect=url_for('index'))
        return render_template('login.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, threaded=True)