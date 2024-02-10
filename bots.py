import json
import os
import random
import secrets
import string
import time

bot_names = ["Sir Aradrian", "The Demon King", "An ambitious goblin", "The Red Dragon", "Alufgardh", "Andorai", "Olthragan", "Mothek"]

secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

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
    if not os.path.exists(f"{bot_name}.json"):
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
    print(bot_name)


while True:
    bot_to_act = random.choice(list(bots.keys()))
    action = random.choice(["farm", "attack"])
    bot_vigor = bots[bot_to_act]["vigor"]
    bot_agility = bots[bot_to_act]["agility"]
    bot_intelligence = bots[bot_to_act]["intelligence"]

    stat_choice_list = ["vigor"] * bot_vigor + ["agility"] * bot_agility + ["intelligence"] * bot_intelligence

    stat = random.choice(stat_choice_list)

    if action == "farm":
        max_difficulty = bots[bot_to_act][stat]
        difficulty = random.randint(0, max_difficulty)
        print(f"{bot_to_act} does a {difficulty} {stat} farm")
    else:
        all_targets = list(bots.keys())
        all_targets.remove(bot_to_act)
        target = random.choice(all_targets)
        print(f"{bot_to_act} attacks {target} using {stat}")

    time.sleep(60 * (10 + random.randint(0, 5)))
