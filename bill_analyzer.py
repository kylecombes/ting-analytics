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
    dr.print_usage_breakdown()

    dfs = dr.read_bill_summary_pdf('bill-{}.pdf'.format(suffix[:-4]), 'tabula-template.json')
    if dfs is None:
        print('ERROR: Could not resolve contents of bill PDF.')
        exit(1)

    costs = resolve_total_base_cost(dfs['usage'])
    taxes_fees = float(dfs['summary'].iat[1, 0][1:])

    # print('Base cost: ${:.2f}\tFees: ${:.2f}'.format(costs, taxes_fees))


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
