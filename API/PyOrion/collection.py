from PyOrion.hash import sha_function
from PyOrion.util_functions import generate_random_number, dict_to_str, validate_string
from PyOrion.data_storage_implementation.item import Item
from PyOrion.merkle_tree import MerkleTree


class Collection:
    def __init__(self):
        self.items = {}  # {item id: item object}
        self.data_size = 0

    def set_data_size(self):
        size = 0
        for item in self.items.values():
            item_data_str = dict_to_str(item.data)
            size += len(item_data_str.encode())
        self.data_size = size

    def generate_merkle_tree(self):
        data_items = [item.data for item in self.items.values()]
        tree = MerkleTree(data_items)
        return tree.root.hash

    def insert_item(self, data: dict):
        if '_id' not in data.keys():
            item_id = self.generate_item_id()
            data['_id'] = item_id
        item_id = data['_id']
        if not validate_string(item_id):
            raise Exception('Invalid item id: "{}"'.format(item_id))
        if item_id not in self.items.keys():
            new_item = Item(data)
            self.items[item_id] = new_item
            self.set_data_size()

    def insert_items(self, items: list):
        for item in items:
            self.insert_item(item)

    def generate_item_id(self):
        random_num = str(generate_random_number())
        item_id = sha_function(random_num)
        if item_id in self.items.keys():
            return self.generate_item_id()
        return item_id

    def find(self, filter: dict):
        items_to_return = []
        for item_id, item in self.items.items():
            if self._matches_filter(item.data, filter):
                items_to_return.append(item_id)
        return items_to_return

    def delete_many(self, filter: dict) -> int:
        deleted_count = 0
        items_to_delete = []
        # Find the items that match the filter criteria
        for item_id, item in self.items.items():
            if self._matches_filter(item.data, filter):
                items_to_delete.append(item_id)
        # Delete the matched items
        for item_id in items_to_delete:
            del self.items[item_id]
            deleted_count += 1
        self.set_data_size()
        return deleted_count

    def _matches_filter(self, data: dict, filter: dict):
        for key, value in filter.items():
            if data.get(key) != value:
                return False
        return True
