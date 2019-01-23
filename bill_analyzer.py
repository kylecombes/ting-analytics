#!/usr/bin/python3

import argparse
import os
from data_loader import DataReader


def process_bill(period, directory):
    dr = DataReader()
    directory = os.path.expanduser(directory)
    file_path_template = os.path.join(directory, 'usage', '{}{}.csv')
    for data_type in DataReader.BILL_COMPONENTS:
        filename = file_path_template.format(data_type, period)
        dr.load_data_from_csv(filename, data_type)

    pdf_path = os.path.join(directory, 'bill-pdfs', '{}.pdf'.format(period))
    dfs = dr.read_bill_summary_pdf(pdf_path)
    if dfs is None:
        print('ERROR: Could not resolve contents of bill PDF.')
        exit(1)

    costs = resolve_total_base_cost(dfs['usage'])
    fees = float(dfs['summary'].iat[1, 0][1:])

    res = calculate_cost_per_line(dr.get_usage_breakdown(), costs, fees)

    total = 0
    for line, line_total in res.items():
        total += line_total

    return {
        'usage': res,
        'total-tallied': total,
        'total-read': dfs['summary'].iat[2, 0],
    }

def calculate_cost_per_line(usage, costs, fees):
    lines = set()
    for usage_type in usage.values():
        for line in list(usage_type['surcharges'].keys()):
            lines.add(line)
    res = {line: 0 for line in lines}

    # Look at talk time usage
    account_for_usage(usage['talk'], costs['Minutes'], res)

    # Look at text message usage
    account_for_usage(usage['text'], costs['Messages'], res)

    # Look at data usage
    account_for_usage(usage['data'], costs['Megabytes'], res)

    # Add on fees and cost for the line
    num_lines = len(lines)
    fees_per_line = fees / num_lines
    cost_for_line = costs['Devices'] / num_lines
    for line in res.keys():
        res[line] += fees_per_line + cost_for_line

    return res


def add_usage(running_totals, new_usage):
    for line, usage in new_usage.items():
        running_totals[line] += usage


def account_for_usage(usage_item, total_cost, running_totals):
    usage_by_line = usage_item['usage']
    surcharges = usage_item['surcharges']

    total_usage = sum(usage_by_line.values())

    for line, line_usage in usage_by_line.items():
        running_totals[line] += (line_usage / total_usage) * total_cost + surcharges.get(line, 0)


def resolve_total_base_cost(df):
    costs = {}
    for idx, row in df.iterrows():
        cost_name = row[0]
        costs[cost_name] = float(row[2][1:])
    return costs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    args = parser.parse_args()
    data_dir = os.path.expanduser(args.directory)
    periods = [bill[:-4] for bill in os.listdir(os.path.join(data_dir, 'bill-pdfs'))]
    good_processes = []
    problem_processes = []
    for period in periods:
        # try:
            res = process_bill(period, data_dir)
            if res['total-tallied'] != res['total-read']:
                problem_processes.append((period, res))
            else:
                good_processes.append((period, res))
        # except Exception as e:
        #     problem_processes.append((period, e))

    for period, process_res in good_processes:
        print('Bill', period)
        print(process_res['usages'])
        print()

    print()
    print('Failed processes:')
    print()
    for period, process_res in problem_processes:
        print('Bill', period)
        print(process_res)
        print()
