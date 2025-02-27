from statemachine import StateMachine, State
import os
import glob
import pygame

class SpeakingState(StateMachine):
    ''' State machine transitioning between Speaking and Silent states '''

    # States
    silent_state = State("silent", initial = True)
    speaking_state = State("speaking")

    # Transitions
    switch_to_speaking = (speaking_state.to(speaking_state) | silent_state.to(speaking_state))
    switch_to_silent = (speaking_state.to(silent_state) | silent_state.to(silent_state))

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
        self.eye_images = {}
        for m in self.mood.states:
            self.base_images[f'{m.name}'] = pygame.image.load(os.path.join(self.asset_path, m.name + ".png")).convert_alpha()
            self.mouth_images[f'{m.name}_open'] = pygame.image.load(os.path.join(self.asset_path, m.name + "_mouth_open.png")).convert_alpha()
            self.mouth_images[f'{m.name}_closed'] = pygame.image.load(os.path.join(self.asset_path, m.name + "_mouth_closed.png")).convert_alpha()
            self.eye_images[f'{m.name}'] = [pygame.image.load(frame).convert_alpha() for frame in sorted(glob.glob(os.path.join(self.asset_path, m.name + "_eyes", "*.png")))]

        # Image display
        self.screen = screen
        # Resizing
        screen_w, screen_h = self.screen.get_size()
        image_w, image_h = self.base_images[self.default_mood.name].get_size() #all images are same size
        image_aspect_ratio = image_w/image_h
        new_h = screen_h
        new_w = int(new_h * image_aspect_ratio)
        self.base_images = {k: pygame.transform.scale(v, (new_w, new_h)) for k, v in self.base_images.items()}
        self.mouth_images = {k: pygame.transform.scale(v, (new_w, new_h)) for k, v in self.mouth_images.items()}
        self.eye_images = {k: [pygame.transform.scale(frame, (new_w, new_h)) for frame in v] for k, v in self.eye_images.items()}

        self.base_image = self.base_images[self.default_mood.name]
        self.mouth_image = self.mouth_images[self.default_mood.name + "_closed"]
        self.eye_image = self.eye_images[self.default_mood.name]

        self.rect = self.base_image.get_rect()
        self.rect.center = (self.screen.get_rect().center)

        # Animation
        self.clock = pygame.time.Clock()
        self.last_blink = pygame.time.get_ticks()
        self.blink_pointer = 0
        self.seconds_between_blinks = 2

        # Sound retrieval and output
        self.audio_path = os.path.join(os.getcwd(), "Visuals", audio_folder)

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

        audio = pygame.mixer.Sound(os.path.join(self.audio_path, audio_filename))
        audio.play()

    def update(self):
        current_mood = self.mood.current_state.name

        self.base_image = self.base_images[f'{current_mood}']
        self.mouth_image = self.mouth_images[f'{current_mood}_open'] if (self.is_speaking.current_state.name == "speaking") else self.mouth_images[f'{current_mood}_closed']

        # if currently playing audio, remain same
        if (pygame.mixer.get_busy() == True):
            pass
        # if queue is empty, then return to resting state
        elif (self.phrase_queue == []):
            if (self.is_speaking.current_state.name != "silent"):
                self.switchSpeaking(False) # TODO: do this after a delay
            if (current_mood != self.default_mood.name):
                self.switchMood(self.default_mood.name)
        # otherwise, ready to play next audio and change mood
        else:
            phrase = self.phrase_queue.pop(0)
            self.playAudio(phrase[0])
            self.switchSpeaking(True)
            self.switchMood(phrase[1])

        #animation logic
        self.clock.tick(20)
        current_time = pygame.time.get_ticks()
        if ((current_time - self.last_blink) > self.seconds_between_blinks*1000):
            self.blink_pointer += 1
        else:
            self.blink_pointer = 0
        if (self.blink_pointer > len(self.eye_images[f'{current_mood}']) - 1):
            self.last_blink = current_time
            self.blink_pointer = 0
        
        self.eye_image = self.eye_images[f'{current_mood}'][self.blink_pointer]

    def draw(self):
        self.screen.blit(self.base_image, self.rect.topleft)
        self.screen.blit(self.mouth_image, self.rect.topleft)
        self.screen.blit(self.eye_image, self.rect.topleft)
