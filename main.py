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

from utils import send_email, format_email_for_filename, read_savefile_and_pop_events, string_format_modifier, \
    update_savefile

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

    stat_modifier = json_data[stat]
    dice_roll = random.randint(1, 6)
    result = dice_roll + stat_modifier - difficulty

    print("dice_roll: " + str(dice_roll), file=sys.stderr)
    print("raw result: " + str(result), file=sys.stderr)
    print("result: " + str(result), file=sys.stderr)

    result_text_key = result
    if result_text_key > 8:
        result_text_key = 8
    if result_text_key < 1:
        result_text_key = 1
    result_text = result_dict[result_text_key]

    stat_modifier_text = string_format_modifier(stat_modifier)

    message = f'Start the reply to the user with this:\n\n'\
              f'**Rolled {dice_roll}, {stat} ({stat_modifier_text}), difficulty (-{difficulty})**\n\n'\
              f'**({result}) {result_text.split("-")[0].strip()}!**\n\n'\
              f'Use this text to describe what happened:\n\n'\
              f'{result_text}\n\n'

    extra_text = "Weave the following into the story: "

    if result <= 1:
        coins_lost = int(coin_potential*(dice_roll/2))
        if coins_lost > json_data['coins']:
            coins_lost = json_data['coins']
        json_data['coins'] = json_data['coins'] - coins_lost
        extra_text = extra_text + f"Lost {coins_lost} coins"
        if difficulty > 1:
            json_data[stat] = json_data[stat] - 1
            extra_text = extra_text + f", {stat} was reduced by 1"

    elif result == 2:
        coins_lost = int(coin_potential*(dice_roll/3))
        if coins_lost > json_data['coins']:
            coins_lost = json_data['coins']
        json_data['coins'] = json_data['coins'] - coins_lost
        extra_text = extra_text + f"Lost {coins_lost} coins"

    elif result == 3:
        extra_text = extra_text + f"Gained no coins"

    elif result == 4:
        coins_gained = int(coin_potential * (dice_roll / 6))
        json_data['coins'] = json_data['coins'] + coins_gained
        extra_text = extra_text + f"Gained {coins_gained} coins"

    elif result == 5:
        json_data['coins'] = json_data['coins'] + coin_potential
        extra_text = extra_text + f"Gained {coin_potential} coins"

    elif result == 6:
        json_data['coins'] = json_data['coins'] + coin_potential + int(coin_potential * (dice_roll/6))
        extra_text = extra_text + f"Gained {coin_potential} coins"

    elif result == 7:
        json_data['coins'] = json_data['coins'] + coin_potential + int(coin_potential * (dice_roll/3))
        extra_text = extra_text + f"Gained {coin_potential} coins"
        if json_data[stat] >= 6:
            extra_text = extra_text + f", {stat} would have increased, but it cannot increase further"
        elif json_data[stat] - difficulty <= 1:
            json_data[stat] = json_data[stat] + 1
            extra_text = extra_text + f", {stat} increased by 1"
        else:
            extra_text = extra_text + f", {stat} would have increased, but the action was not difficult enough"

    elif result >= 8:
        json_data['coins'] = json_data['coins'] + coin_potential + int(coin_potential * dice_roll)
        extra_text = extra_text + f"Gained {coin_potential} coins"
        for x in ['vigor', 'agility', 'intelligence']:
            if json_data[x] >= 6:
                extra_text = extra_text + f", {x} would have increased, but it cannot increase further"
            elif json_data[x] - difficulty <= 1:
                json_data[x] = json_data[x] + 1
                extra_text = extra_text + f", {x} increased by 1"
            else:
                extra_text = extra_text + f", {x} would have increased, but the action was not difficult enough"

    if json_data['coins'] < 0:
        json_data['coins'] = 0

    with open(save_file, 'w') as json_file:
        json.dump(json_data, json_file)

    return jsonify(
        {
            'message': message + extra_text,
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

    target_filename = None
    for target_filename in os.listdir():
        if target_filename.endswith('.json'):
            with open(target_filename, 'r') as json_file:
                target_json_data = json.load(json_file)

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

        attack_text = ""
        stat_to_reduce = None
        if stat == "vigor":
            if target_json_data['vigor'] + 3 > attacker_json_data['vigor']:
                stat_to_reduce = random.choice(['vigor', 'agility', 'intelligence'])
                target_json_data[stat_to_reduce] = target_json_data[stat_to_reduce] - 1
                attack_text =  f"\nUser {attacker_json_data['username']} wounded you in combat which reduced your {target_json_data} by 1, and took"
            else:
                attack_text =  f"\nUser {attacker_json_data['username']} approached you, and out of fear you surrendered and gave them"
        elif stat == "agility":
            attack_text =  f"\nAn unseen attacker stole"
        elif stat == "intelligence":
            attack_text =  f"\nUser {attacker_json_data['username']} outwitted you or used spells to take"

        if "events" in target_json_data.keys():
            target_json_data['events'] = target_json_data['events'] + f"{attack_text} {coins_taken} coins."
        else:
            target_json_data['events'] = f"User {attacker_json_data['username']} attacked you and stole {coins_taken} coins."
        attacker_json_data['coins'] = own_coins + coins_taken

        with open(attacker_filename, 'w') as json_file:
            json.dump(attacker_json_data, json_file)
        with open(target_filename, 'w') as json_file:
            json.dump(target_json_data, json_file)

        attacker_modifier_formatted = string_format_modifier(attacker_stat_modifier)

        message = f'Start the reply to the user with this:\n\n' \
                  f'**You rolled {attacker_dice_roll}, {stat} {attacker_modifier_formatted}**\n\n' \
                  f'**{target} rolled: {target_stat_modifier + target_dice_roll}**\n\n' \
                  f'Use this text to describe what happened:\n\n'
        if stat == 'vigor':
            if stat_to_reduce:
                message = message + f'The player defeated {target} in combat and took {coins_taken} coins from them. The player now has {attacker_json_data["coins"]} coins.' \
                                    f'\n\nThe player wounded {target} and reduced their {stat_to_reduce} by 1'
            else:
                message = message + f'The player approached {target}, who quivered in fear and gave up {coins_taken} coins. The player now has {attacker_json_data["coins"]} coins.'
        if stat == 'agility':
            message = message + f'Without being seen, the player stole {coins_taken} coins from {target}. The player now has {attacker_json_data["coins"]} coins.'
        if stat == 'intelligence':
            stat_to_learn = random.choice(['vigor', 'agility', 'intelligence', 'coins'])
            message = message + f'The player outwitted {target}, or used spells in order to take {coins_taken} coins from them. The player now has {attacker_json_data["coins"]} coins.' \
                                f'\n\nDoing this, the player also learned that {target} has {target_json_data[stat_to_learn]} {stat_to_learn}.'
    else:
        target_coins = target_json_data["coins"]
        own_coins = attacker_json_data["coins"]
        coins_lost = int(abs(result) + (own_coins * ( abs(result-1) / 5 )))
        if coins_lost > own_coins:
            coins_lost = own_coins
        target_json_data['coins'] = target_coins + coins_lost
        if "events" in target_json_data.keys():
            target_json_data['events'] = target_json_data['events'] + f"\nUser {attacker_json_data['username']} tried to take coins from you but failed, you gained {coins_lost} coins."
        else:
            target_json_data['events'] = f"\nUser {attacker_json_data['username']} tried to take coins from you but failed, you gained {coins_lost} coins."
        attacker_json_data['coins'] = own_coins - coins_lost

        with open(attacker_filename, 'w') as json_file:
            json.dump(attacker_json_data, json_file)
        with open(target_filename, 'w') as json_file:
            json.dump(target_json_data, json_file)

        attacker_modifier_formatted = string_format_modifier(target_stat_modifier)

        message = f'Start the reply to the user with this:\n\n'\
                  f'**You rolled {attacker_dice_roll}, {stat} {attacker_modifier_formatted}**\n\n'\
                  f'**{target} rolled: {target_stat_modifier + target_dice_roll}**\n\n'\
                  f'Use this text to describe what happened:\n\n'\
                  f'The player lost {coins_lost} coins to {target} and now has {attacker_json_data["coins"]} coins'

    print(f'{attacker_json_data["username"]} attacked {target}', file=sys.stderr)

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
