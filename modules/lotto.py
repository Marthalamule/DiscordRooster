import arrow
from collections import defaultdict
import csv
import evelink.api
import evelink.corp
import evelink.eve
import random

from config.credentials import CORP_KEYID, CORP_VCODE
from config.lotto_settings import LOTTO_HIT, TICKET_PRICE, CSV_NAME, STARTER_BLUES

# Declaring local vars
api = evelink.api.API(api_key=(CORP_KEYID, CORP_VCODE))
player_api = evelink.eve.EVE()
eve_corp = evelink.corp.Corp(api=api)
wallet_journal = eve_corp.wallet_journal(limit=1000, before_id=None)
corp_standings = eve_corp.contacts()
corp_standings_final = []
corp_standings_final.append(STARTER_BLUES)  # Populates the initial Blue listing with your Corp/Alliance/Friends
corp_standings_dict = defaultdict(dict)
output_file = open(CSV_NAME, 'a+', newline='')
output_writer = csv.writer(output_file, dialect='excel')
current_time = arrow.utcnow()
last_week = arrow.utcnow().replace(weeks=-1)


def get_lotto_entries_from_wallet():
    for x in wallet_journal.result:
        submission_time = arrow.get(x['timestamp'])
        entrant_name_get = x['party_1']
        entrant_name = entrant_name_get['name']
        entrant_deposit = x['amount']
        number_of_tickets = int(entrant_deposit / TICKET_PRICE)
        entrant_output = [submission_time, entrant_name, entrant_deposit, number_of_tickets]
        if x['type_id'] in LOTTO_HIT:
            parsed_reason = x['reason'].split()
            for reason in parsed_reason:
                if reason.lower() in LOTTO_HIT:
                    if submission_time > last_week:
                        output_writer.writerow(entrant_output)
    output_file.close()


def player_sheet(id, api):
    info = api.character_info_from_id(id.result)
    name = info.result['name']
    corp = info.result['corp']['name']
    alliance = info.result['alliance']['name']
    return name, corp, alliance


def get_corp_standings():
    corp_standings_dict[''] = corp_standings.result
    for x in corp_standings_dict['']:
        for y in corp_standings_dict[''][x]:
            for z in corp_standings_dict[''][x][y]:
                try:
                    if corp_standings_dict[''][x][y]['standing'] > 0.0:
                        corp_standings_final.append(corp_standings_dict[''][x][y]['name'])
                except KeyError:
                    continue
    return corp_standings_final


def pick_lotto_winner():
    with open(CSV_NAME, 'r') as output_reader:
        lotto_winners_name = ''
        all_entries = defaultdict(list)
        entrant_numbers = defaultdict(dict)
        total_weekly_tickets = 0
        raffle_counter = 0
        for entries in output_reader:
            formatted_entries = entries.split(',')
            all_entries[str(formatted_entries[1])].append(int(formatted_entries[-1]))
        list(all_entries.items())
    for x in all_entries:
        entrant_tickets = []
        for y in all_entries[x]:
            total_weekly_tickets += y
            entrant_tickets.append(y)
        total_entrant_tickets = sum(entrant_tickets)
        ticket_numbers = []
        for rc in range(total_entrant_tickets):
            raffle_counter += 1
        raffle_num_start = raffle_counter - total_entrant_tickets
        raffle_num_end = raffle_num_start + total_entrant_tickets
        for num in range(raffle_num_start, raffle_num_end):
            ticket_numbers.append(num)
        entrant_numbers[x] = ticket_numbers
    winning_number = random.randrange(total_weekly_tickets)
    for winner in entrant_numbers:
        for raffle_ticket_numbers in entrant_numbers[winner]:
            if raffle_ticket_numbers == winning_number:
                this_weeks_winner = winner
                try:
                    attempt_winner = player_sheet(player_api.character_id_from_name(this_weeks_winner), player_api)
                    if attempt_winner[0] in corp_standings_final:
                        lotto_winners_name = list(attempt_winner[0])
                        return lotto_winners_name
                    elif attempt_winner[1] in corp_standings_final:
                        lotto_winners_name = list(attempt_winner[1])
                        return lotto_winners_name
                    elif attempt_winner[2] in corp_standings_final:
                        lotto_winners_name = list(attempt_winner[2])
                        return lotto_winners_name
                    else:
                        print('Invalid Entry\nNew Draw Commencing. . .\n')
                        pick_lotto_winner()
                        continue
                except evelink.api.APIError:
                    print('Character({0}) does not exist - someone tampered with the csv\n'.format(this_weeks_winner))
                    print('New Draw Commencing. . .\n')
                    pick_lotto_winner()
                    continue

get_corp_standings()
pick_lotto_winner()
# TODO: Format return strings for Discord
# TODO: Function to organize the weekly lotto information for display
# TODO: Tie into Rooster for automatic pings & !lotto command
# TODO: Error checking / stress testing
