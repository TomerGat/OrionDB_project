import xml.etree.ElementTree as et
from hash import hash_function, sha_function
from data_storage_implementation.item import Item
from util_functions import dict_to_str, str_to_dict, format_for_xml, format_from_xml
from network_protocol_implementation.encryption import encrypt, decrypt
from userside_final_values import NODE_DATA_STORAGE_PATH
import os
from userside_final_values import HASH_LENGTH_LIMIT


class NodeStorage:
    def __init__(self, node_id):
        self.file_path = NODE_DATA_STORAGE_PATH
        try:
            os.mkdir(self.file_path)
            # create initial xml tree with opening and closing elements
            self.root = et.Element('nodestorage')
            self.tree = et.ElementTree(self.root)
            self.initial_key = sha_function(node_id)
            self.encryption_key = str(hash_function(self.initial_key))
            while len(self.encryption_key) != HASH_LENGTH_LIMIT:
                self.initial_key = sha_function(node_id)
                self.encryption_key = str(hash_function(self.initial_key))
            self.update_stored_data()
        except FileExistsError:
            with open(self.file_path, 'r') as file:
                encrypted_tree = file.read()
                if len(encrypted_tree) != 0:
                    encrypted_tree, self.initial_key = encrypted_tree.split('<DELIMITER>')[0], encrypted_tree.split('<DELIMITER>')[1]
                    self.encryption_key = str(hash_function(self.initial_key))
                    decrypted_tree_string = decrypt(encrypted_tree, self.encryption_key)
                    print(decrypted_tree_string)
                    print(type(decrypted_tree_string).__name__)
                    self.tree = et.ElementTree(et.fromstring(decrypted_tree_string))
                    self.root = self.tree.getroot()
                else:
                    # create initial xml tree with opening and closing elements
                    self.root = et.Element('nodestorage')
                    self.tree = et.ElementTree(self.root)
                    self.initial_key = sha_function(node_id)
                    self.encryption_key = str(hash_function(self.initial_key))
                    while len(self.encryption_key) != HASH_LENGTH_LIMIT:
                        self.initial_key = sha_function(node_id)
                        self.encryption_key = str(hash_function(self.initial_key))
                    self.update_stored_data()

    def list_stored_db_ids(self):
        db_ids = []
        for db_elem in self.root.findall('*'):
            db_ids.append(db_elem.tag)
        return db_ids

    def update_stored_data(self):
        xml_string = et.tostring(self.root).decode()
        stored_data_encrypted = encrypt(xml_string, self.encryption_key)
        with open(self.file_path, 'w') as file:
            file.write(stored_data_encrypted + '<DELIMITER>' + self.initial_key)

    def get_db_data_size(self, db_id):
        db_tree = self.root.find(db_id)
        data_size = 0  # {collection name: {item id: item data size}}
        for collection_elem in db_tree.findall('*'):
            for item_elem in collection_elem.findall('*'):
                data_size += len(item_elem.text)
        return data_size

    def get_db_details(self, db_id):  # get info about db
        db_tree = self.root.find(db_id)
        db_data = {}  # {collection name: {item id: item data size}}
        for collection_elem in db_tree.findall('*'):
            key = collection_elem.tag
            items = {}
            for item_elem in collection_elem.findall('*'):
                items[item_elem.tag] = len(item_elem.text)
            db_data[key] = items
        return db_data

    def get_db_data(self, db_id):  # get data saved in db
        db_tree = self.root.find(db_id)
        db_data = {}  # {collection: {item id: item data}}
        for collection_elem in db_tree.findall('*'):
            key = collection_elem.tag
            items = {}
            for item_elem in collection_elem.findall('*'):
                items[item_elem.tag] = str_to_dict(format_from_xml(item_elem.text))
            db_data[key] = items
        return db_data

    def insert_data(self, db_id, collection_name, items: [{}]):
        # get db id element
        db_id_elem = self.root.find(db_id)
        if db_id_elem is None:
            db_id_elem = et.SubElement(self.root, db_id)

        # get collection element
        collection_elem = db_id_elem.find(collection_name)
        if collection_elem is None:
            collection_elem = et.SubElement(db_id_elem, collection_name)

        # add items to collection element if they do not exist, otherwise update the item data
        for item in items:
            item_id = item['_id']
            item_elem = collection_elem.find(item_id)
            if item_elem is None:
                item_elem = et.SubElement(collection_elem, item_id)
            item_elem.text = format_for_xml(dict_to_str(item))
        self.update_stored_data()

    def delete_database(self, db_id):
        db_elem = self.root.find(db_id)
        if db_elem is not None:
            self.root.remove(db_elem)
            self.update_stored_data()

    def delete_collection(self, db_id, collection_name):
        db_elem = self.root.find(db_id)
        if db_elem is not None:
            collection_elem = db_elem.find(collection_name)
            if collection_elem is not None:
                db_elem.remove(collection_elem)
                self.update_stored_data()

    def delete_storage(self):
        # empty txt file
        with open(self.file_path, 'w') as file:
            file.write('')
