from LLM.session import ChatSession
from Logistics.databaseTest import ComponentDatabase, SerialController, BoxDatabase



componentDatabase = ComponentDatabase()
box_db = BoxDatabase()
serialController = SerialController(box_db)
def requestBox(box_id : int) -> int:

    '''
    Checks where the box is in the lab

    Args:
    Box_ID : The box number the user wants to fetch

    Returns:
    int : The shelf number of the box the user wants to fetch
    '''
    comms = serialController

    return comms.user_box_fetch(box_id)

def check_component_availability(name: str) -> str:
    '''
    Determines the availability of an item in the lab, do not consider the item's relavence to robotics.

    Args:
        name: Name of the item required

    Returns:
        str: A string containing the quantity and location of the component if found 
    '''

    return componentDatabase.fetch_component(name)

# session = ChatSession([check_component_availability])
# session.query("Do we have any raspberry pis in the lab?")


session = ChatSession([check_component_availability, requestBox])
session.query("Help me find box 2")