from ...gate import Gate


class RV(Gate):
    def __init__(self, v_x, v_y, v_z):
        self.v_x = v_x
        self.v_y = v_y
        self.v_z = v_z

    def name(self):
        return "RV"
