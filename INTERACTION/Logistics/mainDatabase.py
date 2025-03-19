import sqlite3
from rapidfuzz import fuzz, process
import serial
import serial.tools.list_ports
import time
import json
from move_base_msgs.msg import MoveBaseActionResult
from std_msgs.msg import String
import socket



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
    def __init__(self, box_db: BoxDatabase, comp_db: ComponentDatabase, baud_rate=115200):
        print("Initialising ros_node test")
        self.host = '10.42.0.1'
        self.tcp_port = 10000
        print(f"SCont: URI set to {self.host}:{self.tcp_port}")

        self.port = self.detect_com_port()
        self.comp_db = comp_db
        self.box_db = box_db
        self.baud_rate = baud_rate
        self.ser = self.connect_to_serial()
        
        self.bot_pos = {
            2: "box"
        }
        self.connectToROS()


    def connectToROS(self):
        print(f"SCont: Connecting to {self.host}:{self.tcp_port}")
        try:
            self.ros_socket = socket.create_connection(
                (self.host, self.tcp_port), timeout=None
            )
            return 0
        except Exception as e:
            self.ros_socket = None
            print("SCont - err: failed to connect to ROS Impostor Server: {e}")
            return 1

    def ROSCheck(self):
        """Make it check itself before it wrecks itself"""
        if self.ros_socket is None:
            if self.connectToROS() == 1:
                print(f"SCont - err: cannot send command to RIS")
                return False
        return True


    def nyomnyom(self, new_pos):
        if not self.ROSCheck():
            return 1

        try:
            self.ros_socket.sendall(new_pos.encode())
            
        except KeyboardInterrupt:
            self.ros_socket.close()
            print(f"SCont: Peacefully disconnected from ROS server")
        except Exception as e:
            self.ros_socket.close()
            print(f"SCont - err: {e}")


    def receiveStatus(self):
        if not self.ROSCheck():
            return None

        try:
            data = self.ros_socket.recv(1024).decode('utf-8').strip()
            print("Forklift ready command received")
            print(data)
            return data
        except KeyboardInterrupt:
            self.ros_socket.close()
            print(f"SCont: Peacefully disconnected from ROS server")
        except Exception as e:
            self.ros_socket.close()
            print(f"SCont - Error: {e}")


    def detect_com_port(self):
        """Detects the COM port that the microcontroller is connected to."""
        ports = list(serial.tools.list_ports.comports())

        for port in ports:
            # You can customize this based on known attributes of your microcontroller
            if "Espressif" in port.description or "USB" in port.description:
                print(f"Detected microcontroller on {port.device} - {port.description}")
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
            dispenser_dict = {"Locations": [loc], "Type": "Dispenser"}
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

        if comp_details is None:
            print(f"SCont - err: {comp} does not exist in DB")
            return

        dispenser_loc = comp_details[2]

        if self.ser:
            print(self.dispenser_comm(dispenser_loc))
            reply = f"you can pick up {comp_details} from the dispenser now!"
            return reply
        else:
            print("Dispenser command skipped due to no serial connection.")
            return "Serial connection not available. Command skipped."
 

    def user_box_fetch(self, box_request):

        '''
        Input: 'box_request' from the user/ Interaction block
        I expect the input will be an integer containing the box number.

        Return: commands to the forklift to fetch the box
        '''

        print("Processing box request", box_request)
        if self.nyomnyom(self.bot_pos[int(box_request)]) == 1:
            return  # ROS Server isn't connected

        status = self.receiveStatus() 
        while status != "done":
            # TODO: check that it returns sth that isn't None, if it is connected, but not done
            if status is None:
                print(f"SCont::ubf-err: failed to connect, terminating forklift command")
                return

            time.sleep(0.2)
            status = self.receiveStatus() 

        print(f"SCont::ubf: forklift done")
        
        try:
            box_request = int(box_request)

            result = self.box_db.fetch_box(box_request)

            print(self.forklift_comm(result[1], 3 , True))  
            #blocking code for forklift
            for i in range(0, 20):
                time.sleep(5)
                self.nyomnyom(f"dummy {i}")

            self.nyomnyom("FComplete")
            return "Forklift command processed"
        except ValueError:
            return "Invalid box request!"

        
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

def populate_dispenser(comp_db: ComponentDatabase):
    comp_db.insert_component("micro SD Card", "Storage", 2, 10, "MicroSD card for data storage")
    comp_db.insert_component("CAN Transceiver", "Communication", 5, 8, "Module for CAN communication")
    comp_db.insert_component("ESP32", "Microcontroller", 0, 20, "Compact Wifi-enabled microcontroller")
    comp_db.insert_component("STM32", "Transistor", 1, 50, "STM32-based dev board")
    comp_db.insert_component("USB to UART", "Communication", 3, 5, "Adapter for serial communication over USB")

def init_databases():
    # Create Databases
    comp_db = ComponentDatabase()
    box_db = BoxDatabase()   
    comp_db.create_database()
    box_db.create_database()
    
    comms = SerialController(box_db, comp_db)
    # comms.user_box_fetch(comms.bot_pos["1"])
    
    # if ESP32 not in component table, assume unpopulated
    if comms.user_component_fetch("ESP32") is None:
        populate_box(box_db)
        populate_dispenser(comp_db)    


if __name__ == "__main__":
    init_databases()
