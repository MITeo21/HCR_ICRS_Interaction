import sqlite3
from rapidfuzz import fuzz, process
import serial
import serial.tools.list_ports
import time
import json
import rospy
from move_base_msgs.msg import MoveBaseActionResult
from std_msgs.msg import String



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
                type TEXT NOT NULL,
                dispenser_loc INTEGER,
                quantity INTEGER DEFAULT 0,
                description TEXT
            )
            """)

    def insert_component(self, name, type, dispenser_loc, quantity, description):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Component (name, type, dispenser_loc, quantity, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, type, dispenser_loc, quantity, description))
            print(f"Component '{name}' inserted successfully!")

    def fetch_component(self, search_query, threshold=80):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM Component")
            all_components = cursor.fetchall()

            name_to_id = {name: id for id, name in all_components}
            component_names = [name for _, name in all_components]

            # Use extractOne instead of extract to get only the best match
            match = process.extractOne(search_query, component_names, scorer=fuzz.ratio, score_cutoff=threshold)

            if not match:
                print("Could not find the component in database")
                return None

            component_name = match[0]
            match_score = match[1]
            component_id = name_to_id[component_name]

            cursor.execute("""
                SELECT name, type, dispenser_loc, quantity, description
                FROM Component
                WHERE id = ?
            """, (component_id,))

            details = cursor.fetchone()

            if details:
                name, type, dispenser_loc, quantity, description = details
                result = {
                    "name": name,
                    "match_score": match_score,
                    "type": type,
                    "dispenser_location": dispenser_loc,
                    "quantity": quantity,
                    "description": description
                }
                print("Component Database Result", result)
                return [name, quantity, dispenser_loc]


class BoxDatabase(Database):
    def __init__(self):
        super().__init__("box_storage.db")

    def create_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Box (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shelf INTEGER NOT NULL,
                owner TEXT NOT NULL
            )
            """)
            print("Box database created successfully!")

    def insert_box(self, shelf, owner):

        with self.get_connection() as conn:

            cursor = conn.cursor()         
            cursor.execute("""
                INSERT INTO Box (shelf, owner)
                VALUES (?, ?)
            """, (shelf, owner))

            print(f"{owner}'s box inserted successfully!")


    def fetch_box(self, box_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, shelf, owner
            FROM Box
            WHERE id = ?
            """, (box_id,))
            result = cursor.fetchone()
            return result if result else f"No box found with ID '{box_id}'."


magni_status = False

class SerialController:
    def __init__(self, box_db, comp_db, baud_rate=115200):
        print("Initialising ros_node test")
        rospy.init_node('box_fetcher', anonymous=True)
        rospy.sleep(1)
        print("Finished ros stuff")
        self.port = self.detect_com_port()
        self.comp_db = comp_db
        self.box_db = box_db
        self.baud_rate = baud_rate
        self.ser = self.connect_to_serial()
        self.sub = rospy.Subscriber('/salmon/finished', String, self.statusCallback)

    def statusCallback(self, data):
        print(data.data)
        global magni_status
        if data.data=="SALMON Move finished":
            magni_status = True
            print("Magni True!")
        else:
            magni_status = False

    def moveMagni(self, idx):
        bot_pos = {"1":"box"}
        pub=rospy.Publisher('/salmon/goal_waypoint', String, queue_size=10)
        rospy.sleep(1)
        pub.publish(String(bot_pos[idx]))
        print("Sent message about")
        print(bot_pos[idx])


    def detect_com_port(self):
        """Detects the COM port that the microcontroller is connected to."""
        ports = list(serial.tools.list_ports.comports())

        for port in ports:
            # You can customize this based on known attributes of your microcontroller
            if "Espressif" in port.description or "USB" in port.description:
                print(f"Detected microcontroller on {port.device}")
                return port.device  # Return the detected port name (e.g., COM3, /dev/ttyUSB0)

        print("No microcontroller detected. Proceeding without serial connection.")
        return None  # No valid COM port found
    
    def connect_to_serial(self):
        """Tries to establish a serial connection or continues without it."""
        if self.port:
            try:
                return serial.Serial(self.port, self.baud_rate, timeout=1)
            except serial.SerialException:
                print(f"Failed to connect to {self.port}. Proceeding without serial communication.")
        return None  # Return None if connection fails


    def forklift_comm(self, ebox, ibox, collect_box):

        fork_dict = {"EBoxLocation": ebox, "IBoxLocation": ibox, "CollectBox": collect_box, "Type": "Gantry"}
        print("This is the json sent to micro:", fork_dict)

        if not self.ser:
            print("No serial connection available. Forklift command skipped.")
            return None
        else:  
            self.ser.write(json.dumps(fork_dict).encode())
            time.sleep(1)
            return self.ser.read_all()       
        
        
    
    def dispenser_comm(self, loc):
        """
        A function to be called if there is a match in the components database
        """
        if not self.ser:
            print("No serial connection available. Dispenser function skipped.")
            return None

        if loc > 24:
            return "Invalid component location"
        else:
            loc_list = [5, 10, 15, 20]
            dispenser_dict = {"Locations": loc_list, "Type": "Dispenser"}
            self.ser.write(json.dumps(dispenser_dict).encode())  # Fixed method call
            time.sleep(1)
            return self.ser.read_all()
    
    def user_component_fetch(self, comp):
        '''
        Input: component_req from the LLM. It will be a string containing the component wanted

        Return: commands to the dispenser to fetch the component
        '''

        print("Processing component request:", comp)

        comp_details = self.comp_db.fetch_component(comp)

        dispenser_loc = comp_details[2]

        if self.ser:
            print(self.dispenser_comm(dispenser_loc))
            return("Command to dispenser sent")
        else:
            print("Dispenser command skipped due to no serial connection.")
            return {"Serial connection not available. Command skipped."}
 

    def user_box_fetch(self, box_request):

        '''
        Input: 'box_request' from the user/ Interaction block
        I expect the input will be an integer containing the box number.

        Return: commands to the forklift to fetch the box
        '''

        print("Processing box request", box_request)
        self.moveMagni("1")  
        global magni_status
        while(not magni_status):
            pass
        print("Magni done command received")
        try:
            box_request = int(box_request)

            result = self.box_db.fetch_box(box_request)

            print(self.forklift_comm(result[1], result[1] , True))  
            return("Forklift command processed")
        except ValueError:
            return("Invalid box request!")

        
def populate_box(box_db):

    box_db.insert_box("1", "kpg21")
    box_db.insert_box("2", "kpg22")
    box_db.insert_box("3", "kpg23")
    
    # box_db.insert_box("2", "jk421")
    # box_db.insert_box("2","gr824")
    # box_db.insert_box("2","jjl221")
    # box_db.insert_box("2","en723")
    # box_db.insert_box("2","en723")
    # box_db.insert_box("2","dc1021")

    # box_db.insert_box("3", "bb923")
    # box_db.insert_box("3","zl4223")
    # box_db.insert_box("3","ls2624")
    # box_db.insert_box("3","bs621")
    # box_db.insert_box("3","aa5121")
    # box_db.insert_box("3","bb923")
    # box_db.insert_box("3","hk621")

def populate_dispenser(comp_db):

    comp_db.insert_component("uSD Card", "Storage", 3, 10, "MicroSD card for data storage")
    comp_db.insert_component("CAN Transceiver", "Communication", 5, 8, "Module for CAN communication")
    comp_db.insert_component("ESP32 S2 Mini", "Microcontroller", 7, 20, "Compact Wifi-enabled microcontroller")
    comp_db.insert_component("STM32 Blackpill", "Transistor", 10, 50, "STM32-based dev board")
    comp_db.insert_component("USB To UART", "Communication", 12, 5, "Adapter for serial communication over USB")

def main():
    ##Initialise rosnode
    

    ## Init Databases

    comp_db = ComponentDatabase()
    box_db = BoxDatabase()   
    comp_db.create_database()
    box_db.create_database()
    
    comms = SerialController(box_db, comp_db)
    print(comms.user_component_fetch("ESP32 S2 Mini"))

    # When initiating testing on new device, repopulate database. 
    databases_populated = False

    if not databases_populated:
        populate_box(box_db)
        populate_dispenser(comp_db)     

    # print(comms.user_box_fetch(1))
    


if __name__ == "__main__":
    main()
