import functools
import json
import math
import os
import secrets
import string
import random
import sys

from results import result_dict

from flask import Flask, request, jsonify

from utils import send_email, format_email_for_filename, read_savefile_and_pop_events

app = Flask(__name__)

users = {}
authenticated_users = {}

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
    users[email] = token

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

    stored_token = users.get(email)

    if stored_token is None or stored_token != token:
        return jsonify({'error': 'Invalid email or token'}), 401

    characters = string.ascii_letters + string.digits
    length = 32
    secret = ''.join(secrets.choice(characters) for _ in range(length))

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        username = "Anonymous#" + random_chars
        with open(save_file, 'w') as json_file:
            json.dump({
                "coins": 0,
                "vigor": 0,
                "agility": 0,
                "intelligence": 0,
                "items": "",
                "username": username,
            }, json_file)
        authenticated_users[email] = secret
        return jsonify({'message': f'New user created for {email} with username {username}. User starts with 0 vigor, 0 agility, 0 intelligence. User starts with 0 coins.', 'secret': secret})
    else:
        json_data, events = read_savefile_and_pop_events(save_file)

        authenticated_users[email] = secret
        return jsonify(
            {
                'message': f'User {email} authenticated, username is {json_data["username"]}. User has {json_data["vigor"]} vigor, {json_data["agility"]} agility and {json_data["intelligence"]} intelligence. User has {str(json_data["coins"])} coins', 'secret': secret,
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

    stored_secret = authenticated_users.get(email)

    if stored_secret is None or stored_secret != secret:
        return jsonify({'error': 'Invalid email or secret'}), 401

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

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

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    stored_secret = authenticated_users.get(email)

    if stored_secret is None or stored_secret != secret:
        return jsonify({'error': 'Invalid email or secret'}), 401

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

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

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

@app.route('/update-coins', methods=['POST'])
@api_key_required
def update_coins():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    coin_change = int(data.get('coin_change'))

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    stored_secret = authenticated_users.get(email)

    if stored_secret is None or stored_secret != secret:
        return jsonify({'error': 'Invalid email or secret'}), 401

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    new_coin_value = int(json_data['coins']) + coin_change
    json_data['coins'] = new_coin_value

    with open(save_file, 'w') as file:
        json.dump(json_data, file)

    return jsonify(
        {
            'message': f'The user {email} now has {new_coin_value} coins',
            'events': events,
        }
    )

@app.route('/update-stat', methods=['POST'])
@api_key_required
def update_stat():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    stat = data.get('stat').lower()
    stat_change = int(data.get('stat_change').replace("+", "").strip())

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    stored_secret = authenticated_users.get(email)

    if stored_secret is None or stored_secret != secret:
        return jsonify({'error': 'Invalid email or secret'}), 401

    if stat not in ["vigor", "agility", "intelligence"]:
        return jsonify({'error': f'Stat must be either vigor, agility or intelligence'}), 400

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    json_data, events = read_savefile_and_pop_events(save_file)

    new_stat_value = int(json_data[stat]) + stat_change
    json_data[stat] = new_stat_value

    with open(save_file, 'w') as file:
        json.dump(json_data, file)

    return jsonify(
        {
            'message': f'The user {email} now has {new_stat_value} {stat}',
            'events': events,
        }
    )

@app.route('/chance', methods=['POST'])
@api_key_required
def chance():
    data = request.get_json()
    email = data.get('email')
    secret = data.get('secret')
    stat = data.get('stat').lower()
    challenge_level = data.get('challenge_level')
    print("Chance called", file=sys.stderr)
    print("stat: " + stat, file=sys.stderr)
    print("challenge_level: " + str(challenge_level), file=sys.stderr)

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    if stat not in ["vigor", "agility", "intelligence"]:
        return jsonify({'error': f'Stat must be either vigor, agility or intelligence'}), 400

    stored_secret = authenticated_users.get(email)

    if stored_secret is None or stored_secret != secret:
        return jsonify({'error': 'Invalid email or secret'}), 401

    save_file = format_email_for_filename(email)

    if not os.path.exists(save_file):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    if not isinstance(challenge_level, int):
        challenge_level = int(data.get('challenge_level').replace("+", "").strip())


    json_data, events = read_savefile_and_pop_events(save_file)

    stat_modifier = json_data[stat]
    dice_roll = random.randint(1, 6)
    result = stat_modifier + challenge_level + dice_roll

    if challenge_level > 2 and result > 4:
        result = 4
    if challenge_level > 0 and result > 5:
        result = 5
    if challenge_level > -1 and result > 6:
        result = 6
    if result > 7:
        result = 7
    if result < 0:
        result = 0

    result_text = result_dict[result]
    print("dice_roll: " + str(dice_roll), file=sys.stderr)
    print("message_for_user: " +  f"({result}) {result_text.split('-')[0].strip()}!)", file=sys.stderr)
    print("message_for_gm: " + result_text, file=sys.stderr)

    return jsonify(
        {
            'dice_roll': dice_roll,
            'message_for_user': f"({result}) {result_text.split('-')[0].strip()}!",
            'message_for_gm': result_text,
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
    print("Attack called", file=sys.stderr)
    print("stat: " + stat, file=sys.stderr)
    print("user_to_attack: " + target, file=sys.stderr)

    if not email or not secret:
        return jsonify({'error': 'Email and secret are required'}), 400

    if stat not in ["vigor", "agility", "intelligence"]:
        return jsonify({'error': f'Stat must be either vigor, agility or intelligence'}), 400

    stored_secret = authenticated_users.get(email)

    if stored_secret is None or stored_secret != secret:
        return jsonify({'error': 'Invalid email or secret'}), 401

    attacker_filename = format_email_for_filename(email)

    if not os.path.exists(attacker_filename):
        return jsonify({'error': f'User file not found for email {email}'}), 404

    with open(attacker_filename, 'r') as json_file:
        attacker_json_data = json.load(json_file)

    if attacker_json_data['username'] == target:
        return jsonify({'error': 'Cannot attack yourself'}), 400

    target_filename = None
    for target_filename in os.listdir():
        print('target_filename: ' + target_filename, file=sys.stderr)
        if target_filename.endswith('.json'):
            with open(target_filename, 'r') as json_file:
                target_json_data = json.load(json_file)
                print('target: ' + target, file=sys.stderr)
                print('target_json_data: ' + str(target_json_data), file=sys.stderr)

                if 'username' in target_json_data:
                    print('target_json_data["username"]: ' + target_json_data['username'], file=sys.stderr)
                    if target == target_json_data['username']:
                        break
        target_json_data = None

    if target_json_data is None or target_filename is None:
        return jsonify({'error': f'Could not find user {target}'}), 404

    attacker_stat_modifier = attacker_json_data[stat]
    target_stat_modifier = target_json_data[stat]
    attacker_dice_roll = random.randint(1, 6)
    target_dice_roll = random.randint(1, 6)
    result = attacker_stat_modifier + attacker_dice_roll - target_stat_modifier - target_dice_roll

    if result > 0:
        target_coins = target_json_data["coins"]
        own_coins = attacker_json_data["coins"]
        coins_taken = int(result + (target_coins * ( result / 5 )))
        if coins_taken > target_coins:
            coins_taken = target_coins
        target_json_data['coins'] = target_coins - coins_taken
        if "events" in target_json_data.keys():
            target_json_data['events'] = target_json_data['events'] + f"\nUser {attacker_json_data['username']} attacked you and stole {coins_taken} coins."
        else:
            target_json_data['events'] = f"User {attacker_json_data['username']} attacked you and stole {coins_taken} coins."
        attacker_json_data['coins'] = own_coins + coins_taken

        with open(attacker_filename, 'w') as json_file:
            json.dump(attacker_json_data, json_file)
        with open(target_filename, 'w') as json_file:
            json.dump(target_json_data, json_file)

        message = f"Took {coins_taken} coins from {target}! You now have f{attacker_json_data['coins']} coins."
    else:
        target_coins = target_json_data["coins"]
        own_coins = attacker_json_data["coins"]
        coins_lost = int(abs(result) + (own_coins * ( abs(result-1) / 5 )))
        if coins_lost > own_coins:
            coins_lost = own_coins
        target_json_data['coins'] = target_coins + coins_lost
        if "events" in target_json_data.keys():
            target_json_data['events'] = target_json_data['events'] +f"\nUser {attacker_json_data['username']} attacked you but failed, and you gained {coins_lost} coins."
        else:
            target_json_data['events'] = f"User {attacker_json_data['username']} attacked you but failed, and you gained {coins_lost} coins."
        attacker_json_data['coins'] = own_coins - coins_lost

        with open(attacker_filename, 'w') as json_file:
            json.dump(attacker_json_data, json_file)
        with open(target_filename, 'w') as json_file:
            json.dump(target_json_data, json_file)

        message = f"Lost {coins_lost} coins to {target}! You now have f{attacker_json_data['coins']} coins."

    return jsonify(
        {
            'attacker_dice_roll': attacker_dice_roll,
            'target_dice_roll': target_dice_roll,
            'message': message,
        }
    )

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
