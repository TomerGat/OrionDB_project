from PyOrion.util_functions import dict_to_str


class Item:
    def __init__(self, data: {}):
        self.data = data

    def get_data_size(self):
        return len(dict_to_str(self.data))
