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

def load_user_credentials():
    filename = 'users.yaml'
    root_dir = os.path.dirname(__file__)
    if app.config['TESTING']:
        credentials_path = os.path.join(root_dir, 'tests', filename)
    else:
        credentials_path = os.path.join(root_dir, 'data', filename)
    
    with open(credentials_path, 'r') as file:
        return yaml.safe_load(file)

def validate_signin(username, password):
    credentials = load_user_credentials()

    if username in credentials:
        stored_password = credentials[username]['password'].encode('utf-8')
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
    # Initialize score if it's not in the session
    if 'score' not in session:
        session['score'] = [0, 0] # [player, opponent]
        session['game_started'] = False

    # This block handles a player's move
    if request.method == "POST":
        session['game_started'] = True
        player_choice = request.form.get("move")
        computer_choice = game.get_computer_choice()

        # Get results from your game engine
        result_info = game.determine_round_result(player_choice, computer_choice)

        # Update the score (replaces score_keeper())
        if result_info['winner'] == 'player':
            session['score'][0] += 1
        elif result_info['winner'] == 'opponent':
            session['score'][1] += 1

        session['round_data'] = {
            'player_choice': player_choice,
            'computer_choice': computer_choice,
            'winner': result_info['winner'],
            'battle_text': result_info['battle_text']
        }

        session.modified = True

        return redirect(url_for('rps_game'))
    
    round_data = session.pop('round_data', {})

    # Generate and store cowsay title art
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        cowsay.trex("Welcome to Raptor, Pterodactyl, Stegosaurus!")
    title_art = output_buffer.getvalue()

    # Check for a game winner after every round
    game_winner = None
    if session['score'][0] >= 3:
        game_winner = 'player'
    elif session['score'][1] >= 3:
        game_winner = 'opponent'

    # Render the template with all the necessary data
    return render_template('index.html', 
                           score=session['score'], 
                           round_data=round_data,
                           game_winner=game_winner,
                           title_art=title_art,
                           game_started=session.get('game_started', False))

@app.route("/users/stats")
@require_signed_in_user
def show_stats():
    # Implement after user login implemented
    return "User stats coming soon!"


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
            'password': hashed_password_str
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
    username = session.pop('username', None)
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