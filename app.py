from flask import (
    Flask, render_template, request, session, redirect, url_for, flash
    )
from functools import wraps
import bcrypt
import io
import contextlib
import cowsay
import os
import yaml
import game

app = Flask(__name__)
app.secret_key = 'a_super_secret_key' 

def get_user_data_path():
    """Returns the absolute path to the users.yaml file, handling test environments."""
    filename = 'users.yaml'
    root_dir = os.path.dirname(__file__)
    if app.config.get('TESTING'): # Use .get() for safety
        return os.path.join(root_dir, 'tests', filename)
    else:
        return os.path.join(root_dir, 'data', filename)
    
def load_user_data():
    """Loads and returns the user data dictionary."""
    file_path = get_user_data_path()
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}

def save_user_data(users):
    """Saves the entire users dictionary to the yaml file."""
    file_path = get_user_data_path()
    with open(file_path, 'w') as file:
        yaml.dump(users, file)

def validate_signin(username, password):
    """Checks username and password against saved credentials."""
    users = load_user_data()

    if username in users:
        stored_password = users[username]['password'].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_password)

    return False

def user_signed_in():
    return 'username' in session

def require_signed_in_user(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if not user_signed_in():
            flash("Please sign in or create an account.")
            return redirect(url_for('signin'))
        
        return func(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET", "POST"])
@require_signed_in_user
def rps_game():
    # Find all sfx files and create URLs
    sfx_dir = os.path.join(app.static_folder, 'sfx')
    sfx_files = [f for f in os.listdir(sfx_dir) if f.endswith('.mp3')]
    sfx_urls = [url_for('static', filename=f'sfx/{fname}') for fname in sfx_files]

    # Initialize score if it's not in the session
    if 'score' not in session:
        session['score'] = [0, 0] # [player, opponent]
        session['game_started'] = False

    # This block handles a player's move
    if request.method == "POST":
        session['game_started'] = True
        session['play_sound'] = True
        player_choice = request.form.get("move")
        computer_choice = game.get_computer_choice()
        result_info = game.determine_round_result(player_choice, computer_choice)

        # Update the score
        if result_info['winner'] == 'player':
            session['score'][0] += 1
        elif result_info['winner'] == 'opponent':
            session['score'][1] += 1

        # Track moves
        users = load_user_data()
        current_user = session['username']
        users[current_user][player_choice] += 1
        save_user_data(users)

        # Check for a game winner after every round
        game_winner = None
        if session['score'][0] >= 3:
            game_winner = 'player'
        elif session['score'][1] >= 3:
            game_winner = 'opponent'

        # Track wins & losses
        if game_winner:
            users = load_user_data()
            current_user = session['username']
            if game_winner == 'player':
                users[current_user]['wins'] += 1
            else:
                users[current_user]['losses'] += 1
            save_user_data(users)

        session['round_data'] = {
            'player_choice': player_choice,
            'computer_choice': computer_choice,
            'winner': result_info['winner'],
            'battle_text': result_info['battle_text']
        }

        session.modified = True

        return redirect(url_for('rps_game'))

    round_data = session.pop('round_data', {})

    # Generate and store cowsay art
    title_art_buffer = io.StringIO()
    with contextlib.redirect_stdout(title_art_buffer):
        cowsay.trex(f"Greetings, {session.get('username', 'human')}!\nWelcome to Raptor, Pterodactyl, Stegosaurus!")
    title_art = title_art_buffer.getvalue()
    win_art_buffer = io.StringIO()
    with contextlib.redirect_stdout(win_art_buffer):
        cowsay.trex('Congratulations, conqueror!\nYou are our new leige!')
    win_art = win_art_buffer.getvalue()

    # Check for a game winner after every round
    game_winner = None
    if session['score'][0] >= 3:
        game_winner = 'player'
    elif session['score'][1] >= 3:
        game_winner = 'opponent'

    # Works with game.js to play a sound
    play_sound_on_load = session.pop('play_sound', False)

    # Render the template with all the necessary data
    return render_template('index.html', 
                           score=session['score'], 
                           round_data=round_data,
                           game_winner=game_winner,
                           title_art=title_art,
                           win_art=win_art,
                           play_sound=play_sound_on_load,
                           sfx_urls=sfx_urls,
                           game_started=session.get('game_started', False))

@app.route("/users/stats")
@require_signed_in_user
def show_stats():
    users = load_user_data()
    current_user = session['username']
    stats = users[current_user]

        # Calculate favorite move
    moves = {
        'Raptor': stats['Raptor'],
        'Pterodactyl': stats['Pterodactyl'],
        'Stegosaurus': stats['Stegosaurus']
    }

    favorite_move = "None yet"
    if any(moves.values()): # Check if any moves have been made
        favorite_move = max(moves, key=moves.get)

    # Calculate percentages
    total_moves = sum(moves.values())
    percentages = {}
    if total_moves > 0:
        for move, count in moves.items():
            percentages[move] = round((count / total_moves) * 100, 1)

    return render_template('stats.html', 
                           stats=stats,
                           favorite_move=favorite_move,
                           percentages=percentages)

@app.route ('/users/signup', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        password_bytes = password.encode('utf-8')

        hashed_password_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        hashed_password_str = hashed_password_bytes.decode('utf-8')

        root_dir = os.path.dirname(__file__)
        file_path = os.path.join(root_dir, 'data', 'users.yaml')

        try:
            with open(file_path, 'r') as file:
                users = yaml.safe_load(file) or {}
        except FileNotFoundError:
            users = {}

        users[username] = {
            'password': hashed_password_str,
            'wins': 0,
            'losses': 0,
            'Raptor': 0,
            'Pterodactyl': 0,
            'Stegosaurus': 0,
        }

        with open('data/users.yaml', 'w') as file:
            print(users)
            yaml.dump(users, file)

        flash(f'Account creation successful! Welcome {username}!')
        session['username'] = username
        session.modified = True

        return redirect(url_for('rps_game'))


    return render_template('account_creation.html')

@app.route('/users/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if validate_signin(username, password):
            flash(f'Welcome to the jungle, {username}!')
            session['username'] = username
            session.modified = True
            return redirect(url_for('rps_game'))
    
    return render_template('signin_form.html')

@app.route("/users/signout", methods=['GET'])
def signout():
    username = session.clear()
    if username:
        flash(f"You have been signed out, {username}.")
    return redirect(url_for('signin'))

# Route to reset the game
@app.route("/reset")
def reset_game():
    session['score'] = [0, 0]
    session['game_started'] = False
    return redirect(url_for('rps_game'))


if __name__ == "__main__":
    app.run(debug=True, port=5003)