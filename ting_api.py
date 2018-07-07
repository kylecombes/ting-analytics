import requests
from bs4 import BeautifulSoup
import json


class TingApi:

    def __init__(self):
        self.session = requests.session()

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

    def get_billing_history(self):
        response = self.session.get('https://ting.com/account/bill_history')
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)
        billing_table = soup.find(id='billingTable')
        items = billing_table.find('tbody').find_all('tr')
        res = []
        for item in items:
            date = item.find('td').text.strip()
            amount = item.find(class_='amountCol').text.strip()
            url = item.find('a')['href']
            bill_type = item.find(class_='billType')['data']

            if bill_type == 'bill':
                pdf_url = item.find(class_='pdfIcon')['href']
                res.append(TingBill(date, amount, url, pdf_url))
            elif bill_type == 'payment':
                res.append(TingPayment(date, amount, url))
            elif bill_type == 'refund':
                res.append(TingCredit(date, amount, url))

        return res


class TingBill:

    def __init__(self, date, amount, url, pdf_url=None):
        self.date = date
        if type(amount) is str:
            amount = float(amount[1:])
        self.amount = amount
        self.url = url
        self.pdf_url = pdf_url


class TingPayment:

    def __init__(self, date, amount, url):
        self.date = date
        if type(amount) is str:
            amount = float(amount[2:])
        self.amount = amount
        self.url = url


class TingCredit(TingPayment):

    pass


if __name__ == '__main__':

    ting = TingApi()
    ting.connect(...)

    hist = ting.get_current_usage_details()

    bills = ting.get_billing_history()

    print(hist)
