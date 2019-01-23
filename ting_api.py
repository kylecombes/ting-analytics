import requests
from bs4 import BeautifulSoup
import json
from data_cache import DataCache
from pathlib import Path
from time import sleep


class TingApi:

    def __init__(self, cache=None):
        self.session = requests.session()
        self.cache = cache

    def connect(self, email, password):
        login_details = {
            'agent_logged_in': False,
            'createType': 'login',
            'is_remember_me': False,
            'isAllowStorage': True,
            'login_type': 'password',
            'email': email,
            'password': password,
        }

        # Get the necessary cookies and CSRF token
        self.session.get('https://ting.com/api/tmw/v1/ping')
        self.session.get('https://ting.com/json/get_unviewed_notifications')

        headers = {
            'Host': 'ting.com',
            'Referer': 'https://ting.com/useraccount/login',
            'X-CSRF-Token': requests.utils.unquote(self.session.cookies['csrf_token']),
        }

        login_response = self.session.post('https://ting.com/api/tmw/v1/login', json=login_details, headers=headers)

        # TODO Figure out why this is necessary
        self.get_current_usage_details()

        return json.loads(login_response.text)


    def get_current_usage_details(self):
        response = self.session.get('https://ting.com/json/account/get_account_usage_details')
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def get_billing_history(self, filter_by_types=None):
        response = self.session.get('https://ting.com/account/bill_history')
        soup = BeautifulSoup(response.text, 'html.parser')
        billing_table = soup.find(id='billingTable')
        items = billing_table.find('tbody').find_all('tr')
        res = []
        for item in items:
            date = item.find('td').text.strip()
            amount = item.find(class_='amountCol').text.strip()
            url = item.find('a')['href']
            bill_type = item.find(class_='billType')['data']

            if filter_by_types and bill_type not in filter_by_types:
                continue

            if bill_type == 'bill':
                pdf_url = item.find(class_='pdfIcon')['href']
                res.append(TingBill(date, amount, url, pdf_url))
            elif bill_type == 'payment':
                res.append(TingPayment(date, amount, url))
            elif bill_type == 'refund':
                res.append(TingCredit(date, amount, url))

        return res

    def get_detailed_usage(self, period_id):
        url = 'https://ting.com/json/account/usage_csv?download=1'
        for usage_type in ['minutes', 'messages', 'megabytes']:
            r = self.session.post(
                'https://ting.com/json/account/usage_csv',
                data={'period_id': period_id, 'type': usage_type}
            )
            r = json.loads(r.text)
            sleep(0.3)
            if r['success'] == 1:
                filename = '{}{}.csv'.format(usage_type, period_id)
                self.cache.add_file_if_necessary(filename, url, self.session, 'usage')
            else:
                print('Requesting {}{}.csv generation failed'.format(usage_type, period_id))


class TingBill:

    def __init__(self, date, amount, url, pdf_url=None):
        self.date = date
        if type(amount) is str:
            amount = float(amount[1:])
        self.amount = amount
        self.url = url
        self.period_id = url.split('/')[-1]
        self.pdf_url = pdf_url

    def __str__(self):
        return 'Bill for ${:.2f} on {} (URL: {} PDF: {})'.format(self.amount, self.date, self.url, self.pdf_url)


class TingPayment:

    def __init__(self, date, amount, url):
        self.date = date
        if type(amount) is str:
            amount = float(amount[2:])
        self.amount = amount
        self.url = url

    def __str__(self):
        return 'Payment of ${:.2f} on {} (URL: {})'.format(self.amount, self.date, self.url)


class TingCredit(TingPayment):

    def __str__(self):
        return 'Credit for ${:.2f} on {} (URL: {})'.format(self.amount, self.date, self.url)


if __name__ == '__main__':

    cache_dir = Path.home() / 'ting-data'
    cache = DataCache(cache_dir)
    ting = TingApi(cache)
    ting.connect(...)

    # hist = ting.get_current_usage_details()

    bills = ting.get_billing_history(filter_by_types=['bill'])

    for bill in bills:
        print('Downloading deets for bill', bill.period_id)
        cache.add_file_if_necessary(bill.period_id + '.pdf', bill.pdf_url, ting.session, 'bill-pdfs')
        ting.get_detailed_usage(bill.period_id)


