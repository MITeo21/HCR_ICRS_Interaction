import sqlite3
from rapidfuzz import fuzz, process
import serial
import time
import json
import argparse

# Only import ROS packages when needed.
try:
    import rospy
    from std_msgs.msg import String, Int64
except ImportError:
    pass

#############################
# Database Classes
#############################

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
                dispenser = SerialController(None)  # Not using box_db in this context.
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
            
            cursor.execute("""
                INSERT INTO Box (box_location, box_owner)
                VALUES (?, ?)
            """, (box_location, box_owner))
            print(f"Box '{box_location}' inserted successfully!")

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

#############################
# Serial Communication Class
#############################

class SerialController:
    def __init__(self, box_db, port="COM4", baud_rate=115200):
        self.port = port
        self.box_db = box_db
        self.baud_rate = baud_rate
        self.ser = serial.Serial(self.port, self.baud_rate)

    def forklift_comm(self, ebox, ibox, collect_box):
        fork_dict = {"EBoxLocation": ebox, "IBoxLocation": ibox, "CollectBox": collect_box}
        self.ser.write(json.dumps(fork_dict).encode())
        print("sent", fork_dict)
        while(1):
            print(self.ser.read_all())
        return

    def dispenser_func(self, result):
        dispenser_list = [12, 5, 7, 8]
        self.ser.write(json.dumps(dispenser_list).encode())
        time.sleep(1)
        return self.ser.read_all()

    def user_box_fetch(self, box_request, shelf_update_callback=None):
        """
        Fetches a box from the BoxDatabase.
        If a valid box is found, it extracts the shelf number (using box_location).
        In ROS mode (when a callback is provided), it calls the callback to publish the shelf number
        and waits for the SLAM system to send "arrived" before issuing the forklift command.
        In non-ROS mode, the forklift command is issued immediately.
        """
        if not isinstance(box_request, int):
            return "You have entered an invalid box number"
        else:
            result = self.box_db.fetch_box(box_request)
            if isinstance(result, tuple):
                # Assume result is (id, box_location, box_owner)
                shelf_num = result[1]
                if shelf_update_callback:
                    # In ROS mode, publish the shelf number and do not immediately send the forklift command.
                    shelf_update_callback(shelf_num)
                    return {"Status": "Waiting for SLAM status before sending forklift command"}
                else:
                    # In test (no ROS) mode, send the forklift command immediately.
                    forklift_result = self.forklift_comm(1, 1, True)
                    return {"Result": forklift_result}
            else:
                return result

#############################
# ROS Shelf Handler Class
#############################

class ROSHandler:
    """
    In ROS mode, this class subscribes to the "slam_status" topic and holds the shelf number
    (published when a positive box fetch occurs). Once an "arrived" message is received,
    it issues the forklift command.
    """
    def __init__(self, serial_controller):
        self.serial_controller = serial_controller
        self.shelf_num = None
        self.shelf_pub = rospy.Publisher('shelf_num', Int64, queue_size=10)
        self.slam_sub = rospy.Subscriber('slam_status', String, self.slam_callback)

    def update_shelf(self, shelf_num):
        self.shelf_num = shelf_num
        self.shelf_pub.publish(json.dumps(self.shelf_data))
        rospy.loginfo("Published shelf number: %s", shelf_num)

    def slam_callback(self, msg):
        rospy.loginfo("Received SLAM message: %s", msg.data)
        if msg.data == "arrived" and self.shelf_num is not None:
            try:
                ebox = int(self.shelf_num)
            except ValueError:
                ebox = 0
            # Issue the forklift command now that SLAM confirms arrival.
            result = self.serial_controller.forklift_comm(ebox, 1, True)
            rospy.loginfo("Forklift command sent. Result: %s", result)
            self.shelf_num = None

#############################
# Main Entry Point
#############################

def main():
    parser = argparse.ArgumentParser(description="Database Node with optional ROS functionality (default: ROS enabled)")
    # Add a flag to disable ROS functionality.
    parser.add_argument("--noros", action="store_true", help="Disable ROS functionality")
    args = parser.parse_args()
    use_ros = not args.noros  # By default, use_ros is True unless --noros is specified.

    # Initialize databases and create tables.
    comp_db = ComponentDatabase()
    box_db = BoxDatabase()
    comp_db.create_database()
    box_db.create_database()

    serial_controller = SerialController(box_db)

    box_db.insert_box(2, "kevin")

    ## TODO: Change this code when integrating with LLM Wrapper. 

    if use_ros:
        rospy.init_node('database_ros_node', anonymous=True)
        ros_handler = ROSHandler(serial_controller)
        rospy.loginfo("ROS node started.")

        try:
            box_input = input("Enter a box ID to fetch: ")
            box_id = int(box_input)
        except ValueError:
            print("Invalid input. Please enter an integer box ID.")
            return

        # In ROS mode, call user_box_fetch with the ROS shelf update callback.
        result = serial_controller.user_box_fetch(box_id, shelf_update_callback=ros_handler.update_shelf)
        rospy.loginfo("Result: %s", result)
        rospy.spin()
    else:   
        print("ROS functionality is disabled. Running in non-ROS mode.")
        try:
            box_input = input("Enter a box ID to fetch: ")
            box_id = int(box_input)
        except ValueError:
            print("Invalid input. Please enter an integer box ID.")
            return
        result = serial_controller.user_box_fetch(box_id)
        print("Result:", result)

if __name__ == "__main__":
    main()
