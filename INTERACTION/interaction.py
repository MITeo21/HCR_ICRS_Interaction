import pygame
import threading
from queue import Queue
#from speech_to_text.real_time_transcription import SpeechToText
from RealtimeSTT import AudioToTextRecorder
# from mocks.text_to_text import InputServer as AudioToTextRecorder
import sounddevice  # black magic to make this run on linux


import Visuals.character as char
from TTS.tts_class import TTS
# from mocks.text_to_text import TTT as TTS
from LLM.session import ChatSession
from Logistics.databaseTest import ComponentDatabase, SerialController, BoxDatabase

database = ComponentDatabase()
box_db = BoxDatabase()
comp_db = ComponentDatabase()
serialController = SerialController(box_db, comp_db)

tts = TTS(
    api_key="sk_9abae8a150c2a3885b6947c895539a1ff5c5e519020f1644",
    voice_id="ZF6FPAbjXT4488VcRRnw",
    model_id="eleven_flash_v2_5"
)

# Determines the location of the requested box in the lab and uses its forklift to fetch it and brings it to the user at their desk once fetched.
def requestBox(box_id : int) -> int:
    '''
    Fetches a specific box from the shelf in the robotics lab using its forklift.

    - The function should only be called when a user requests a "box" with a specific **box number**.
    - It does not handle requests for general components or availability.
    - Uses the forklift to fetch the box and brings it to the user at their desk.

    Args:
    box_ID : The box number the user wants to fetch

    Returns:
    int : The shelf number of the box the user wants to fetch
    '''

    print("Request Box LLM Handler")

    comms = SerialController

    return comms.user_box_fetch(box_id)

# Determines the location of a component in the lab, do not consider the item's relavence to robotics.
def requestComponent(comp_name: str) -> int:
    '''
    Retrieves the exact location of a **component** inside the robotics lab.

    - Should only be called when a user is asking for a specific **component name**.
    - Does **not** handle box-related queries.
    - Returns the dispenser location of the requested component.

    Args:
    comp_name: The component the user wants to fetch

    Returns:
    int : The location of the component on the dispenser
    '''

    comms = SerialController
    return comms.user_component_fetch(comp_name)

# Determines the availability of an item in the lab, do not consider the item's relavence to robotics.
def check_component_availability(name: str) -> str:
    '''
    Checks whether a specific component is available in the robotics lab.

    - Only use this function when the user wants to know the **availability** of a component.
    - Do **not** use this function for retrieving or fetching items.
    - Returns a string indicating the quantity and storage location.

    Args:
        name: Name of the item required

    Returns:
        str: A string containing the quantity and location of the component if found 
    '''

    return database.fetch_component(name)

session = ChatSession([check_component_availability, requestBox, requestComponent], use_tts=True)

query_queue = Queue()
def LLM_queue_handler(character):
    """Runs in a separate thread to collect user input without blocking the visuals."""
    while True:

        if not query_queue.empty():
            character.switchMood('thinking', True)
            text = query_queue.get()
            print(f"Query Received: '{text}'")
            session.query(text, tts)

def visuals_initialisation():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((0,0), pygame.RESIZABLE)
    pygame.display.set_caption("Visual Interaction with TTS")
    character = char.Character(screen, "audio")
    running = True

    return screen, character, running


def visuals_update_loop(screen, character):
    for event in pygame.event.get():
        if (event.type == pygame.QUIT):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            tts.request_speech("Welcome to the Imperial College Robotics Society! How can I help you today?")
            character.switchMood('thinking', True)
        if event.type == pygame.KEYDOWN:
            pass
    
    (speech_data, text_data) = tts.get_next_speech()
    if speech_data:
        speech_file, sentiment = speech_data
        character.addPhrase(speech_file, text_data, sentiment)

    character.update()

    screen.fill((40,40,150))
    character.draw()

    pygame.display.flip()

    return True


def visuals_shutdown():
    pygame.quit()

def process_text(text):
    query_queue.put(text)

def STT():
    recorder = AudioToTextRecorder(
        wakeword_backend="oww",
        wake_words_sensitivity=0.2,
        openwakeword_model_paths="eye_riss.onnx",
        wake_word_buffer_duration=1,
        device="cpu",
        no_log_file=True,
        realtime_processing_pause=0.3,
        min_gap_between_recordings=10,
        min_length_of_recording=3
    )

    while True:
        recorder.text(process_text)

if __name__ == "__main__":
    visuals_screen, visuals_character, visuals_running = visuals_initialisation()
    
    LLM_query_thread = threading.Thread(
        target=LLM_queue_handler, args=(visuals_character,), daemon=True
    )
    LLM_query_thread.start()

    STT_thread = threading.Thread(target=STT, daemon=True)
    STT_thread.start()

    while visuals_running:
        visuals_running = visuals_update_loop(visuals_screen, visuals_character)
    visuals_shutdown()
    quit()
