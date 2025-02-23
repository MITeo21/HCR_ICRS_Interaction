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
    ''' State machine transitioning between mood states: positive, negative, and thinking '''

    # States
    positive_state = State("positive", initial = True)
    negative_state = State("negative")
    thinking_state = State("thinking")

    # Transitions
    switch_to_positive = (positive_state.to(positive_state) | negative_state.to(positive_state) | thinking_state.to(positive_state))
    switch_to_negative = (positive_state.to(negative_state) | negative_state.to(negative_state) | thinking_state.to(negative_state))
    switch_to_thinking = (positive_state.to(thinking_state) | negative_state.to(thinking_state) | thinking_state.to(thinking_state))

class Character(pygame.sprite.Sprite):
    def __init__(self, screen: pygame.display, audio_folder: str):

        super().__init__()

        self.character_name = "icrschan"

        # State machines
        self.is_speaking = SpeakingState();
        self.mood = MoodState();
        self.default_mood = self.mood.positive_state

        # Image retrieval
        self.asset_path = os.path.join(os.getcwd(), "Visuals", "assets", self.character_name)
        self.base_images = {}
        self.mouth_images = {}
        for m in self.mood.states:
            self.base_images[f'{m.name}'] = pygame.image.load(os.path.join(self.asset_path, m.name + ".png"))
            self.mouth_images[f'{m.name}_open'] = pygame.image.load(os.path.join(self.asset_path, m.name + "_mouth_open.png"))
            self.mouth_images[f'{m.name}_closed'] = pygame.image.load(os.path.join(self.asset_path, m.name + "_mouth_closed.png"))
        self.base_image = self.base_images[self.default_mood.name]
        self.mouth_image = self.mouth_images[self.default_mood.name + "_closed"]

        # Image display
        self.screen = screen
        self.rect = self.base_image.get_rect()
        self.rect.center = (self.screen.get_rect().center)

        # Sound retrieval and output
        self.audio_path = os.path.join(os.getcwd(), audio_folder)

        # Queues
        self.phrase_queue = []
        self.mood_queue = []
    
    def switchMood(self, mood: str):
        ''' Switch to given mood, out of: 'positive', 'negative', 'thinking' '''
        mood = mood.lower()

        match mood:
            case 'positive':
                self.mood.switch_to_positive()
            case 'negative':
                self.mood.switch_to_negative()
            case 'thinking':
                self.mood.switch_to_thinking()
            case _:
                pass
    
    def switchSpeaking(self, to_speaking: bool):
        ''' Switch between speaking (to_speaking = true) and silent (to_speaking = false)'''

        match to_speaking:
            case True:
                self.is_speaking.switch_to_speaking()
            case False:
                self.is_speaking.switch_to_silent()
            case _:
                pass
    
    def clearPhraseQueue(self):
        self.phrase_queue = []
    
    def addPhrase(self, audio_filename: str, mood: str = "none"):
        ''' Adds audio phrase file name + mood (out of 'positive', 'negative', 'thinking') tuple to queue '''

        # Add audio file and associated mood (if present) to the audio queue
        phrase_tuple = (audio_filename, mood)
        self.phrase_queue.append(phrase_tuple)

    def playAudio(self, audio_filename: str):
        ''' Plays an audio file '''

        #audio = pygame.mixer.Sound(os.path.join(self.audio_path, audio_filename))
        #audio.play()
        print("Playing audio")

    def update(self):
        current_mood = self.mood.current_state.name

        self.base_image = self.base_images[f'{current_mood}']
        self.mouth_image = self.mouth_images[f'{current_mood}_open'] if (self.is_speaking.current_state.name == "speaking") else self.mouth_images[f'{current_mood}_closed']
        
        # if queue is empty, then return to resting state
        if (self.phrase_queue == []):
            if (self.is_speaking.current_state.name != "silent"):
                self.switchSpeaking(False) # TODO: do this after a delay
            if (current_mood != self.default_mood.name):
                self.switchMood(self.default_mood.name)
        # TODO: if queue is not empty, check if currently playing audio; if so, pass
        # otherwise, ready to play next audio and change mood
        else:
            phrase = self.phrase_queue.pop(0)
            self.playAudio(phrase[0])
            self.switchSpeaking(True)
            self.switchMood(phrase[1])


    def draw(self):
        self.screen.blit(self.base_image, self.rect)
        self.screen.blit(self.mouth_image, self.rect)
