from pathlib import Path
import pandas as pd
import argparse
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

MINUTES = 'minutes'
MESSAGES = 'messages'
DATA = 'megabytes'

BILL_COMPONENTS = [
    MESSAGES,
    MINUTES,
    DATA
]

USAGE_KEY_MAP = {
    MINUTES: 'Duration (min)',
    MESSAGES: '',
    DATA: 'Kilobytes'
}

DEVICE_ID_MAP = {
    MINUTES: 'Phone',
    MESSAGES: 'Phone',
    DATA: 'Device'
}


class Usage:
    def __init__(self, usage_type: str):
        self.type = usage_type
        self.totals: Dict[int, int] = {}
        self.surcharges: Dict[int, float] = {}

    def add_usage(self, device_id: int, addition: int):
        if device_id not in self.totals:
            self.totals[device_id] = addition
        else:
            self.totals[device_id] += addition

    def add_surcharge(self, device_id: int, addition: float):
        if device_id not in self.surcharges:
            self.surcharges[device_id] = addition
        else:
            self.surcharges[device_id] += addition


class FileParseResult:
    def __init__(self, date: datetime, usage: Usage):
        self.date = date
        self.usage = usage


def calculate_usage_breakdown(file_path: Path) -> FileParseResult:
    # Read the data
    data = pd.read_csv(file_path)

    # Get the 'megabytes', 'minutes', 'messages' file name prefix
    data_type = re.search('^\D+', file_path.name)[0]

    # Init our results objects
    usage = Usage(data_type)

    # Determine the device identifier column name
    device_id_column_name = DEVICE_ID_MAP[data_type]

    # Split behavior based on summation type
    if data_type == MESSAGES:  # Messages are just a tally
        for index, row in data.iterrows():
            user = row[device_id_column_name]
            surcharge = row['Surcharges ($)']
            usage.add_usage(user, 1)
            usage.add_surcharge(user, surcharge)
    else:  # Everything else has a quantity associated with each entry
        usage_key = 'Duration (min)' if data_type == MINUTES else 'Kilobytes'
        for index, row in data.iterrows():
            user = row[device_id_column_name]
            line_usage = row[usage_key]
            surcharge = row['Surcharges ($)']
            usage.add_usage(user, line_usage)
            usage.add_surcharge(user, surcharge)

    last_date = data['Date'][len(data)-1]

    return FileParseResult(
        # Just ignore the day of the month
        date=datetime.strptime(last_date, '%B %d, %Y').replace(day=1),
        usage=usage,
    )


def group_and_print_results(parse_results: List[FileParseResult], device_ordering: List[int]) -> None:
    periods: Dict[datetime, Dict[str, Usage]] = {}
    # Group by billing period
    for result in parse_results:
        if result.date not in periods:
            periods[result.date] = {}
        periods[result.date][result.usage.type] = result.usage

    # Sort according to date
    ordered_periods: List[Tuple[datetime, Dict[str, Usage]]] = sorted(periods.items(), key=lambda pair: pair[0])

    for date, usages in ordered_periods:
        print(f'For the month of {date.strftime("%B %Y")}:')
        for device in device_ordering:
            print(f"\t{device}:\t", end='')
            if device in usages[MINUTES].totals:
                print(usages[MINUTES].totals[device], end='\t')
            if device in usages[MESSAGES].totals:
                print(usages[MESSAGES].totals[device], end='\t')
            if device in usages[DATA].totals:
                print(usages[DATA].totals[device])


def parse_directory(dir_path: Path) -> List[FileParseResult]:
    data_dir = Path(os.path.expanduser(dir_path))
    if not data_dir.is_dir():
        raise FileNotFoundError(f'Could not find the directory {args.data_dir}')

    tallies: List[FileParseResult] = []

    for file in data_dir.iterdir():
        if file.name.endswith('.csv'):
            tallies.append(calculate_usage_breakdown(file))

    return tallies


# RUN THIS
# This is the latest, working, self-contained code bit (as of 12/6/2020)
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('phone_numbers')
    args = parser.parse_args()
    try:
        # Split the string at spaces and convert to int
        phone_numbers = list(map(int, args.phone_numbers.split(' ')))
    except Exception:
        raise ValueError('Please ensure that your phone numbers are integers separated by spaces')

    # file = Path(os.path.expanduser(args.file_path))
    # if not file.exists():
    #     raise FileNotFoundError(f'Could not find the file {args.file_path}')
    results = parse_directory(args.data_dir)
    group_and_print_results(results, phone_numbers)

