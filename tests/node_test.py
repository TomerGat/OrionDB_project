from node_implementation.network_node import NetworkNode
from general_system_functions import get_node_approval, open_node_account


confirm, code = get_node_approval(2000)
string = open_node_account('mynode', '3232', 2000, code)
node = NetworkNode(string)
