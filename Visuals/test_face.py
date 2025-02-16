import pygame
import character

if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((1920,1200))
    pygame.display.set_caption("Visual Interaction Endpoint")

    character = character.Character(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                character.switchMood("Negative")
                print(character.mood.current_state.name)

        character.update()

        screen.fill((40,40,150))
        character.draw()

        pygame.display.flip()

    pygame.quit()