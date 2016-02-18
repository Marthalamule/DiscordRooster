import arrow
from collections import defaultdict
import csv
import evelink.api
import evelink.corp
import evelink.eve
import random

from config.credentials import CORP_KEYID, CORP_VCODE
from config.lotto_settings import LOTTO_HIT, TICKET_PRICE, CSV_NAME

# Declaring local vars
api = evelink.api.API(api_key=(CORP_KEYID, CORP_VCODE))
eve_corp = evelink.corp.Corp(api=api)
wallet_journal = eve_corp.wallet_journal(limit=1000, before_id=None)
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


def pick_lotto_winner():
    with open(CSV_NAME, 'r') as output_reader:
        all_entries = defaultdict(list)
        entrant_numbers = defaultdict(dict)
        total_weekly_tickets = 0
        raffle_counter = 0
        for entries in output_reader:
            formatted_entries = entries.split(',')
            all_entries[str(formatted_entries[1])].append(int(formatted_entries[-1]))
        list(all_entries.items())
    for x in all_entries:
        print('Entrant: {0}'.format(x))
        entrant_tickets = []
        for y in all_entries[x]:
            total_weekly_tickets += y
            entrant_tickets.append(y)
        total_entrant_tickets = sum(entrant_tickets)
        print('Tickets purchased: {0}'.format(total_entrant_tickets))
        ticket_numbers = []
        for rc in range(total_entrant_tickets):
            raffle_counter += 1
        raffle_num_start = raffle_counter - total_entrant_tickets
        raffle_num_end = raffle_num_start + total_entrant_tickets
        for num in range(raffle_num_start, raffle_num_end):
            ticket_numbers.append(num)
        entrant_numbers[x] = ticket_numbers

    print('Total tickets purchased this week: {0}'.format(total_weekly_tickets))
    print(entrant_numbers)
    winning_number = random.randrange(total_weekly_tickets)
    for winner in entrant_numbers:
        for raffle_ticket_numbers in entrant_numbers[winner]:
            if raffle_ticket_numbers == winning_number:
                this_weeks_winner = winner
    print('The winning number this week is: {0}\nThis Week\'s Winner: {1}'.format(winning_number, this_weeks_winner))


pick_lotto_winner()

# TODO: Cross check blue status to confirm the entrant is valid
# TODO: Function to organize the weekly lotto information for display
# TODO: Tie into Rooster for automatic pings & !lotto command
# TODO: Error checking / stress testing
