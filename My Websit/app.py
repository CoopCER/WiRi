from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages, send_from_directory, jsonify
from datetime import datetime
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Konfiguration für Datei-Uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Pfad zur JSON-Datei und Ordner
USERS_FILE = os.path.join('data', 'users.json')
FILES_DIR = os.path.join('My Websit', 'static', 'files')
FAXFILES_DIR = os.path.join('static', 'files')
FAXPUBLIC_DIR = os.path.join(FAXFILES_DIR, 'public')
FAXGROUPS_DIR = os.path.join(FAXFILES_DIR, 'groups')
PUBLIC_DIR = os.path.join(FILES_DIR, 'public')
GROUPS_DIR = os.path.join(FILES_DIR, 'groups')
CHAT_DIR = os.path.join('data', 'chat')  # Neues Verzeichnis für Chat-Nachrichten

# Stelle sicher, dass die Ordner existieren
for dir_path in [FILES_DIR, PUBLIC_DIR, GROUPS_DIR, CHAT_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def load_users():
    """Lädt die Benutzerdaten aus der JSON-Datei"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {
        'admin': {
            'password': 'password123', 
            'age': 30, 
            'birthdate': '1993-01-01',
            'role': 'admin',
            'permissions': ['download', 'upload', 'delete', 'manage_users'],
            'groups': ['management', 'it']
        },
        'user': {
            'password': 'password456', 
            'age': 25, 
            'birthdate': '1998-01-01',
            'role': 'user',
            'permissions': ['download'],
            'groups': ['it']
        }
    }

def save_users(users):
    """Speichert die Benutzerdaten in der JSON-Datei"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_available_files(username=None):
    """Gibt eine Liste der verfügbaren Dateien zurück"""
    files = {'public': [], 'groups': {}}
    
    # Öffentliche Dateien
    if os.path.exists(PUBLIC_DIR):
        files['public'] = [f for f in os.listdir(PUBLIC_DIR) if os.path.isfile(os.path.join(PUBLIC_DIR, f))]
    
    # Gruppen-Dateien
    if username and username in USERS:
        user_groups = USERS[username].get('groups', [])
        for group in user_groups:
            group_dir = os.path.join(GROUPS_DIR, group)
            if os.path.exists(group_dir):
                files['groups'][group] = [f for f in os.listdir(group_dir) if os.path.isfile(os.path.join(group_dir, f))]
    
    return files

def get_all_groups():
    """Gibt eine Liste aller verfügbaren Gruppen zurück"""
    if os.path.exists(GROUPS_DIR):
        return [d for d in os.listdir(GROUPS_DIR) if os.path.isdir(os.path.join(GROUPS_DIR, d))]
    return []

# Initialisiere USERS beim Start
USERS = load_users()

def has_permission(username, permission):
    """Überprüft, ob ein Benutzer eine bestimmte Berechtigung hat"""
    if username not in USERS:
        return False
    return permission in USERS[username].get('permissions', [])

def is_admin(username):
    """Überprüft, ob ein Benutzer Admin ist"""
    if username not in USERS:
        return False
    return USERS[username].get('role') == 'admin'

def is_group_member(username, group):
    """Überprüft, ob ein Benutzer Mitglied einer Gruppe ist"""
    if username not in USERS:
        return False
    return group in USERS[username].get('groups', [])

def get_user_role(username):
    """Gibt die Rolle eines Benutzers zurück"""
    if username not in USERS:
        return None
    return USERS[username].get('role', 'user')

def get_user_permissions(username):
    """Gibt die Berechtigungen eines Benutzers zurück"""
    if username not in USERS:
        return []
    return USERS[username].get('permissions', [])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    if 'username' in session:
        user_permissions = get_user_permissions(session['username'])
        user_role = get_user_role(session['username'])
        return render_template('home.html', 
                             username=session['username'], 
                             user_permissions=user_permissions,
                             user_role=user_role)
    elif 'guest' in session:
        return render_template('home.html', username='Gast', user_permissions=['download'], user_role='guest')
    return redirect(url_for('login'))

@app.route('/gamechoose')
def gamechoose():
    if 'username' in session or 'guest' in session:
        return render_template('gamechoose.html')
    else:
        flash('Bitte melden Sie sich an, um Spiele zu spielen.', 'error')
        return redirect(url_for('login'))

@app.route('/2048')
def game2048():
    if 'username' in session or 'guest' in session:
        username = session.get('username', 'Gast')
        # Load leaderboard data
        leaderboard = {'scores': []}
        if os.path.exists('data/2048_leaderboard.json'):
            with open('data/2048_leaderboard.json', 'r') as f:
                leaderboard = json.load(f)
        return render_template('2048.html', username=username, leaderboard=leaderboard['scores'])
    else:
        flash('Bitte melden Sie sich an, um das Spiel zu spielen.', 'error')
        return redirect(url_for('login'))

@app.route('/flappy_bird')
def flappy_bird():
    if 'username' in session or 'guest' in session:
        username = session.get('username', 'Gast')
        # Load leaderboard data
        leaderboard = {'scores': []}
        if os.path.exists('data/flappy_bird_leaderboard.json'):
            with open('data/flappy_bird_leaderboard.json', 'r') as f:
                leaderboard = json.load(f)
        return render_template('flappy_bird.html', username=username, leaderboard=leaderboard['scores'])
    else:
        flash('Bitte melden Sie sich an, um das Spiel zu spielen.', 'error')
        return redirect(url_for('login'))

@app.route('/snake')
def snake():
    if 'username' in session or 'guest' in session:
        username = session.get('username', 'Gast')
        # Load leaderboard data
        leaderboard = {'scores': []}
        if os.path.exists('data/snake_leaderboard.json'):
            with open('data/snake_leaderboard.json', 'r') as f:
                leaderboard = json.load(f)
        return render_template('snake.html', username=username, leaderboard=leaderboard['scores'])
    else:
        flash('Bitte melden Sie sich an, um das Spiel zu spielen.', 'error')
        return redirect(url_for('login'))

@app.route('/download')
def download_page():
    if 'username' in session or 'guest' in session:
        username = session.get('username', None)
        files = get_available_files(username)
        return render_template('download.html', files=files)
    else:
        flash('Bitte melden Sie sich an, um Dateien herunterzuladen.', 'error')
        return redirect(url_for('login'))

@app.route('/download/<path:filepath>')
def download_file(filepath):
    if 'username' in session or 'guest' in session:
        try:
            parts = filepath.split('/')
            if parts[0] == 'public':
                return send_from_directory(FAXPUBLIC_DIR, parts[1], as_attachment=True)
            elif parts[0] == 'groups' and len(parts) == 3:
                group = parts[1]
                filename = parts[2]
                if 'username' in session and group in USERS[session['username']].get('groups', []):
                    return send_from_directory(os.path.join(FAXGROUPS_DIR, group), filename, as_attachment=True)
                else:
                    flash('Sie haben keine Berechtigung für diese Datei.', 'error')
            else:
                flash('Ungültiger Dateipfad.', 'error')
        except Exception as e:
            flash(f'Fehler beim Download: {str(e)}', 'error')
        return redirect(url_for('download_page'))
    else:
        flash('Bitte melden Sie sich an, um Dateien herunterzuladen.', 'error')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            flash('Erfolgreich angemeldet!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Falscher Benutzername oder Passwort', 'error')
    
    return render_template('login.html')

@app.route('/guest')
def guest_login():
    session['guest'] = True
    flash('Willkommen als Gast!', 'success')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        age = int(request.form['age'])
        birthdate = request.form['birthdate']
        
        try:
            age = int(request.form['age'])
            birthdate = request.form['birthdate']
            
            # Das Datum wird im Format YYYY-MM-DD erwartet
            birth_date = datetime.strptime(birthdate, '%Y-%m-%d')
            
            # Alter berechnen
            today = datetime.now()
            calculated_age = today.year - birth_date.year
            
            if username in USERS:
                flash('Benutzername bereits vergeben', 'error')
            elif password != confirm_password:
                flash('Passwörter stimmen nicht überein', 'error')
            elif calculated_age != age and calculated_age != age+1:
                flash(f'Alter stimmt nicht überein.', 'error')
            else:
                # Speichere neue Benutzerdaten mit Standardberechtigungen
                USERS[username] = {
                    'password': password,
                    'age': age,
                    'birthdate': birthdate,
                    'role': 'user',
                    'permissions': ['download','upload','manage_groups','gamechoose','chat'],
                    'groups': []
                }
                save_users(USERS)
                flash('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success')
                return redirect(url_for('login'))
        except ValueError as e:
            if 'unconverted data remains' in str(e):
                flash('Ungültiges Datumsformat. Bitte verwenden Sie das Format YYYY-MM-DD', 'error')
            else:
                flash('Ungültige Eingabe. Bitte überprüfen Sie Ihre Angaben.', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()  # Löscht sowohl Benutzer- als auch Gast-Session
    flash('Sie wurden erfolgreich abgemeldet', 'success')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if 'username' not in session:
        flash('Bitte melden Sie sich an, um Dateien hochzuladen.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        target_group = request.form.get('target_group', 'public')
        
        if file.filename == '':
            flash('Keine Datei ausgewählt', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Prüfe Berechtigungen
            if target_group == 'public' and not has_permission(session['username'], 'upload'):
                flash('Sie haben keine Berechtigung zum Hochladen öffentlicher Dateien.', 'error')
                return redirect(request.url)
            elif target_group != 'public' and not is_group_member(session['username'], target_group):
                flash('Sie haben keine Berechtigung für diese Gruppe.', 'error')
                return redirect(request.url)
            
            if target_group == 'public':
                target_dir = PUBLIC_DIR
            else:
                target_dir = os.path.join(GROUPS_DIR, target_group)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
            
            file.save(os.path.join(target_dir, filename))
            flash('Datei erfolgreich hochgeladen', 'success')
            return redirect(url_for('upload_page'))
        else:
            flash('Ungültiger Dateityp', 'error')
            return redirect(request.url)
    
    # Hole die Gruppen, in denen der Benutzer Mitglied ist
    user_groups = USERS[session['username']].get('groups', [])
    can_upload = has_permission(session['username'], 'upload') or len(user_groups) > 0
    
    if not can_upload:
        flash('Sie haben keine Berechtigung zum Hochladen von Dateien.', 'error')
        return redirect(url_for('home'))
        
    return render_template('upload.html', 
                         groups=user_groups, 
                         can_upload_public=has_permission(session['username'], 'upload'))

@app.route('/delete')
def delete_page():
    if 'username' in session:
        if has_permission(session['username'], 'delete'):
            files = get_available_files()
            return render_template('delete.html', files=files)
        else:
            flash('Sie haben keine Berechtigung zum Löschen von Dateien.', 'error')
            return redirect(url_for('home'))
    else:
        flash('Bitte melden Sie sich an, um Dateien zu löschen.', 'error')
        return redirect(url_for('login'))

@app.route('/delete_file/<path:filename>', methods=['POST'])
def delete_file(filename):
    if 'username' not in session:
        flash('Bitte melden Sie sich an.', 'error')
        return redirect(url_for('login'))
    
    try:
        parts = filename.split('/')
        if parts[0] == 'public':
            if not has_permission(session['username'], 'delete'):
                flash('Sie haben keine Berechtigung zum Löschen öffentlicher Dateien.', 'error')
                return redirect(url_for('delete_page'))
            file_path = os.path.join(PUBLIC_DIR, parts[1])
        elif parts[0] == 'groups' and len(parts) == 3:
            group = parts[1]
            if not is_group_member(session['username'], group):
                flash('Sie haben keine Berechtigung für diese Gruppe.', 'error')
                return redirect(url_for('delete_page'))
            file_path = os.path.join(GROUPS_DIR, group, parts[2])
        else:
            flash('Ungültiger Dateipfad.', 'error')
            return redirect(url_for('delete_page'))
        
        if os.path.exists(file_path):
            os.remove(file_path)
            flash('Datei erfolgreich gelöscht.', 'success')
        else:
            flash('Datei nicht gefunden.', 'error')
            
    except Exception as e:
        flash(f'Fehler beim Löschen der Datei: {str(e)}', 'error')
    
    return redirect(url_for('delete_page'))

@app.route('/manage_users')
def manage_users():
    if 'username' in session:
        if has_permission(session['username'], 'manage_users'):
            return render_template('manage_users.html', users=USERS)
        else:
            flash('Sie haben keine Berechtigung zum Verwalten von Benutzern.', 'error')
            return redirect(url_for('home'))
    else:
        flash('Bitte melden Sie sich an, um Benutzer zu verwalten.', 'error')
        return redirect(url_for('login'))
    
@app.route('/invite_user', methods=['GET', 'POST'])
def invite_user():
    if 'username' in session:
        if request.method == 'POST':
            username = request.form.get('username')
            gruppe = request.form.get('gruppe')
            if username in USERS:
                if not gruppe in USERS[username]['groups']:
                    USERS[username]['groups'].append(gruppe)
                    save_users(USERS)
                    flash('Benutzer erfolgreich eingeladen', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Benutzer ist bereits in dieser Gruppe', 'error')
                    return redirect(url_for('invite_user'))
            else:
                flash('Benutzer nicht gefunden', 'error')
        return render_template('invite_user.html')
    else:
        flash('Bitte melden Sie sich an, um Benutzer einzuladen.', 'error')
        return redirect(url_for('login'))

@app.route('/edit_user/<username>', methods=['GET', 'POST'])
def edit_user(username):
    if 'username' in session and has_permission(session['username'], 'manage_users'):
        if request.method == 'POST':
            role = request.form.get('role', 'user')
            permissions = request.form.getlist('permissions')
            groups = request.form.getlist('groups')
            
            if username in USERS:
                USERS[username]['role'] = role
                USERS[username]['permissions'] = permissions
                USERS[username]['groups'] = groups
                save_users(USERS)
                flash('Benutzer erfolgreich aktualisiert', 'success')
                return redirect(url_for('manage_users'))
            else:
                flash('Benutzer nicht gefunden', 'error')
                return redirect(url_for('manage_users'))
        
        if username in USERS:
            all_groups = get_all_groups()
            return render_template('edit_user.html', 
                                username=username, 
                                user_data=USERS[username],
                                all_groups=all_groups)
        else:
            flash('Benutzer nicht gefunden', 'error')
            return redirect(url_for('manage_users'))
    else:
        flash('Sie haben keine Berechtigung zum Verwalten von Benutzern', 'error')
        return redirect(url_for('home'))

@app.route('/save_score', methods=['POST'])
def save_score():
    if 'username' not in session or session['username'] == 'Gast':
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    score = data.get('score')
    game = data.get('game', '2048')  # Default to 2048 if no game specified

    if not score:
        return jsonify({'error': 'No score provided'}), 400

    # Determine which leaderboard file to use based on the game
    leaderboard_files = {
        '2048': 'data/2048_leaderboard.json',
        'snake': 'data/snake_leaderboard.json',
        'flappy_bird': 'data/flappy_bird_leaderboard.json',
        'doodle_jump': 'data/doodle_jump_leaderboard.json',
        'tictactoe': 'data/tictactoe_leaderboard.json'
    }

    leaderboard_file = leaderboard_files.get(game)
    if not leaderboard_file:
        return jsonify({'error': 'Invalid game'}), 400

    # Load existing leaderboard
    if os.path.exists(leaderboard_file):
        with open(leaderboard_file, 'r') as f:
            leaderboard = json.load(f)
    else:
        leaderboard = {'scores': []}

    # Add new score
    new_score = {
        'username': session['username'],
        'score': score,
        'timestamp': datetime.now().isoformat()
    }

    # Remove any existing scores for this user
    leaderboard['scores'] = [s for s in leaderboard['scores'] if s['username'] != session['username']]
    
    # Add the new score
    leaderboard['scores'].append(new_score)

    # Sort scores in descending order
    leaderboard['scores'].sort(key=lambda x: x['score'], reverse=True)

    # Keep only top 10 scores
    leaderboard['scores'] = leaderboard['scores'][:10]

    # Save updated leaderboard
    with open(leaderboard_file, 'w') as f:
        json.dump(leaderboard, f, indent=4)

    return jsonify({'success': True})

@app.route('/manage_groups')
def manage_groups():
    if 'username' in session:
        groups = get_all_groups()
        permissions = get_user_permissions(session['username'])
        return render_template('manage_groups.html', groups=groups, permissions=permissions)
    flash('Sie haben keine Berechtigung zum Verwalten von Gruppen.', 'error')
    return redirect(url_for('home'))

@app.route('/create_group', methods=['POST'])
def create_group():
    if 'username' not in session:
        flash('Sie haben keine Berechtigung zum Erstellen von Gruppen.', 'error')
        return redirect(url_for('home'))
    
    group_name = request.form.get('group_name')
    if not group_name:
        flash('Bitte geben Sie einen Gruppennamen ein.', 'error')
        return redirect(url_for('manage_groups'))
    
    group_dir = os.path.join(GROUPS_DIR, group_name)
    if os.path.exists(group_dir):
        flash('Eine Gruppe mit diesem Namen existiert bereits.', 'error')
    else:
        os.makedirs(group_dir)
        flash('Gruppe erfolgreich erstellt.', 'success')
    
    return redirect(url_for('manage_groups'))

@app.route('/delete_group/<group_name>', methods=['POST'])
def delete_group(group_name):
    if 'username' not in session or not is_admin(session['username']):
        flash('Sie haben keine Berechtigung zum Löschen von Gruppen.', 'error')
        return redirect(url_for('home'))
    
    group_dir = os.path.join(GROUPS_DIR, group_name)
    if os.path.exists(group_dir):
        import shutil
        shutil.rmtree(group_dir)
        flash('Gruppe erfolgreich gelöscht.', 'success')
    else:
        flash('Gruppe nicht gefunden.', 'error')
    
    return redirect(url_for('manage_groups'))

@app.route('/chat')
def chat():
    if 'username' not in session and 'guest' not in session:
        flash('Bitte melden Sie sich an, um den Chat zu nutzen.', 'error')
        return redirect(url_for('login'))
    
    username = session.get('username', 'Gast')
    user_groups = []
    if username != 'Gast':
        user_groups = USERS[username].get('groups', [])
    
    return render_template('chat.html', username=username, groups=user_groups)

@app.route('/api/messages/<group>', methods=['GET'])
def get_messages(group):
    if 'username' not in session and 'guest' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    
    username = session.get('username', 'Gast')
    if username != 'Gast' and not is_group_member(username, group):
        return jsonify({'error': 'Keine Berechtigung für diese Gruppe'}), 403
    
    messages_file = os.path.join(CHAT_DIR, f'{group}_messages.json')
    if os.path.exists(messages_file):
        with open(messages_file, 'r') as f:
            messages = json.load(f)
    else:
        messages = []
    
    return jsonify(messages)

@app.route('/api/messages/<group>', methods=['POST'])
def post_message(group):
    if 'username' not in session and 'guest' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    
    username = session.get('username', 'Gast')
    if username != 'Gast' and not is_group_member(username, group):
        return jsonify({'error': 'Keine Berechtigung für diese Gruppe'}), 403
    
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'Keine Nachricht'}), 400
    
    messages_file = os.path.join(CHAT_DIR, f'{group}_messages.json')
    if os.path.exists(messages_file):
        with open(messages_file, 'r') as f:
            messages = json.load(f)
    else:
        messages = []
    
    messages.append({
        'username': username,
        'message': message,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Behalte nur die letzten 100 Nachrichten
    messages = messages[-100:]
    
    os.makedirs(os.path.dirname(messages_file), exist_ok=True)
    with open(messages_file, 'w') as f:
        json.dump(messages, f)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True) 