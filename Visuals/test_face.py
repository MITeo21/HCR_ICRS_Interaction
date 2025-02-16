import pygame
import character

if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((800,600))
    pygame.display.set_caption("Visual Interaction Endpoint")

    character = character.Character(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0,0,0))
        character.draw()

        pygame.display.flip()

    pygame.quit()