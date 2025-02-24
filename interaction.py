import pygame
import threading
from queue import Queue

import Visuals.character as char
from TTS.tts_class import TTS
from LLM.session import ChatSession
from Logistics.databaseTest import create_database,insert_component,fetch_component

tts = TTS(
    api_key="sk_954ebfba7f0e81b2c0b4aad30f5471321a7ff331b7e93d94",
    voice_id="ZF6FPAbjXT4488VcRRnw",
    model_id="eleven_flash_v2_5"
)

def check_component_availability(name: str) -> str:
    '''
    Determines the availability of an item in the lab, do not consider the item's relavence to robotics.

    Args:
        name: Name of the item required

    Returns:
        str: A string containing the quantity and location of the component if found 
    '''

    return fetch_component(name)
session = ChatSession([check_component_availability])

query_queue = Queue()

def LLM_queue_handler():
    """Runs in a separate thread to collect user input without blocking the visuals."""
    while True:
        text = input("Enter query: ")
        query_queue.put(text) 

        if not query_queue.empty():
            text = query_queue.get()
            session.query(text, tts)

def visuals_initialisation():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1060,700)) # TODO: set screen size to fill
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
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     tts.request_speech("Hey kids, what is for dinner?")
    
    speech_data = tts.get_next_speech()
    if speech_data:
        speech_file, sentiment = speech_data
        character.addPhrase(speech_file, sentiment)

    character.update()

    screen.fill((40,40,150))
    character.draw()

    pygame.display.flip()

    return True

def visuals_shutdown():
    pygame.quit()

if __name__ == "__main__":
    LLM_query_thread = threading.Thread(target=LLM_queue_handler, daemon=True)
    LLM_query_thread.start()

    visuals_screen, visuals_character, visuals_running = visuals_initialisation()
    while visuals_running:
        visuals_running = visuals_update_loop(visuals_screen, visuals_character)
    visuals_shutdown()