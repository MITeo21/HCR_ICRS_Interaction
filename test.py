from Visuals.LLM import ChatSession
from Logistics.databaseTest import create_database,insert_component,fetch_component


def check_component_availability(name: str) -> str:
    '''
    Determines the availability of an item in the lab, do not consider the item's relavence to robotics.

    Args:
        name: Name of the item required

    Returns:
        str: A string containing the quantity and location of the component if found 
    '''

    return fetch_component(name)
session = ChatSession([check_component_availability])
session.query("Do we have any raspberry pis in the lab?")
