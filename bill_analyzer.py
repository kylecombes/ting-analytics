#!/usr/bin/python3

import argparse
import re
import os
from data_loader import DataReader


def process_bill(filename):
    directory, filename = os.path.split(filename)
    dr = DataReader()
    suffix = re.search('\d*\..*', filename).group(0)
    for data_type in DataReader.BILL_COMPONENTS:
        filename = os.path.join(directory, data_type + suffix)
        dr.load_data_from_csv(filename, data_type)

    dfs = dr.read_bill_summary_pdf('bill-{}.pdf'.format(suffix[:-4]), 'tabula-template.json')
    if dfs is None:
        print('ERROR: Could not resolve contents of bill PDF.')
        exit(1)

    costs = resolve_total_base_cost(dfs['usage'])
    fees = float(dfs['summary'].iat[1, 0][1:])

    res = calculate_cost_per_line(dr.get_usage_breakdown(), costs, fees)

    print()
    total = 0
    for line, line_total in res.items():
        print('Line {}: ${:.2f}'.format(line, line_total))
        total += line_total

    print('Tallied total: ${:.2f}\t Actual total: {}'.format(total, dfs['summary'].iat[2,0]))


def calculate_cost_per_line(usage, costs, fees):
    res = {line: 0 for line in usage['data']['usage'].keys()}

    # Look at talk time usage
    account_for_usage(usage['talk'], costs['Minutes'], res)

    # Look at text message usage
    account_for_usage(usage['text'], costs['Messages'], res)

    # Look at data usage
    account_for_usage(usage['data'], costs['Megabytes'], res)

    # Add on fees and cost for the line
    num_lines = len(usage['text']['usage'])
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
        running_totals[line] += (line_usage / total_usage) * total_cost + surcharges[line]


def resolve_total_base_cost(df):
    costs = {}
    for idx, row in df.iterrows():
        cost_name = row[0]
        costs[cost_name] = float(row[2][1:])
    return costs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    process_bill(args.filename)
