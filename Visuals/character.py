from statemachine import StateMachine, State
import os
import pygame

class SpeakingState(StateMachine):
    ''' State machine transitioning between Speaking and Silent states '''

    # States
    silent_state = State("silent", initial = True)
    speaking_state = State("speaking")

    # Transitions
    switch_to_silent = speaking_state.to(silent_state)
    switch_to_speaking = silent_state.to(speaking_state)

class MoodState(StateMachine):
    ''' State machine transitioning between mood states: Positive, Negative, and Thinking '''

    # States
    positive_state = State("positive", initial = True)
    negative_state = State("negative")
    thinking_state = State("thinking")

    # Transitions
    switch_to_positive = (negative_state.to(positive_state) | thinking_state.to(positive_state))
    switch_to_negative = (positive_state.to(negative_state) | thinking_state.to(negative_state))
    switch_to_thinking = (positive_state.to(thinking_state) | negative_state.to(thinking_state))

class Character(pygame.sprite.Sprite):
    def __init__(self, screen: pygame.display):

        super().__init__()

        self.is_speaking = SpeakingState();
        self.mood = MoodState();
    
        self.character_name = "icrschan"
        self.asset_path = os.path.join(os.getcwd(), "Visuals", "assets", self.character_name)
        self.base_images = {}
        for m in self.mood.states:
            self.base_images[f'{m.name}'] = pygame.image.load(os.path.join(self.asset_path, m.name + ".png"))
        self.base_image = self.base_images["positive"]

        self.screen = screen
        self.rect = self.base_image.get_rect()
        self.rect.center = (self.screen.get_rect().center)
    
    def switchMood(self, mood: str):
        ''' Switch to given mood, out of: 'Positive', 'Negative', 'Thinking' '''

        match mood:
            case 'Positive':
                self.mood.switch_to_positive()
            case 'Negative':
                self.mood.switch_to_negative()
            case 'Thinking':
                self.mood.switch_to_thinking()
            case _:
                pass

    def update(self):
        self.base_image = self.base_images[f'{self.mood.current_state.name}']

    def draw(self):
        self.screen.blit(self.base_image, self.rect)
