import numpy as np
from typing import Union
from collections import deque


class SimpleMA:

    def __init__(self, n: int) -> None:
        self.n = n
        self.prices = deque(maxlen=n)
        self.weights = np.array([1 for _ in range(0, n)])

    def get(self, price: float) -> Union[None, float]:
        self.prices.append(price)
        if len(self.prices) != self.n:
            return None
        prices = np.array(self.prices)
        res = np.sum((self.weights * prices)) / np.sum(self.weights)
        return res
