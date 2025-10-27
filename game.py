"""
Game logic to be imported by app.py
"""
import json
import random


VALID_CHOICES = {'1': 'Raptor','2': 'Pterodactyl', '3': 'Stegosaurus'}

with open('rps_messages.json', 'r', encoding='utf-8') as file:
    OUTPUT = json.load(file)

def messages(category, message_key):
    """
    Accesses and returns message value from OUTPUT dictionary.
    For now, only battle_text is in json, but formatted so that
    other text could be moved if desired.
    """
    return OUTPUT[category][message_key]

def get_computer_choice():
    """
    Randomly assign and return computer choice.
    """
    return VALID_CHOICES[random.choice(list(VALID_CHOICES.keys()))]

def determine_round_result(player, opponent):
    """
    Compares choices and returns a dictionary with all round results.
    """
    winning_pairs = (
        ('Raptor', 'Stegosaurus'),
        ('Pterodactyl', 'Raptor'),
        ('Stegosaurus', 'Pterodactyl')
    )

    if (player, opponent) in winning_pairs:
        winner = 'player'
    elif player == opponent:
        winner = 'tie'
    else:
        winner = 'opponent'

    # Get the descriptive battle text
    # This logic is adapted from your old battle_text function
    if winner == 'tie':
        text = messages('battle_text', 'tie')
    elif 'Raptor' in (player, opponent) and 'Stegosaurus' in (player, opponent):
        text = messages('battle_text', 'r_vs_s')
    elif 'Pterodactyl' in (player, opponent) and 'Stegosaurus' in (player, opponent):
        text = messages('battle_text', 'p_vs_s')
    elif 'Raptor' in (player, opponent) and 'Pterodactyl' in (player, opponent):
        text = messages('battle_text', 'r_vs_p')
    else:
        text = messages('battle_text', 'tie')

    return {
        'winner': winner,
        'battle_text': text
    }