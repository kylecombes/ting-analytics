import pandas as pd
from pdf_parser import parse_pdf


class DataReader:

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

    def __init__(self):
        self.data = {}

    def load_data_from_csv(self, filename, data_type):
        """
        Reads data from a file.
        :param filename: the name of the file
        :type filename: string
        :param data_type: 'minutes' | 'messages' | 'data'
        :type data_type: string
        """
        self.data[data_type] = pd.read_csv(filename)

    def read_bill_summary_pdf(self, filename):
        return parse_pdf(filename)

    def _calculate_usage_breakdown(self, data_type):
        """
        Calculates the usage by device/user.
        :param data_type: MESSAGES | MINUTES | DATA
        :return: the total usage and surcharges for each device
        :rtype (dict, dict)
        """
        data = self.data[data_type]
        totals = {}
        surcharges = {}

        device_id_column = DataReader.DEVICE_ID_MAP[data_type]
        # Split behavior based on summation type
        if data_type == DataReader.MESSAGES:  # Messages are just a tally
            for index, row in data.iterrows():
                user = row[device_id_column]
                surcharge = row['Surcharges ($)']
                DataReader._add_usage(totals, user, 1)
                DataReader._add_usage(surcharges, user, surcharge)
        else:  # Everything else has a quantity associated with each entry
            usage_key = 'Duration (min)' if data_type == DataReader.MINUTES else 'Kilobytes'
            for index, row in data.iterrows():
                user = row[device_id_column]
                usage = row[usage_key]
                surcharge = row['Surcharges ($)']
                DataReader._add_usage(totals, user, usage)
                DataReader._add_usage(surcharges, user, surcharge)

        return totals, surcharges

    def get_usage_breakdown(self):
        res = {}
        # Talk time
        tt, scs = self._calculate_usage_breakdown(DataReader.MINUTES)
        res['talk'] = {
            'usage': tt,
            'surcharges': scs,
        }

        # Messages
        msgs, scs = self._calculate_usage_breakdown(DataReader.MESSAGES)
        res['text'] = {
            'usage': msgs,
            'surcharges': scs,
        }

        # Data usage
        data, scs = self._calculate_usage_breakdown(DataReader.DATA)
        res['data'] = {
            'usage': data,
            'surcharges': scs,
        }

        return res

    def print_usage_breakdown(self):
        usage = self.get_usage_breakdown()

        print('Minutes usage breakdown:')
        talk = usage['talk']
        for device, usage in talk['usage'].items():
            print('\t{}: {} minutes \t\tSurcharges: ${}'.format(device, usage, talk['surcharges'][device]))

        text = usage['text']
        print('Messages usage breakdown:')
        for device, usage in usage['text'].items():
            print('\t{}: {} messages \t\tSurcharges: ${}'.format(device, usage, text['surcharges'][device]))

        data = usage['data']
        print('Data usage breakdown:')
        for device, usage in usage['data'].items():
            print('\t{}: {} MB \t\tSurcharges: ${}'.format(device, usage, data['surcharges'].get(device, 0)))

    @staticmethod
    def _add_usage(totals, user, addition):
        if user not in totals:
            totals[user] = addition
        else:
            totals[user] += addition

