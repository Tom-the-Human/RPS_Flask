from flask import (
    Flask, render_template, request, session, redirect, url_for, flash
    )
from functools import wraps
import io
import contextlib
import cowsay
import game

app = Flask(__name__)
# You need a secret key to use sessions
app.secret_key = 'a_super_secret_key' 

def user_signed_in():
    return 'username' in session

def require_signed_in_user(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if not user_signed_in():
            flash("Please sign in or create an account.")
            return redirect(url_for('show_signin_form'))
        
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

@app.route("<username>/stats")
@require_signed_in_user
def show_stats():
    # Implement after user login implemented
    return "User stats coming soon!"

@app.route('/users/signin' methods=['GET', 'POST'])
def show_signin_form():
    return render_template('signin_form.html')

@app.route("/users/signout", methods=['POST'])
def signout():
    session.pop('username', None)
    flash("You have been signed out.")
    return redirect(url_for('index'))

# Route to reset the game
@app.route("/reset")
def reset_game():
    session.clear() # Clears the score
    return redirect(url_for('rps_game'))


if __name__ == "__main__":
    app.run(debug=True, port=5003)