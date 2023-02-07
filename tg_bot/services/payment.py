import datetime
import uuid
from dataclasses import dataclass

import pyqiwi

from tg_bot.config import load_config, Config


class NotEnoughMoney(Exception):
    pass


class NoPaymentFound(Exception):
    pass


@dataclass
class Payment:
    amount: int
    id: str = None
    config: Config = load_config()
    wallet = pyqiwi.Wallet(token=config.qiwi.token,
                           number=config.qiwi.qiwi_phone)

    def get_id(self):
        return self.id

    def create(self):
        self.id = str(uuid.uuid4())

    def check_payment(self):
        start_date = datetime.datetime.now() - datetime.timedelta(days=2)
        transactions = self.wallet.history(start_date=start_date)["transactions"]
        for transaction in transactions:
            if transaction.comment:
                if self.id in transaction.comment:
                    if float(transaction.total.amount) == float(self.amount):
                        return True
                    else:
                        raise NotEnoughMoney
        else:
            raise NoPaymentFound

    @property
    def invoice(self):
        link = f'https://oplata.qiwi.com/create?publicKey={self.config.qiwi.qiwi_pub_key}&amount={self.amount}&comment={self.id}'
        return link
