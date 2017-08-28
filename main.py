import kivy
kivy.require('1.9.0')

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.clock import Clock
from kivy.properties import NumericProperty

import random
import time
import csv

FLASH_TIMES = 5
MIN_DELAY = 1.5
MAX_DELAY = 4

class DataHandler:

    def __init__(self):
        self.user_info = []
    
    def store_user_info(self, name, age, sex):
        self.user_info = [name, age, sex]

    def write(self, round_no, incorrect_reactions, scores):
        with open('game_report.csv', 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(self.user_info + [round_no] + scores)

class MenuScreen(Screen):

    def __init__(self, **kwargs):
	super(MenuScreen, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.name = self.ids.name_input.text
        self.age = self.ids.age_input.text
        self.sex = self.ids.sex_input.text
        self.error_label = self.ids.error_label

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
	if keycode[1] == 'escape':
            keyboard.release()
        elif keycode[1] == 'enter':
            if self.validate_input():
                print "Here"
                dataHandler.store_user_info(self.name, self.age, self.sex)
                screenManager.current = 'game'
        else:
            self.display_error()

        return True

    def validate_input(self):
        if((len(self.name) == 0) or (len(self.age) == 0) or (len(self.sex) == 0)):
            self.error_label.text = "Please enter all values"
            return False

        else:
            print self.name, self.age, self.sex
            return True

    def display_error(self):
        pass

class GameScreen(Screen):

    r = NumericProperty(0.7)
    g = NumericProperty(0.7)
    b = NumericProperty(0.7)

    def __init__(self, **kwargs):
	super(GameScreen, self).__init__(**kwargs)
        self.center_label = self.ids.center_label
        self.instruction_label = self.ids.instruction_label
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.status = 'waiting'
        self.count = 3
        self.flash_time = 0
        self.reaction_times = []
        self.flash_count = 0
        self.pressed = True
        self.flashed = False
        self.incorrect_reactions = 0
        self.round = 1

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
	if keycode[1] == 'escape':
            if self.status == 'waiting':
                screenManager.current = 'menu'
            if self.status == 'running':
                self.status = 'waiting'

        elif keycode[1] == 'enter':
            if self.status == 'waiting':
                self.instruction_label.text = ''
                Clock.schedule_once(self.countdown, 0.1)
            if self.status == 'completed':
                self.center_label.text = 'start'
                self.instruction_label.text = 'press enter'
                self.count = 3
                self.flash_count = 0
                self.incorrect_reactions = 0
                self.status = 'waiting'
                self.pressed = True
                self.flashed = False
                self.round += 1

        elif keycode[1] == 'spacebar':
            if self.status == 'running':
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
                    dataHandler.write(self.round, self.incorrect_reactions, self.reaction_times)

	return True

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
                self.center_label.text = 'done'
                self.set_color('gray')
                self.status = 'completed'
                dataHandler.write(self.round, self.incorrect_reactions, self.reaction_times)

            if self.pressed == False:
                self.reaction_times.append(9)
                print 9

            self.pressed = False

    def clear_screen(self, *args):
        self.set_color('white')

    def countdown(self, *args):
        if self.status == 'waiting':
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

class CustomTextInput(TextInput):
    pass

screenManager = ScreenManager(transition=FadeTransition())
dataHandler = DataHandler()

class ReactGameApp(App):

    def build(self):
        dataHandler = DataHandler()
        screenManager.add_widget(MenuScreen(name='menu'))
        screenManager.add_widget(GameScreen(name='game'))
        screenManager.current = 'menu'
        return screenManager

if __name__ == '__main__':
    ReactGameApp().run()
