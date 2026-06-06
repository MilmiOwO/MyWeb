from functools import wraps
from argon2.exceptions import VerifyMismatchError
from flask import Flask, request, Response, session, render_template, url_for, jsonify
from argon2 import PasswordHasher
import datetime
import queue
import uuid

app = Flask(__name__)
app.secret_key = open('env/secret_key.txt').read().strip()
port = 5000

ph = PasswordHasher()
requests_store = []
announcers = []

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_admin'):
            return f(*args, **kwargs)
        if request.path.startswith('/api/'):
            return {'error': 'Unauthorized'}, 403
        return render_template('no-permission.html', alert='Login Required', redirect='/auth')
    return decorated_function

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

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        admin_pwHash = open('env/adminPasswordHash.txt', 'r').read().strip()
        pw = request.form.get('password')
        try:
            if ph.verify(admin_pwHash, pw):
                session['is_admin'] = True
                return render_template('auth.html', alert='Login success', redirect=url_for('index'))
        except VerifyMismatchError:
            return render_template('auth.html', error='Wrong password')
        except Exception as e:
            return render_template('auth.html', error='An error occurred while verifying the password ({e})'.format(e=e))
    else:
        if session.get('is_admin'):
            return render_template('auth.html', alert='You already have permission', redirect=url_for('index'))
        return render_template('auth.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, threaded=True)