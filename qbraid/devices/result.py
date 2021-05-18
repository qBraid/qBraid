from abc import ABC, abstractmethod


class Result(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_counts(self):
        pass
