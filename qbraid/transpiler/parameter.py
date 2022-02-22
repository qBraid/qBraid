"""Paramater Module"""


class ParamID:
    """An itermediate representation for storing abstract parameters during the
    transpilation process. This class is needed, as opposed to a serial number,
    in order to distinguish abstract parameters from numbers.

    Attributes:
        index (integer): a serial number given to arbitrarily to each parameter
        name (str): name of the parameter as string
    """

    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name
