from UserSide.client_implementation.orionclient import OrionClient
from general_system_functions import open_account
import time


client = OrionClient('oriondb.account//tomers=3232')


db = client['mydb']
print(db)
print(db.get_db_details())
