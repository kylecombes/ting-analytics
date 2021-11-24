#!/usr/bin/python3
import os
from threading import Thread
from data_loader import DataReader


class BillAnalyzer(Thread):

    def __init__(self, directory, period, callback, template_dir=None):
        Thread.__init__(self)
        self.directory = os.path.expanduser(directory)
        self.period = period
        self.callback = callback
        if template_dir is not None:
            self.template_dir = template_dir
        else:
            self.template_dir = os.path.join(os.getcwd(), 'tabula-templates')

    def run(self):
        dr = DataReader()
        file_path_template = os.path.join(self.directory, '{}{}.csv')
        for data_type in DataReader.BILL_COMPONENTS:
            filename = file_path_template.format(data_type, self.period)
            dr.load_data_from_csv(filename, data_type)

        print('Usage for period', self.period)
        breakdown = dr.get_usage_breakdown()
        usage_by_num = {}
        for category, details in breakdown.items():
            for item, deets in details.items():
                if item != 'usage':
                    continue
                for num, usage in deets.items():
                    if num not in usage_by_num:
                        usage_by_num[num] = {}
                    usage_by_num[num][category] = usage
        lines = sorted(usage_by_num.keys())
        for line in lines:
            print(line)
            for category, tot in usage_by_num[line].items():
                print(f'\t{category}: {tot}')
        return

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

    @staticmethod
    def resolve_total_base_cost(df):
        costs = {}
        for idx, row in df.iterrows():
            cost_name = row[0]
            costs[cost_name] = float(row[2][1:])
        return costs

