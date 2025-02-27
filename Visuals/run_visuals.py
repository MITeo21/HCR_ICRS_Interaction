import pygame
import character as char

def visuals_initialisation():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    pygame.display.set_caption("Visual Interaction Endpoint")
    character = char.Character(screen, "audio")
    running = True

    return screen, character, running

def visuals_update_loop(screen, character):
    for event in pygame.event.get():
        if (event.type == pygame.QUIT):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN: # DEBUG HERE
            character.addPhrase('test.mp3', "thinking")
        if event.type == pygame.MOUSEBUTTONUP: # DEBUG HERE
            character.addPhrase('test.mp3', "negative")

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


    