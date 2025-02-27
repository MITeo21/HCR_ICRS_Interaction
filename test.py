from LLM.session import ChatSession
from Logistics.databaseTest import SerialController


# def check_component_availability(name: str) -> str:
# '''
# Determines the availability of an item in the lab, do not consider the item's relavence to robotics.

# Args:
# name: Name of the item required

# Returns:
# str: A string containing the quantity and location of the component if found
# '''

# return fetch_component(name)

def requestBox(box_id : int) -> int:

    '''
    Fetches information from user about the box they want to fetch, specifically the shelf number.

    Args:
    Box_ID : The ID of the box the user wants to fetch

    Returns:
    int : The shelf number of the box the user wants to fetch
    '''
    comms = SerialController

    return comms.user_box_fetch(box_id)

# session = ChatSession([check_component_availability])
# session.query("Do we have any raspberry pis in the lab?")


session = ChatSession([requestBox])
session.query("Can you fetch me a box 5")