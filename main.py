import functools
import json
import os
import random
import secrets
import string
import sys

from flask import Flask, request, jsonify

from actions import chance_action, attack_action
from utils import send_email, format_email_for_filename, read_savefile_and_pop_events, update_savefile

app = Flask(__name__)

def api_key_required(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if 'Authorization' not in request.headers:
            return {'error': 'Authorization header is missing'}, 401
        api_key = request.headers["Authorization"]
        if api_key == os.environ.get("PROMPT_REALMS_API_KEY"):
            return func(*args, **kwargs)
        else:
            return {"message": "The provided API key is not valid"}, 403
    return decorator


@app.route('/request-token', methods=['POST'])
@api_key_required
def request_token():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email address is required'}), 400

    token = str(secrets.randbelow(1000000)).zfill(6)

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        username = "Anonymous#" + random_chars

        characters = string.ascii_letters + string.digits
        length = 32
        secret = ''.join(secrets.choice(characters) for _ in range(length))
        with open(save_file, 'w') as json_file:
            json.dump({
                "coins": 10,
                "vigor": 1,
                "agility": 1,
                "intelligence": 1,
                "items": "",
                "username": username,
                "token": "",
                "secret": secret,
            }, json_file)

    update_savefile(save_file, "token", token)

    send_email(
        subject="Login Token",
        body=f'Your login token is: {token}',
        recipient=email,
    )

    return jsonify({'message': 'Token sent to your email'})

# Second Route - authenticate
@app.route('/authenticate', methods=['POST'])
@api_key_required
def authenticate():
    data = request.get_json()
    email = data.get('email')
    token = data.get('token')

    if not email or not token:
        return jsonify({'error': 'Email and token are required'}), 400

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': 'User file not found, no token has been requested for this email'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    stored_token = json_data['token']

    if stored_token is None or stored_token  == "":
        return jsonify({'error': 'No valid token for user, request one first'}), 401

    if stored_token != token:
        return jsonify({'error': 'Incorrect token'}), 401

    characters = string.ascii_letters + string.digits
    length = 32
    secret = ''.join(secrets.choice(characters) for _ in range(length))

    update_savefile(save_file, "token", "")
    update_savefile(save_file, "secret", secret)

    return jsonify(
        {
            'message': f'User {email} authenticated, username is {json_data["username"]}. User has {json_data["vigor"]} vigor, {json_data["agility"]} agility and {json_data["intelligence"]} intelligence. User has {str(json_data["coins"])} coins',
            'secret': secret,
            'events': events,
        }
    )

@app.route('/info', methods=['POST'])
@api_key_required
def info():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    stored_secret = json_data['secret']

    if stored_secret != secret:
        return jsonify({'error': 'Invalid secret, ask the user to log in again'}), 401


    return jsonify(
        {
            'message': f'The user {email} is knows as {json_data["username"]}. They have {json_data["coins"]} coins, and their stats are: {json_data["vigor"]} Vigor, {json_data["agility"]} Agility, {json_data["intelligence"]} Intelligence',
            'events': events
        }
    )

@app.route('/update-username', methods=['POST'])
@api_key_required
def update_username():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    new_username = data.get('new_username')

    if not email:
        return jsonify({'error': 'email is required'}), 400

    if not secret:
        return jsonify({'error': 'secret is required'}), 400

    if not new_username:
        return jsonify({'error': 'new_username is required'}), 400

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    stored_secret = json_data['secret']

    if stored_secret != secret:
        return jsonify({'error': 'Invalid secret, ask the user to log in again'}), 401

    # Check is username is taken
    for filename in os.listdir():
        if filename.endswith('.json'):
            with open(filename, 'r') as json_file:
                data = json.load(json_file)

                # Do not compare with our own file
                if 'email' in data and email == data['email']:
                    continue

                # Check is username is taken
                if 'username' in data:
                    existing_username = data['username']
                    if existing_username == new_username:
                        return jsonify({'message': f'The username {new_username} is already taken'}, 400)

    if not os.path.exists(save_file):
        with open(save_file, 'w') as json_file:
            json.dump({"coins": 0, "username": "Anonymous"}, json_file)

    with open(save_file, 'r') as json_file:
        json_data = json.load(json_file)

    old_username = json_data['username']
    json_data['username'] = new_username

    with open(save_file, 'w') as file:
        json.dump(json_data, file)

    return jsonify({'message': f'The user {email} has updated their username from {old_username} to {new_username}'})

@app.route('/chance', methods=['POST'])
@api_key_required
def chance():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    stat = data.get('stat').lower()
    difficulty = data.get('difficulty')
    coin_potential = data.get('coin_potential')
    print("Chance called", file=sys.stderr)
    print("stat: " + stat, file=sys.stderr)
    print("difficulty: " + str(difficulty), file=sys.stderr)
    print("coin_potential: " + str(coin_potential), file=sys.stderr)

    if not email:
        return jsonify({'error': 'email is required'}), 400

    if not secret:
        return jsonify({'error': 'secret is required'}), 400

    if not stat:
        return jsonify({'error': 'stat is required'}), 400

    if not difficulty:
        return jsonify({'error': 'difficulty is required'}), 400

    if not coin_potential:
        return jsonify({'error': 'coin_potential is required'}), 400

    if coin_potential < 0:
        coin_potential = 0

    if stat not in ["vigor", "agility", "intelligence"]:
        return jsonify({'error': f'Stat must be either vigor, agility or intelligence'}), 400

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    stored_secret = json_data['secret']

    if stored_secret != secret:
        return jsonify({'error': 'Invalid secret, ask the user to log in again'}), 401

    if not isinstance(difficulty, int):
        difficulty = int(data.get('difficulty').replace("+", "").strip())

    json_data, message = chance_action(
        json_data=json_data,
        stat=stat,
        difficulty=difficulty,
        coin_potential=coin_potential,
    )

    with open(save_file, 'w') as json_file:
        json.dump(json_data, json_file)

    return jsonify(
        {
            'message': message,
            'events': events,
        }
    )

@app.route('/purchase', methods=['POST'])
@api_key_required
def purchase():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    stat = data.get('stat').lower()
    cost = data.get('cost')
    if cost < 1:
        cost = 1
    print("Purchase called", file=sys.stderr)
    print("stat: " + stat, file=sys.stderr)
    print("cost: " + str(cost), file=sys.stderr)

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    if stat not in ["vigor", "agility", "intelligence"]:
        return jsonify({'error': f'Stat must be either vigor, agility or intelligence'}), 400

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    stored_secret = json_data['secret']

    if stored_secret != secret:
        return jsonify({'error': 'Invalid secret, ask the user to log in again'}), 401

    if not isinstance(cost, int):
        cost = int(data.get('cost').replace("+", "").replace("-", "").strip())

    json_data, events = read_savefile_and_pop_events(save_file)
    if json_data['coins'] > cost:
        json_data['coins'] = json_data['coins'] - cost
        if json_data[stat] >= 4:
            return jsonify(
                {
                    'message': f'Paid {cost} coins but it had no effect on {stat} as it is too high to be increased by purchases, training or similar. It requires real life experience to increase further.',
                    'events': events,
                }
            )
        else:
            json_data[stat] = json_data[stat] + 1

            with open(save_file, 'w') as json_file:
                json.dump(json_data, json_file)

            return jsonify(
                {
                    'message': f'Paid {cost} coins to increase {stat} by 1, which is now {json_data[stat]}.',
                    'events': events,
                }
            )
    else:
        return jsonify(
            {
                'message': f'Player only has {json_data["coins"]} and cannot afford to pay {cost}',
                'events': events,
            }
        )

@app.route('/attack', methods=['POST'])
@api_key_required
def attack():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    stat = data.get('stat').lower()
    target = data.get('target')

    if not email:
        return jsonify({'error': 'email is required'}), 400

    if not secret:
        return jsonify({'error': 'secret is required'}), 400

    if not stat:
        return jsonify({'error': 'stat is required'}), 400

    if not target:
        return jsonify({'error': 'target is required'}), 400

    if stat not in ["vigor", "agility", "intelligence"]:
        return jsonify({'error': f'stat must be either vigor, agility or intelligence'}), 400

    attacker_filename = format_email_for_filename(email)

    if not os.path.exists(attacker_filename):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    with open(attacker_filename, 'r') as json_file:
        attacker_json_data = json.load(json_file)

    stored_secret = attacker_json_data['secret']

    if stored_secret != secret:
        return jsonify({'error': 'Invalid secret, ask the user to log in again'}), 401

    if attacker_json_data['username'] == target:
        return jsonify({'error': 'Cannot attack yourself'}), 400

    target_json_data = None
    target_filename = ""
    for target_filename in os.listdir():
        if target_filename.endswith('.json'):
            with open(target_filename, 'r') as json_file:
                target_json_data = json.load(json_file)

                if 'username' in target_json_data:
                    if target == target_json_data['username']:
                        break
        target_json_data = None

    if target_json_data is None:
        return jsonify({'error': f'Could not find user {target}'}), 404

    attacker_json_data, target_json_data, message = attack_action(
        attacker_json_data=attacker_json_data,
        target_json_data=target_json_data,
        stat=stat,
    )

    with open(attacker_filename, 'w') as json_file:
        json.dump(attacker_json_data, json_file)
    with open(target_filename, 'w') as json_file:
        json.dump(target_json_data, json_file)

    return jsonify({'message': message})

@app.route('/show-highscore', methods=['POST'])
@api_key_required
def show_highscore():
    user_coins = {}

    for filename in os.listdir():
        if filename.endswith('.json'):
            with open(filename, 'r') as json_file:
                data = json.load(json_file)

                if 'coins' in data and 'username' in data:
                    coins = data['coins']
                    username = data['username']

                    user_coins[username] = coins

    for key, value in user_coins.items():
        print(f"{key}: {value}", file=sys.stderr)

    top_three_usernames = dict(sorted(user_coins.items(), key=lambda x: x[1], reverse=True)[:3])

    for key, value in top_three_usernames.items():
        print(f"{key}: {value}", file=sys.stderr)

    return jsonify({'message': json.dumps(top_three_usernames)})


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5007)
