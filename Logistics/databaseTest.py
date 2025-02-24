import sqlite3
from rapidfuzz import fuzz, process
import serial
import time
import json

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def get_connection(self):
        return sqlite3.connect(self.db_name)

class ComponentDatabase(Database):
    def __init__(self):
        super().__init__("component_storage.db")

    def create_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
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

    def insert_component(self, name, category_id, storage_id, quantity, description):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Component (name, category_id, storage_id, quantity, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, category_id, storage_id, quantity, description))
            print(f"Component '{name}' inserted successfully!")

    def fetch_component(self, search_query, threshold=80):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM Component")
            all_components = cursor.fetchall()

            name_to_id = {name: id for id, name in all_components}
            component_names = [name for _, name in all_components]

            # Use extractOne instead of extract to get only the best match
            match = process.extractOne(search_query, component_names, scorer=fuzz.ratio,
                                score_cutoff=threshold)

            if not match:
                return None

            component_name = match[0]
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
                result = {
                    "name": name,
                    "match_score": match_score,
                    "quantity": quantity,
                    "description": description,
                    "category": category,
                    "storage_location": storage
                }
                dispenser = DispenserController()
                return dispenser.dispenser_func(result)

            return None


class BoxDatabase(Database):
    def __init__(self):
        super().__init__("box_storage.db")

    def create_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Box (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                box_location TEXT UNIQUE NOT NULL,
                box_owner TEXT NOT NULL
            )
            """)
            print("Box database created successfully!")

    def insert_box(self, box_location, box_owner):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Box (box_location, box_owner)
                VALUES (?, ?)
            """, (box_location, box_owner))
            print(f"Box '{box_location}' inserted successfully!")

    def fetch_box(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, box_location, box_owner
            FROM Box
            WHERE box_owner = ?
            """, (user_id,))
            result = cursor.fetchone()
            return result if result else f"No box found for user '{user_id}'."

class ForkliftController:
    def __init__(self, port="COM4", baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate

    def serial_test(self):
        ser_test = serial.Serial(self.port, self.baud_rate)
        dict_test = {"EBoxLocation": 2, "IBoxLocation":1, "CollectBox":True}
        ser_test.write(json.dumps(dict_test).encode())
        time.sleep(1)
        return ser_test.read_all()

    def process_user(self, user_id):
        box_db = BoxDatabase()
        box_result = box_db.fetch_box(user_id)
        
        if isinstance(box_result, tuple):
            box_id, box_location, box_owner = box_result
            print(f"Box found:\n"
                  f"  ID: {box_id}\n"
                  f"  Location: {box_location}\n"
                  f"  Owner: {box_owner}")
            
            return "Test successful" if self.serial_test() else "Test failed"
        return "Box not found"

class DispenserController:
    def __init__(self, port="COM4", baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
    def dispenser_func(self, results_arr):
        """
        A function to be called if there is a match in the components database
        """
        print(results_arr)
        return('Dispensed Component')
        
def main():
    comp_db = ComponentDatabase()
    box_db = BoxDatabase()
    forklift = ForkliftController()

    # Create databases
    comp_db.create_database()
    box_db.create_database()

    comp_db.insert_component("Arduino", 1, 3, 6, "A Microcontroller")
    print(comp_db.fetch_component("Arduin"))

    # comp_db.insert_component("Arduino", 1, 3, 6, "A Microcontroller")
    # result = forklift.process_user("Albi Astolfi")
    # print(result)


if __name__ == "__main__":
    main()
