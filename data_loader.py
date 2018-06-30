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

    def read_bill_summary_pdf(self, filename, template=None):
        return parse_pdf(filename, template)


    def get_usage_breakdown(self, data_type):
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
            for index, row in data.iterrows():
                user = row[device_id_column]
                surcharge = row['Surcharges ($)']
                DataReader._add_usage(totals, user, 1)
                DataReader._add_usage(surcharges, user, surcharge)

        return totals, surcharges

    def print_usage_breakdown(self):
        # Talk time
        tt, scs = self.get_usage_breakdown(DataReader.MINUTES)
        print('Minutes usage breakdown:')
        for device, usage in tt.items():
            print('\t{}: {} minutes \t\tSurcharges: ${}'.format(device, usage, scs[device]))
        # Messages
        msgs, scs = self.get_usage_breakdown(DataReader.MESSAGES)
        print('Messages usage breakdown:')
        for device, usage in msgs.items():
            print('\t{}: {} messages \t\tSurcharges: ${}'.format(device, usage, scs[device]))
        # Data usage
        data, scs = self.get_usage_breakdown(DataReader.DATA)
        print('Data usage breakdown:')
        for device, usage in msgs.items():
            print('\t{}: {} MB \t\tSurcharges: ${}'.format(device, usage, scs.get(device, 0)))

    @staticmethod
    def _add_usage(totals, user, addition):
        if user not in totals:
            totals[user] = addition
        else:
            totals[user] += addition

