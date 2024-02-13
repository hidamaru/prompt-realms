import json
import os
import random
import secrets
import string
import sys
import time

from actions import chance_action, attack_action

bots = {
    "sir_aradrian": {
        "coins": 250,
        "vigor": 3,
        "agility": 1,
        "intelligence": 2,
        "items": "",
        "username": "Sir Aradrian",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "the_demon_king": {
        "coins": 780,
        "vigor": 5,
        "agility": 4,
        "intelligence": 4,
        "items": "",
        "username": "The Demon King",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "an_ambitious_goblin": {
        "coins": 40,
        "vigor": 1,
        "agility": 3,
        "intelligence": 0,
        "items": "",
        "username": "An ambitious goblin",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "the_red_dragon": {
        "coins": 890,
        "vigor": 4,
        "agility": 5,
        "intelligence": 5,
        "items": "",
        "username": "The Red Dragon",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "alufgardh": {
        "coins": 80,
        "vigor": 2,
        "agility": 3,
        "intelligence": 1,
        "items": "",
        "username": "Alufgardh",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "andorai": {
        "coins": 340,
        "vigor": 2,
        "agility": 5,
        "intelligence": 4,
        "items": "",
        "username": "Andorai",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "olthragan": {
        "coins": 520,
        "vigor": 4,
        "agility": 2,
        "intelligence": 3,
        "items": "",
        "username": "Olthragan",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
    "mothek": {
        "coins": 420,
        "vigor": 4,
        "agility": 3,
        "intelligence": 1,
        "items": "",
        "username": "Mothek",
        "token": "",
        "secret": ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)),
        "events": "",
    },
}

for bot_name in bots.keys():
    print(f"Resetting {bot_name}")
    with open(f"{bot_name}.json", 'w') as f:
        json.dump({
            "coins": bots[bot_name]["coins"],
            "vigor": bots[bot_name]["vigor"],
            "agility": bots[bot_name]["agility"],
            "intelligence": bots[bot_name]["intelligence"],
            "items": bots[bot_name]["items"],
            "username": bots[bot_name]["username"],
            "token": bots[bot_name]["token"],
            "secret": bots[bot_name]["secret"],
            "events": bots[bot_name]["events"],
        }, f)


while True:
    # Clean up events
    for bot in list(bots.keys()):
        with open(f"{bot}.json", 'r') as json_file:
            bot_json_data = json.load(json_file)

        bot_json_data["events"] = ""

        with open(f"{bot}.json", 'w') as json_file:
            json.dump(bot_json_data, json_file)


    bot_to_act = random.choice(list(bots.keys()))

    with open(f"{bot_to_act}.json", 'r') as json_file:
        bot_to_act_json = json.load(json_file)

    action = random.choice(["chance", "attack"])
    bot_vigor = bot_to_act_json["vigor"]
    bot_agility = bot_to_act_json["agility"]
    bot_intelligence = bot_to_act_json["intelligence"]

    stat_choice_list = ["vigor"] * bot_vigor + ["agility"] * bot_agility + ["intelligence"] * bot_intelligence

    stat = random.choice(stat_choice_list)

    if action == "chance":
        max_difficulty = bot_to_act_json[stat]
        difficulty = random.randint(0, max_difficulty)
        coin_potential = int(random.randint(1,9) * (10**(difficulty-1)))

        print(f"{bot_to_act} does a {difficulty} {stat} farm", file=sys.stderr)
        bot_to_act_json, _ = chance_action(
            json_data=bot_to_act_json,
            stat=stat,
            difficulty=difficulty,
            coin_potential=coin_potential,
        )

        with open(f"{bot_to_act}.json", 'w') as json_file:
            json.dump(bot_to_act_json, json_file)

    else:
        all_targets = {}
        for player_file in os.listdir():
            if player_file.endswith('.json'):
                with open(player_file, 'r') as json_file:
                    target_json_data = json.load(json_file)

                    if 'username' in target_json_data:
                        if bot_to_act_json['username'] == target_json_data['username']:
                            continue
                        else:
                            all_targets[target_json_data['username']] = player_file
            target_json_data = None

        target_username = random.choice(list(all_targets.keys()))

        with open(f"{all_targets[target_username]}", 'r') as json_file:
            target_json = json.load(json_file)

        bot_to_act_json, target_json, _ = attack_action(
            attacker_json_data=bot_to_act_json,
            target_json_data=target_json,
            stat=stat,
        )

        with open(f"{bot_to_act}.json", 'w') as json_file:
            json.dump(bot_to_act_json, json_file)
        with open(f"{all_targets[target_username]}", 'w') as json_file:
            json.dump(target_json, json_file)

    time.sleep(60 * (10 + random.randint(0, 5)))
