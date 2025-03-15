import pygame
import threading
from queue import Queue
import time
# from speech_to_text.real_time_transcription import SpeechToText

import Visuals.character as char
from TTS.tts_class import TTS
from LLM.session import ChatSession
from Logistics.databaseTest import ComponentDatabase, SerialController, BoxDatabase

database = ComponentDatabase()
box_db = BoxDatabase()
comp_db = ComponentDatabase()
serialController = SerialController(box_db, comp_db)

tts = TTS(
    api_key="sk_9abae8a150c2a3885b6947c895539a1ff5c5e519020f1644",
    # api_key="sk_954ebfba7f0e81b2c0b4aad30f5471321a7ff331b7e93d94",
    # voice_id="ZF6FPAbjXT4488VcRRnw",
    voice_id="ZF6FPAbjXT4488VcRRnw",
    model_id="eleven_flash_v2_5"
)

def requestBox(box_id : int) -> int:

    '''
    Checks where the box is in the lab

    Args:
    box_ID : The box number the user wants to fetch

    Returns:
    int : The shelf number of the box the user wants to fetch
    '''

    print("Request Box LLM Handler")

    comms = SerialController

    return comms.user_box_fetch(box_id)

def requestComponent(comp_name: str) -> int:
    '''
    Checks where the component is in the dispenser

    Args:
    comp_name: The component the user wants to fetch

    Returns:
    int : The location of the component on the dispenser
    '''

    comms = SerialController
    return comms.user_component_fetch(comp_name)

def check_component_availability(name: str) -> str:
    '''
    Determines the availability of an item in the lab, do not consider the item's relavence to robotics.

    Args:
        name: Name of the item required

    Returns:
        str: A string containing the quantity and location of the component if found 
    '''

    return database.fetch_component(name)

session = ChatSession([check_component_availability, requestBox, requestComponent])

query_queue = Queue()
print("hello b!")
# speechRec = SpeechToText(mic_name="MacBook Pro Microphone")
# speechRec.run()
# print("hello s!")
def LLM_queue_handler(character):
    """Runs in a separate thread to collect user input without blocking the visuals."""
    while True:
        print(f"qsize: {query_queue.qsize()}")
        # text = input("Enter query: ")
        text = "Hi Iris, can I please have an ESP32"
        print(text)
        query_queue.put(text)
        print("flag")
        print(f"qsize: {query_queue.qsize()}")
        query_queue.put_nowait("a")

        try:
            query_queue.put_nowait("b")
        except Queue.Full:
            print ("Queue is full.")

        if not query_queue.empty():
            character.switchMood('thinking', True)
            text = query_queue.get()
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
            # if event.key == pygame.K_SPACE:  # Press Space to toggle Speech Recognition
            #     speechRec.toggle_recording()
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     tts.request_speech("Hey kids, what is for dinner?")
    
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


if __name__ == "__main__":
    visuals_screen, visuals_character, visuals_running = visuals_initialisation()
    
    LLM_query_thread = threading.Thread(
        target=LLM_queue_handler, args=(visuals_character,), daemon=True
    )
    LLM_query_thread.start()

    # STT_thread = threading.Thread(target=speechRec.run, args=(), daemon=True)
    # STT_thread.start()

    while visuals_running:
        visuals_running = visuals_update_loop(visuals_screen, visuals_character)
    visuals_shutdown()
