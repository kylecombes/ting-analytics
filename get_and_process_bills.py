import argparse
import os
import pandas as pd
import threading

from data_cache import DataCache
from pathlib import Path
from queue import deque

from ting_api import TingApi
from bill_analyzer import BillAnalyzer

parser = argparse.ArgumentParser()
parser.add_argument('directory')
parser.add_argument('username')
parser.add_argument('password')
args = parser.parse_args()
data_dir = os.path.expanduser(args.directory)

if not args.username or not args.password:
    print('Please specify your Ting account username and password.')


print('Downloading data to', data_dir)
cache = DataCache(data_dir)
ting = TingApi(cache)
ting.connect(args.username, args.password)

bills = ting.get_billing_history(filter_by_types=['bill'])
period_id_to_bill_map = {}

for bill in bills:
    period_id_to_bill_map[bill.period_id] = bill
    print('Downloading bill details', bill.period_id)
    cache.fetch_if_necessary(bill.period_id + '.pdf', bill.pdf_url, ting.session, 'bill-pdfs')
    ting.get_detailed_usage_if_necessary(bill.period_id)

print('All bills downloaded.')
print('Processing bills...')

# Extract the period names by dropping the '.pdf' file extensions
periods = [bill[:-4] for bill in os.listdir(os.path.join(data_dir, 'bill-pdfs'))]
good_processes = []
problem_processes = []

console_lock = threading.Lock()


def print_result(period, result):
    print('Bill', period)
    if result:
        print(result['usage'])
        if 'template-used' in result:
            print('Used template', result['template-used'])
    print()


def bill_processed(period, result):
    console_lock.acquire()
    if result and (round(result['total-tallied']*100))/100 == result['total-read']:
        good_processes.append((period, result))
    else:
        problem_processes.append((period, result))

    print_result(period, result)
    console_lock.release()


q = deque()
for period in periods:
    q.append(BillAnalyzer(data_dir, period, bill_processed))

thread_count = 4
while len(q) > 0:
    t = None
    while threading.active_count() - 1 < thread_count:  # Ignore main thread
        if len(q) == 0:
            break
        t = q.popleft()
        t.start()

    if t is not None:
        t.join()

# Get all phone numbers
phone_numbers = set()
for _, process_res in good_processes:
    phone_numbers = phone_numbers.union(set(process_res['usage'].keys()))

print('Successfully processed bills:')
totals = dict()
data = {'date': [], 'total': []}
for period, process_res in good_processes:
    bill = period_id_to_bill_map[period]
    data['date'].append(bill.date)
    data['total'].append(bill.amount)
    print_result(period, process_res)
    for number in phone_numbers:
        share = process_res['usage'].get(number, 0)

        if number not in totals:
            data[number] = [share]
            totals[number] = share
        else:
            data[number].append(share)
            totals[number] += share

df = pd.DataFrame(data=data)
writer = pd.ExcelWriter(os.path.join(data_dir, 'Ting usage.xlsx'))
df.to_excel(writer, 'Sheet1')
writer.save()

if len(problem_processes) > 0:
    print()
    print('Failed processes:')
    print()
    for period, process_res in problem_processes:
        print_result(period, process_res)

print('Billing shares:')
print(totals)
