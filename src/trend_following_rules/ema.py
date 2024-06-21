import numpy as np
from typing import Union


class ExponentialMA:

    def __init__(self, n: int) -> None:
        self.n = n
        self.lmbd = (n - 1) / (n + 1)
        self.prices = np.array([])
        self.weights = np.array([])

    def get(self, price: float) -> Union[None, float]:
        self.prices = np.append(self.prices, [price])
        i = len(self.prices) - 1
        w = (1 - self.lmbd) * (self.lmbd ** i)
        self.weights = np.append(self.weights, [w])
        if len(self.prices) < self.n:
            return None
        return sum(self.weights[::-1] * self.prices)
