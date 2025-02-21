import sqlite3
from rapidfuzz import fuzz, process
import serial
import time
import json

def create_component_database():
    connection = sqlite3.connect("lab_storage.db")
    cursor = connection.cursor()

    # Categories of components (e.g., Resistors, Microcontrollers, Motors)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # Storage locations (e.g., Shelf A, Drawer 3, Box 5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS StorageLocation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    """)

    # Components table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Component (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        storage_id INTEGER,
        quantity INTEGER DEFAULT 0,
        description TEXT,
        FOREIGN KEY (category_id) REFERENCES Category(id),
        FOREIGN KEY (storage_id) REFERENCES StorageLocation(id)
    )
    """)

    # Transactions for check-in/check-out
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        component_id INTEGER,
        change INTEGER,  -- Positive for check-in, negative for check-out
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (component_id) REFERENCES Component(id)
    )
    """)

    connection.commit()
    connection.close()
## Fetch component code; has fuzzy search capabilities.

def fetch_component(search_query, threshold=80):
    connection = sqlite3.connect("lab_storage.db")
    cursor = connection.cursor()

    # Fetch all component names
    cursor.execute("SELECT id, name FROM Component")
    all_components = cursor.fetchall()

    # Create a dictionary to map names back to IDs
    name_to_id = {name: id for id, name in all_components}
    # Extract just the names for matching
    component_names = [name for _, name in all_components]

    # Match against names only
    matches = process.extract(search_query, component_names, scorer=fuzz.ratio,
                              score_cutoff=threshold, limit=5)

    results = []
    for match in matches:
        component_name = match[0]  # Now this is just the name
        match_score = match[1]
        component_id = name_to_id[component_name]

        cursor.execute("""
            SELECT c.name, c.quantity, c.description, cat.name, sl.name
            FROM Component c
            LEFT JOIN Category cat ON c.category_id = cat.id
            LEFT JOIN StorageLocation sl ON c.storage_id = sl.id
            WHERE c.id = ?
        """, (component_id,))

        details = cursor.fetchone()
        if details:
            name, quantity, description, category, storage = details
            results.append({
                "name": name,
                "match_score": match_score,
                "quantity": quantity,
                "description": description,
                "category": category,
                "storage_location": storage
            })

    connection.close()
    return tts_result(results)

def tts_result(results):
    if not results:
        return "No matching components found."

    tts_output = "Here are the matching components:\n"
    for result in results:
        tts_output += f"Component: {result['name']}, "
        tts_output += f"Quantity: {result['quantity']}, "
        tts_output += f"Category: {result['category']}, "
        tts_output += f"Storage Location: {result['storage_location']}, "
        tts_output += f"Description: {result['description']}.\n"

    return tts_output
    

def create_box_database():
    # Connect to a new/reusable box database file
    connection = sqlite3.connect("box_storage.db")
    cursor = connection.cursor()

    # Create a table for box data with columns for box_location and box_owner
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Box (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        box_location TEXT UNIQUE NOT NULL,
        box_owner TEXT NOT NULL
    )
    """)

    connection.commit()
    connection.close()
    print("Box database created successfully!")

def insert_box(box_location, box_owner):


    connection = sqlite3.connect("box_storage.db")
    cursor = connection.cursor()

    # Insert a new record into the Box table
    cursor.execute("""
        INSERT INTO Box (box_location, box_owner)
        VALUES (?, ?)
    """, (box_location, box_owner))

    connection.commit()
    connection.close()
    print(f"Box '{box_location}' inserted successfully!")


def fetch_box(user_id):
    """
    Given a user identifier, fetch the box assigned to that user.
    This function queries the box_storage.db for a record where the box_owner matches the supplied user_id.
    """
    connection = sqlite3.connect("box_storage.db")
    cursor = connection.cursor()
    cursor.execute("""
    SELECT id, box_location, box_owner
    FROM Box
    WHERE box_owner = ?
    """, (user_id,))
    result = cursor.fetchone()
    connection.close()

    if result:
        return result
       
    else:
        return f"No box found for user '{user_id}'."


def forklift_test(user_id):

    # Check for box by user
    search_term = user_id
    box_id, box_location, box_owner = fetch_box(search_term)


    ## Debug print
    print(f"Box found:\n"
                f"  ID: {box_id}\n"
                f"  Location: {box_location}\n"
                f"  Owner: {box_owner}")
    
    if(serial_test()):
        return "Test successful"
    else:
        return "Test failed"


    


def serial_test():
    # Open the serial port
    port = "COM4"
    baud_rate = 115200
    ser_test = serial.Serial(port, baud_rate)

    dict_test = {"EBoxLocation": 2, "IBoxLocation":1, "CollectBox":True}

    # Send the dictionary as a JSON string
    ser_test.write(json.dumps(dict_test).encode())   

    time.sleep(1)

    print(ser_test.read_all())



if __name__ == "__main__":
    # create_database()
    # insert_component("Arduino", 1, 3, 6, "A Microcontroller")
    # print("Database and tables created successfully!")

    # search_term = "Arduino"
    # print(fetch_component(search_term))
    # insert_component("Raspberry Pi", 1, 3, 3, "A Single Board Computer")

    # create_box_database()
    # insert_box("Shelf 2", "Albi Astolfi")

    serial_test() 
    

    

