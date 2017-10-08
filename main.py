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

FLASH_TIMES = 30
MIN_DELAY = 1.5
MAX_DELAY = 4
BEEP_PERCENTAGE = 50
DATA_FILE_NAME = 'game_report.csv'
HEADING = 'Task'
BEEP_FILE = 'beep.csv'

with open('config.txt', 'rb') as configFile:
    configuration = configFile.readlines()

    for config in configuration:
        config = config.strip()
        if 'FLASH_TIMES' in config:
            FLASH_TIMES = int(config.split('= ')[1])
        elif 'MIN_DELAY' in config:
            MIN_DELAY = float(config.split('= ')[1])
        elif 'MAX_DELAY' in config:
            MAX_DELAY = float(config.split('= ')[1])
        elif 'BEEP_PERCENTAGE' in config:
            BEEP_PERCENTAGE = float(config.split('= ')[1])
        elif 'DATA_FILE_NAME' in config:
            DATA_FILE_NAME = config.split('= ')[1]
        elif 'HEADING' in config:
            HEADING = config.split('= ')[1]
        elif 'BEEP_FILE' in config:
            BEEP_FILE = config.split('= ')[1]

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
                [header.append('T' + str(num)) for num in range(1, FLASH_TIMES + 1)]
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
        self.mode_visible = False
        self.mode_label = self.ids.mode_label
        Clock.schedule_once(self.set_focus, 0.5)

    def handle_event(self, keycode):
        global gameMode
        if keycode[1] == 'escape':
            exit(1)

        elif keycode[1] == 'enter':
            if self.validate_input():
                dataHandler.store_user_info(self.name_input.text, self.age_input.text, self.sex_input.text.upper())
                screenManager.current = 'game'

        elif keycode[1] == 'f1':    # normal mode with no beeps
            gameMode = 'gamma'
            self.show_mode()

        elif keycode[1] == 'f2':    # distraction mode with beeps randomly on keypress
            gameMode = 'lambda'
            self.show_mode()
        
        '''
        elif keycode[1] == 'f3':    # normal mode with beeps at every keypress
            gameMode = 'gamma'
            self.show_mode()

        elif keycode[1] == 'f4':    # distraction mode with randomly missing beeps at keypress
            gameMode = 'lambda'
            self.show_mode()

        elif keycode[1] == 'f5':    # distraction mode with blank screen at random places
            gameMode = 'eta'
            self.show_mode()
        '''

        return True

    def validate_input(self):
        if((len(self.name_input.text) == 0) or (len(self.age_input.text) == 0) or (len(self.sex_input.text) == 0)):
            self.display_error('incomplete')
            return False

        elif not self.age_input.text.isdigit():
            self.display_error('age')
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
            self.error_label.text = "Sex should not be left empty"

    def set_focus(self, *args):
        self.name_input.focus = True

    def show_mode(self, *args):
        global gameMode
        if self.mode_visible:
            self.mode_label.text = ''
            self.mode_visible = False
        else:
            self.mode_label.text = gameMode
            self.mode_visible = True
            Clock.schedule_once(self.show_mode, 0.5)

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
        self.noBeep = False

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
                    self.reaction_times.append("{0:.5f}".format(time.clock() - self.flash_time))
                    print self.reaction_times[-1]
                elif not self.noBeep:
                    self.incorrect_reactions += 1

                self.flashed = False

                if self.flash_count == FLASH_TIMES:
                    self.center_label.text = 'done'
                    self.instruction_label.text = 'press enter'
                    self.set_color('gray')
                    self.status = 'completed'
                    dataHandler.write(gameMode, self.round, self.incorrect_reactions, self.reaction_times)
                    
                if gameMode == 'alpha':
                    pass

                elif gameMode == 'beta':
                    if random.randint(1, 100/BEEP_PERCENTAGE) == 1:
                        beep.play()

                elif gameMode == 'gamma':
                    beep.play()

                elif gameMode == 'lambda':
                    if (random.randint(1, 100/BEEP_PERCENTAGE) != 1) or self.noBeep or (self.flash_count == FLASH_TIMES):
                        beep.play()
                        self.noBeep = False
                    else:
                        self.noBeep = True

                elif gameMode == 'eta':
                    pass

        elif keycode[1] == 'f12':
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
            self.set_color('dark-grey')
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
                self.reaction_times.append(9)
                dataHandler.write(gameMode, self.round, self.incorrect_reactions, self.reaction_times)

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
        elif color == 'dark-grey':
            self.r, self.g, self.b = 0.22, 0.28, 0.31

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
beep = SoundLoader.load('assets/' + BEEP_FILE)
gameMode = 'alpha'

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
