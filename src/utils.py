import pickle
from typing import Dict
from tinkoff.invest import Order, Quotation
from tinkoff.invest.utils import quotation_to_decimal

def OrderToDict(order: Order, side: str) -> Dict[float, int]:
    return {f'{side}_price': float(quotation_to_decimal(order.price)), f'{side}_quantity': order.quantity}

def save(obj, path):
    with open(path, 'wb') as obj_file:
        pickle.dump(obj, obj_file, protocol=pickle.HIGHEST_PROTOCOL)

def load(path):
    with open(path, 'rb') as obj_file:
        obj = pickle.load(obj_file)
    return obj
