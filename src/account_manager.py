from uuid import uuid4
from tinkoff.invest import (
    Client,
    Quotation,
    OrderDirection,
    OrderType
)
from decimal import getcontext, Decimal


class ACCManager:

    def __init__(
            self,
            token: str,
            figi: str,
            id_acc: str) -> None:

        self.token = token
        self.figi = figi
        self.id_acc = id_acc
        self.price = None

    def __calculate_price(self, points: float) -> Quotation:
        getcontext().prec = 2
        fraction = Decimal(points % 1)
        units = int(points // 1)
        nano = int(fraction * Decimal("10e8"))
        return Quotation(units=units, nano=nano)

    def manage_orders_and_sl(
            self, signal: dict, quantity: int) -> None:

        if signal is None:
            return None
        if self.price == self.__calculate_price(points=signal['price']):
            return None
        else:
            self.price = self.__calculate_price(points=signal['price'])

        order_id = str(uuid4())

        # LONG
        if signal['action'] == 'open' and signal['side'] == 'long':
            with Client(self.token) as cli:
                # create buy order
                cli.orders.post_order(
                    figi=self.figi,
                    quantity=quantity,
                    price=self.price,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=self.id_acc,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    order_id=order_id
                )
            print('[Long side opened]')
            return None
        if signal['action'] == 'close' and signal['side'] == 'long':
            with Client(self.token) as cli:
                # create sell order
                cli.orders.post_order(
                    figi=self.figi,
                    quantity=quantity,
                    price=self.price,
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    account_id=self.id_acc,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    order_id=order_id
                )
            print('[Long side closed]')
            return None

        # SHORT
        if signal['action'] == 'open' and signal['side'] == 'short':
            with Client(self.token) as cli:
                # create buy order
                cli.orders.post_order(
                    figi=self.figi,
                    quantity=quantity,
                    price=self.price,
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    account_id=self.id_acc,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    order_id=order_id
                )
            print('[Short side opened]')
            return None
        if signal['action'] == 'close' and signal['side'] == 'short':
            with Client(self.token) as cli:
                # create sell order
                cli.orders.post_order(
                    figi=self.figi,
                    quantity=quantity,
                    price=self.price,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=self.id_acc,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    order_id=order_id
                )
            print('[Short side closed]')
            return None
