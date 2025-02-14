from LLM.session import ChatSession

def check_component_availability(name: str) -> str:
    '''
    Determines the availability of an item in the lab, do not consider the item's relavence to robotics.

    Args:
        name: Name of the item required

    Returns:
        str: A json containing the quantity and location of the component if found 
    '''
    
    db = {"raspberry pi":5}
    if name.lower() in db:
        result = f"There are {db[name.lower()]} of {name} in the lab"
    else:
        result = f"There are no {name} in the lab"
    return result
session = ChatSession([])
session.query("Hello")
