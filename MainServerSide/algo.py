from main_server_implementation.main_data_directory import MainDataDirectory
from util_functions import get_key_for_highest_value
from network_protocol_implementation.networks_functions import calculate_ttl
from final_values import NUMBER_OF_NODES_TO_OFFER_CLIENT


"""
theory behind algorithm to find closest node to a new client:
1. ping to all nodes and to client
2. ttl is radius of a circle that is the geometric location of each node/client
3. find x nodes for which the radius of the geometric circle location is closest to the radius of the client's circle
4. also find y nodes for which the radius of the geometric circle location is smallest (node is close to the server)
4. send x+y addresses to client, have client ping addresses to check which is closest

explanation - theoretically expressing location of nodes as circles according to ttl allows server to find nodes that
have high chance of being relatively close to new client, as the average distance is theoretically equal to the radius
(ttl) difference
"""


def get_closest_available_nodes(client_address):
    all_nodes = MainDataDirectory().nodes  # {node id: (node data object, node socket)}
    available_node_ids = MainDataDirectory().active_nodes  # list of active node ids
    available_nodes = {}  # should be - {node id: (node data object, node socket)}
    if len(available_node_ids) <= 6:
        return available_node_ids
    for node_id in available_node_ids:
        available_nodes[node_id] = all_nodes[node_id]
    closest_nodes = find_closest_storage_nodes_to_client(client_address, available_nodes)
    closest_nodes.extend(find_closest_storage_nodes_to_server(available_nodes))
    return closest_nodes  # list of closest node ids


def find_closest_storage_nodes_to_server(nodes):  # nodes format is identical to 'nodes' in MainDataDirectory()
    nodes_ttl = {}  # {node id: server to node ttl}

    # create dict of node ids to node ttl (geometric location radius)
    for node_id, node_data_tuple in nodes.items():
        node_data_obj, node_socket = node_data_tuple
        node_ttl = node_data_obj.ttl
        nodes_ttl[node_id] = node_ttl

    # get 3 nodes that are closest to server (have highest ttl after trip)
    highest_ttl = []  # list of node ids with highest ttl
    for _ in range(NUMBER_OF_NODES_TO_OFFER_CLIENT):
        node_id = get_key_for_highest_value(nodes_ttl)
        highest_ttl.append(node_id)
        del nodes_ttl[node_id]

    return highest_ttl


def find_closest_storage_nodes_to_client(client_address, nodes):  # nodes format is identical to 'nodes' in MainDataDirectory()
    nodes_ttl = {}  # {node id: server to node ttl}
    client_ttl = calculate_ttl(client_address[0])

    # create dict of node ids to node ttl (geometric location radius)
    for node_id, node_data_tuple in nodes.items():
        node_data_obj, node_socket = node_data_tuple
        node_ttl = node_data_obj.ttl
        nodes_ttl[node_id] = node_ttl

    # get 3 nodes with smallest ttl delta to new client's ttl
    lowest_ttl_dif = {}  # {node id: ttl delta}
    for node_id, ttl in nodes_ttl.items():
        delta = abs(ttl - client_ttl)
        if len(lowest_ttl_dif) == NUMBER_OF_NODES_TO_OFFER_CLIENT:
            key = get_key_for_highest_value(lowest_ttl_dif)
            del lowest_ttl_dif[key]
        lowest_ttl_dif[node_id] = delta

    return list(lowest_ttl_dif.keys())


def find_nodes_with_database(db_id):
    # get relevant data from main data director
    db_storage_division = MainDataDirectory().db_storage_division  # {db id: {collection name: {node id: [item ids]}}}
    node_storage_data = MainDataDirectory().node_storage_data  # {node id: {id of stored db: {name of stored collection: count of stored items}}}
    database_data = MainDataDirectory().database_data  # {db id: {collection name: [item ids]}}

    # alter data to only contain active nodes (only alter data for relevant db to improve efficiency of algorithm
    active_nodes = MainDataDirectory().active_nodes
    for collection_name in db_storage_division[db_id].keys():
        for node_id in db_storage_division[db_id][collection_name].keys():
            if node_id not in active_nodes:
                del db_storage_division[db_id][collection_name][node_id]
    for node_id in node_storage_data.keys():
        if node_id not in active_nodes:
            del node_storage_data[node_id]

    # Create a set to store the nodes that contain the database data
    nodes_with_db = set()

    def dfs(db_id, collection_name, visited, items_to_find):
        if db_id in visited and collection_name in visited[db_id]:
            return
        visited.setdefault(db_id, set()).add(collection_name)
        collections = db_storage_division.get(db_id, {})
        if collection_name in collections:
            nodes_with_db.update(collections[collection_name].keys())
            for node_id in collections[collection_name]:
                node_items = node_storage_data.get(node_id, {}).get(db_id, {}).get(collection_name, {})
                if items_to_find.issubset(node_items):
                    dfs(db_id, collection_name, visited, items_to_find)
        else:
            return
        visited[db_id].remove(collection_name)

    # Get the items in the given database
    items_to_find = set(database_data.get(db_id, {}).values())

    # Perform a DFS starting from each collection in the given database
    collections = db_storage_division.get(db_id, {})
    for collection_name in collections.keys():
        visited = {}
        dfs(db_id, collection_name, visited, items_to_find)

    return list(nodes_with_db)
