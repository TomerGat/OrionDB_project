from UserSide.client_implementation.orionclient import OrionClient
from general_system_functions import open_account
import time

# string = open_account('tomers', '3232')

data = {
    'key1': {1: 2, 3.5: None},
    'correct': False,
    2: 'number 2'
}

client = OrionClient('oriondb.account//tomers=3232')

db = client['mydb']
db.create_collection('col1')
col = db['col1']
col.insert_item(data)
client.upload_data('mydb')

