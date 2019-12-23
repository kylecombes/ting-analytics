#!/usr/bin/python3

import argparse
import pandas as pd
import os
import threading
from threading import Thread, Lock
from data_loader import DataReader
from queue import deque


class BillAnalyzer(Thread):

    def __init__(self, directory, period, callback):
        Thread.__init__(self)
        self.directory = os.path.expanduser(directory)
        self.period = period
        self.callback = callback

    def run(self):
        dr = DataReader()
        file_path_template = os.path.join(self.directory, 'usage', '{}{}.csv')
        for data_type in DataReader.BILL_COMPONENTS:
            filename = file_path_template.format(data_type, self.period)
            dr.load_data_from_csv(filename, data_type)

        pdf_path = os.path.join(self.directory, 'bill-pdfs', '{}.pdf'.format(self.period))
        dfs = dr.read_bill_summary_pdf(pdf_path)
        if dfs is None:
            print('ERROR: Could not resolve contents of bill PDF {}.'.format(self.period))
            self.callback(self.period, None)
            return

        costs = self.resolve_total_base_cost(dfs['usage'])
        fees = float(dfs['summary'].iat[1, 0][1:])

        res = self.calculate_cost_per_line(dr.get_usage_breakdown(), costs, fees)

        total = 0
        for line, line_total in res.items():
            total += line_total

        self.callback(self.period, {
            'usage': res,
            'total-tallied': total,
            'total-read': float(dfs['summary'].iat[2, 0][1:]),
        })

    def calculate_cost_per_line(self, usage, costs, fees):
        lines = set()
        for usage_type in usage.values():
            for line in list(usage_type['surcharges'].keys()):
                lines.add(line)
        res = {line: 0 for line in lines}

        # Look at talk time usage
        self.account_for_usage(usage['talk'], costs['Minutes'], res)

        # Look at text message usage
        self.account_for_usage(usage['text'], costs['Messages'], res)

        # Look at data usage (in kilobytes)
        self.account_for_usage(usage['data'], costs['Megabytes'], res)

        # Add on fees and cost for the line
        num_lines = len(lines)
        fees_per_line = fees / num_lines
        cost_for_line = costs['Devices'] / num_lines
        for line in res.keys():
            res[line] += fees_per_line + cost_for_line

        return res

    def add_usage(self, running_totals, new_usage):
        for line, usage in new_usage.items():
            running_totals[line] += usage

    def account_for_usage(self, usage_item, total_cost, running_totals):
        usage_by_line = usage_item['usage']
        surcharges = usage_item['surcharges']

        total_usage = sum(usage_by_line.values())

        for line, line_usage in usage_by_line.items():
            running_totals[line] += (line_usage / total_usage) * total_cost + surcharges.get(line, 0)

    def resolve_total_base_cost(self, df):
        costs = {}
        for idx, row in df.iterrows():
            cost_name = row[0]
            costs[cost_name] = float(row[2][1:])
        return costs


def print_result(period, result):
    print('Bill', period)
    if result:
        print(result['usage'])
        if 'template-used' in result:
            print('Used template', result['template-used'])
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    data_dir = os.path.expanduser(args.directory)
    # Extract the period names by dropping the '.pdf' file extensions
    periods = [bill[:-4] for bill in os.listdir(os.path.join(data_dir, 'bill-pdfs'))]
    good_processes = []
    problem_processes = []

    console_lock = Lock()

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
        while threading.active_count() - 1 < thread_count:  # Ignore main thread
            if len(q) == 0:
                break
            t = q.popleft()
            t.start()

        t.join()  # FIXME: Probably will crash sometimes

    # Get all phone numbers
    numbers = set()
    for _, process_res in good_processes:
        numbers = numbers.union(set(process_res['usage'].keys()))

    print('Successfully processed bills:')
    totals = dict()
    data = {'periods': []}
    for period, process_res in good_processes:
        data['periods'].append(period)
        print_result(period, process_res)
        for number in numbers:
            share = process_res['usage'].get(number, 0)

            if number not in totals:
                data[number] = [share]
                totals[number] = share
            else:
                data[number].append(share)
                totals[number] += share

    max_num_records = max([len(x) for x in data.values()])
    for number, records in data.items():
        num_records = len(records)
        if num_records < max_num_records:
            x = [0 for _ in range(max_num_records - num_records)]
            x.extend(records)
            data[number] = x

    df = pd.DataFrame(data=data)
    writer = pd.ExcelWriter('output.xlsx')
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
