import kivy
kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.config import Config
from kivy.core.audio import SoundLoader

import random
import time
import csv
import os.path

Config.set('graphics', 'fullscreen', 'auto')
Config.write()

FLASH_TIMES = 5
MIN_DELAY = 1.5
MAX_DELAY = 4
DATA_FILE_NAME = 'game_report.csv'

class DataHandler:

    def __init__(self):
        self.user_info = []
    
    def store_user_info(self, name, age, sex):
        self.user_info = [name, age, sex]

    def write_header(self):
        if not os.path.isfile(DATA_FILE_NAME):
            with open(DATA_FILE_NAME, 'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',')
                header = ['Name', 'Age', 'Sex', 'Game Mode', 'Round', 'Incorrect Reactions']
                [header.append('Reaction Time ' + str(num)) for num in range(1, FLASH_TIMES + 1)]
                csvwriter.writerow(header)

    def write(self, gameMode, round_no, incorrect_reactions, scores):
        self.write_header()
        with open(DATA_FILE_NAME, 'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(self.user_info + [gameMode] + [round_no] + [incorrect_reactions] + scores)

class MenuScreen(Screen):

    r = NumericProperty(0.17)
    g = NumericProperty(0.24)
    b = NumericProperty(0.31)

    def __init__(self, **kwargs):
	super(MenuScreen, self).__init__(**kwargs)
        self.name_input = self.ids.name_input
        self.age_input = self.ids.age_input
        self.sex_input = self.ids.sex_input
        self.error_label = self.ids.error_label

    def handle_event(self, keycode):
        if keycode[1] == 'escape':
            exit(1)

        if keycode[1] == 'enter':
            if self.validate_input():
                dataHandler.store_user_info(self.name_input.text, self.age_input.text, self.sex_input.text.upper())
                screenManager.current = 'game'

        if keycode[1] == 'f2':
            global gameMode
            if gameMode == 'lambda':
                gameMode = 'gamma'
                self.r, self.g, self.b = 0.20, 0.29, 0.37
            elif gameMode == 'gamma':
                gameMode = 'lambda'
                self.r, self.g, self.b = 0.17, 0.24, 0.31

        return True

    def validate_input(self):
        if((len(self.name_input.text) == 0) or (len(self.age_input.text) == 0) or (len(self.sex_input.text) == 0)):
            self.display_error('incomplete')
            return False

        elif not self.age_input.text.isdigit():
            self.display_error('age')
            return False

        elif ((len(self.sex_input.text) != 1) or
                (not (('M' in self.sex_input.text.upper()) or ('F' in self.sex_input.text.upper())))):
            self.display_error('sex')
            return False
        else:
            print self.name_input.text, self.age_input.text, self.sex_input.text
            return True

    def display_error(self, code):
        if code == 'incomplete':
            self.error_label.text = "Please enter all values"
        elif code == 'age':
            self.error_label.text = "Age should be a numeric value"
        elif code == 'sex':
            self.error_label.text = "Sex should either be M or F"

class GameScreen(Screen):

    r = NumericProperty(0.7)
    g = NumericProperty(0.7)
    b = NumericProperty(0.7)

    def __init__(self, **kwargs):
	super(GameScreen, self).__init__(**kwargs)
        self.center_label = self.ids.center_label
        self.round_label = self.ids.round_label
        self.instruction_label = self.ids.instruction_label
        self.mode_label = self.ids.mode_label
        self.round = 1
        self.reset_game()
        self.mode_visible = False

    def reset_game(self):
        self.status = 'waiting'
        self.count = 3
        self.flash_time = 0
        self.reaction_times = []
        self.flash_count = 0
        self.pressed = True
        self.flashed = False
        self.incorrect_reactions = 0
        self.center_label.text = 'start'
        self.instruction_label.text = 'press enter'
        self.round_label.text = "round " + str(self.round)

    def handle_event(self, keycode):
	if keycode[1] == 'escape':
            if self.status == 'waiting':
                self.round = 1
                self.reset_game()
                screenManager.current = 'menu'
            if self.status == 'running':
                self.reset_game()
            if self.status == 'completed':
                self.round = 1
                self.reset_game()
                screenManager.current = 'menu'

        elif keycode[1] == 'enter':
            if self.status == 'waiting':
                Clock.schedule_once(self.countdown, 0.1)
            if self.status == 'completed':
                self.round += 1
                self.reset_game()

        elif keycode[1] == 'spacebar':
            if self.status == 'running':
                global gameMode
                self.pressed = True

                if self.flashed:
                    self.reaction_times.append(time.clock() - self.flash_time)
                    print self.reaction_times[-1]
                else:
                    self.incorrect_reactions += 1

                self.flashed = False

                if self.flash_count == FLASH_TIMES:
                    self.center_label.text = 'done'
                    self.instruction_label.text = 'press enter'
                    self.set_color('gray')
                    self.status = 'completed'
                    dataHandler.write(gameMode, self.round, self.incorrect_reactions, self.reaction_times)
                else:
                    if gameMode == 'gamma':
                        if random.randint(0, 2) == 2:
                            beep.play()

        elif keycode[1] == 'f2':
            if self.status == 'waiting' or self.status == 'completed':
                self.show_mode()

	return True
    
    def show_mode(self, *args):
        global gameMode
        if self.mode_visible:
            self.mode_label.text = ''
            self.mode_visible = False
        else:
            self.mode_label.text = gameMode
            self.mode_visible = True
            Clock.schedule_once(self.show_mode, 0.5)
        

    def flash(self, *args):
        if self.status == 'running':
            self.set_color('red')
            self.flash_time = time.clock()

            self.flash_count += 1
            self.flashed = True

            if self.flash_count <= FLASH_TIMES:
                Clock.schedule_once(self.clear_screen, 0.1)
                Clock.schedule_once(self.flash, self.get_next_update())
            elif self.flash_count > FLASH_TIMES:
                global gameMode
                self.center_label.text = 'done'
                self.set_color('gray')
                self.status = 'completed'
                dataHandler.write(self.gameMode, self.round, self.incorrect_reactions, self.reaction_times)

            if self.pressed == False:
                self.reaction_times.append(9)
                print 9

            self.pressed = False

    def clear_screen(self, *args):
        self.set_color('white')

    def countdown(self, *args):
        if self.status == 'waiting':
            self.instruction_label.text = ''
            self.round_label.text = ''
            self.center_label.text = str(self.count)
            self.count -= 1

            if self.count == -1:
                self.set_color('white')
                self.center_label.text = ''
                self.status = 'running'
                Clock.schedule_once(self.flash, self.get_next_update())
            else:
                Clock.schedule_once(self.countdown, 1)

    def get_next_update(self):
        return (MIN_DELAY + (MAX_DELAY-MIN_DELAY)*random.randint(1, 1001)/1000)

    def set_color(self, color):
        if color == 'red':
            self.r, self.g, self.b = 1, 0, 0
        elif color == 'green':
            self.r, self.g, self.b = 0, 1, 0
        elif color == 'blue':
            self.r, self.g, self.b = 0, 0, 1
        elif color == 'white':
            self.r, self.g, self.b = 1, 1, 1
        elif color == 'gray':
            self.r, self.g, self.b = 0.7, 0.7, 0.7

    def set_random_color(self):
        color = random.randint(0, 3)
        if color == 0:
            self.set_color('red')
        elif color == 1:
            self.set_color('green')
        elif color == 2:
            self.set_color('blue')

screenManager = ScreenManager(transition=FadeTransition())
dataHandler = DataHandler()
beep = SoundLoader.load('assets/beep.wav')
gameMode = 'lambda'

class ReactGameApp(App):

    def build(self):
        dataHandler = DataHandler()

        screenManager.add_widget(MenuScreen(name='menu'))
        screenManager.add_widget(GameScreen(name='game'))

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self.root)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        
        return screenManager

    def _keyboard_closed(self):
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        screenManager.current_screen.handle_event(keycode)
        return True
            

if __name__ == '__main__':
    ReactGameApp().run()
