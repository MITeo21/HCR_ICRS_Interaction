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
                dispenser = SerialController()
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
            cursor.execute("SELECT * FROM Box WHERE box_location = ?", (box_location,))
            existing_box = cursor.fetchone()

            if existing_box:

                print(f"Box location '{box_location}' already exists!")
                return
            
            # Insert new box if it doesn't exist
            cursor.execute("""
                INSERT INTO Box (box_location, box_owner)
                VALUES (?, ?)
            """, (box_location, box_owner))

            print(f"Box '{box_location}' inserted successfully!")


    # def fetch_box(self, user_id):
    #     with self.get_connection() as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("""
    #         SELECT id, box_location, box_owner
    #         FROM Box
    #         WHERE box_owner = ?
    #         """, (user_id,))
    #         result = cursor.fetchone()
    #         return result if result else f"No box found for user '{user_id}'."

    def fetch_box(self, box_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, box_location, box_owner
            FROM Box
            WHERE id = ?
            """, (box_id,))
            result = cursor.fetchone()
            return result if result else f"No box found with ID '{box_id}'."

class SerialController:
    def __init__(self, box_db, port="COM4", baud_rate=115200):
        self.port = port
        self.box_db = box_db
        self.baud_rate = baud_rate
        self.ser = serial.Serial(self.port, self.baud_rate)

    def forklift_comm(self, ebox, ibox, collect_box):
        fork_dict = {"EBoxLocation": ebox, "IBoxLocation": ibox, "CollectBox": collect_box} ## Internal Box Location is redundant so get rid of later
        self.ser.write(json.dumps(fork_dict).encode())
        time.sleep(1)
        return self.ser.read_all()
    
    def dispenser_func(self):
        """
        A function to be called if there is a match in the components database
        """
        dispenser_list = [12, 5, 7, 8]
        self.ser_write(json.dumps(dispenser_list).encode())
        time.sleep(1)
        return self.ser.read.all()

    def user_box_fetch(self, box_request):

        '''
        Input: 'box_request' from the user/ Interaction block
        I expect the input will be an integer containing the box number.

        Return: commands to the forklift to fetch the box
        '''
        # Fetch the box location from the database
        if box_request != int(box_request):
            ## Code to feed back to Interaction 
            return("You have entered an invalid box number")
        else:
             result = self.box_db.fetch_box(box_request)

             ## Dummy forklift call, to be changed with actual shelf numbers etc
             print(self.forklift_comm(int(result[1]), 2, True)) ## Result[1] is external shelf number and comes from the database, ebox arbitrary.  
             return{"Command sent to forklift successfully"}
        
def main():


    ## Init Databases

    comp_db = ComponentDatabase()
    box_db = BoxDatabase()   
    comp_db.create_database()
    box_db.create_database()

    comms = SerialController(box_db)


    ## Need LLM wrappers for this code:


    comp_db.insert_component("Arduino", 1, 3, 6, "A Microcontroller")
    # print(comp_db.fetch_component("Arduin"))

    box_db.insert_box("2", "User1")
    print(comms.user_box_fetch(1))


if __name__ == "__main__":
    main()
