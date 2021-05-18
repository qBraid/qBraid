from abc import ABC, abstractmethod, abstractproperty


class Result(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_counts(self):
        pass
