import pygame
import character as char
import tts

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
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     tts.request_speech("Welcome to the Imperial College Robotics Society! How can I help you today?")
        if event.type == pygame.MOUSEBUTTONDOWN:
            tts.request_speech("Hey kids, what is for dinner?")
    
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
    visuals_screen, visuals_character, visuals_running = visuals_initialisation()
    while visuals_running:
        visuals_running = visuals_update_loop(visuals_screen, visuals_character)
    visuals_shutdown()


    