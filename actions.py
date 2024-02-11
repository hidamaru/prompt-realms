import random
import sys

from results import result_dict
from utils import string_format_modifier


def chance_action(json_data: dict, stat: str, difficulty: int, coin_potential: int):
    stat_modifier = json_data[stat]
    dice_roll = random.randint(1, 6)
    result = dice_roll + stat_modifier - difficulty

    print("*** CHANCE ****", file=sys.stderr)
    print("stat: " + str(stat), file=sys.stderr)
    print("difficulty: " + str(difficulty), file=sys.stderr)
    print("coin_potential: " + str(coin_potential), file=sys.stderr)
    print("dice_roll: " + str(dice_roll), file=sys.stderr)
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
        coins_gained = int(coin_potential + int(coin_potential * (dice_roll/6)))
        json_data['coins'] = json_data['coins'] + coins_gained
        extra_text = extra_text + f"Gained {coins_gained} coins"

    elif result == 7:
        coins_gained = int(coin_potential + int(coin_potential * (dice_roll/3)))
        json_data['coins'] = json_data['coins'] + coins_gained
        extra_text = extra_text + f"Gained {coins_gained} coins"
        if json_data[stat] >= 6:
            extra_text = extra_text + f", {stat} would have increased, but it cannot increase further"
        elif json_data[stat] - difficulty <= 1:
            json_data[stat] = json_data[stat] + 1
            extra_text = extra_text + f", {stat} increased by 1"
        else:
            extra_text = extra_text + f", {stat} would have increased, but the action was not difficult enough"

    elif result >= 8:
        coins_gained = int(coin_potential + int(coin_potential * dice_roll))
        json_data['coins'] = json_data['coins'] + coins_gained
        extra_text = extra_text + f"Gained {coins_gained} coins"
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

    message = message + extra_text

    print("*** MESSAGE ***\n" + str(message) + "\n*************", file=sys.stderr)

    return json_data, message

def attack_action(attacker_json_data: dict, target_json_data: dict, stat: str):
    target = target_json_data["username"]

    attacker_stat_modifier = attacker_json_data[stat]
    target_stat_modifier = target_json_data[stat]
    attacker_dice_roll = random.randint(1, 6)
    target_dice_roll = random.randint(1, 6)
    result = attacker_stat_modifier + attacker_dice_roll - target_stat_modifier - target_dice_roll

    print("*** ATTACK ****", file=sys.stderr)
    print(f'{attacker_json_data["username"]} attacked {target}', file=sys.stderr)
    print("attacker_stat_modifier: " + str(attacker_stat_modifier), file=sys.stderr)
    print("target_stat_modifier: " + str(target_stat_modifier), file=sys.stderr)
    print("attacker_dice_roll: " + str(attacker_dice_roll), file=sys.stderr)
    print("target_dice_roll: " + str(target_dice_roll), file=sys.stderr)
    print("result: " + str(result), file=sys.stderr)

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
                attack_text =  f"\nUser {attacker_json_data['username']} wounded you in combat which reduced your {stat_to_reduce} by 1, and took"
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

        attacker_modifier_formatted = string_format_modifier(target_stat_modifier)

        message = f'Start the reply to the user with this:\n\n'\
                  f'**You rolled {attacker_dice_roll}, {stat} {attacker_modifier_formatted}**\n\n'\
                  f'**{target} rolled: {target_stat_modifier + target_dice_roll}**\n\n'\
                  f'Use this text to describe what happened:\n\n'\
                  f'The player lost {coins_lost} coins to {target} and now has {attacker_json_data["coins"]} coins'

    print("*** MESSAGE ***\n" + str(message) + "\n*************", file=sys.stderr)

    return attacker_json_data, target_json_data, message
