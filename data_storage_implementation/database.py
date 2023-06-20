from data_storage_implementation.collection import Collection


class DB:
    def __init__(self, name: str):
        self.db_name = name
        self.collections = {}  # {col name: collection}

    def __getitem__(self, key):
        return self.collections[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Collection):
            raise Exception('Cannot set collection to a type that is not a collection.')
        self.collections[key] = value

    def create_collection(self, collection_name: str):
        self.collections[collection_name] = Collection()

    def to_dict(self):
        db_data = {}  # {collection name: {item id: item data}}
        for col_name, collection in self.collections.items():
            items = dict(zip(list(collection.items.keys()), [item.data for item in collection.items.values()]))
            db_data[col_name] = items
        return db_data

    def get_db_details(self):  # get details in the format of 'database_data' in MDD - {collection name: {item id: item data size}}
        collection_names = list(self.collections.keys())
        collections = {}
        for col_name in collection_names:
            collections[col_name] = dict(
                zip(self.collections[col_name].items.keys(), [item.get_data_size() for item in self.collections[col_name].items.values()])
            )
        return collections

    def list_collections(self):
        return list(self.collections.keys())

    def rename_collection(self, previous_name, new_name):
        try:
            self.collections[new_name] = self.collections[previous_name]
            del self.collections[previous_name]
        except KeyError:
            raise Exception('Collection name not found: "{}"'.format(previous_name))

    def get_item_count(self):
        counter = 0
        for collection_name in self.collections:
            counter += len(list(self.collections[collection_name].items.keys()))
        return counter

    def drop_collection(self, collection_name: str):
        try:
            del self.collections[collection_name]
        except KeyError:
            raise Exception('Collection name not found: "{}"'.format(collection_name))
