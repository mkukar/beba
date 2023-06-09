# Copyright Michael Kukar 2023

from mood import Mood
from music import Music

from dotenv import load_dotenv
import logging
import os
from langchain.llms import OpenAI
from pynput import keyboard
from threading import Thread

logger = logging.getLogger('beba')

class Controller:

    MOOD_KEY = 'm'
    PLAY_PAUSE_KEY = 'p'
    QUIT_KEY = 'q'

    llm = None
    mood = None
    music = None

    def setup(self):
        load_dotenv()
        self.setup_logger()
        self.llm = OpenAI(
            model="text-davinci-003",
            temperature=0.9,
            max_tokens=2000,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        self.mood = Mood(self.llm)
        self.music = Music(self.llm)
        self.startup_message()
        logger.info("Running...")

    def start(self):
        keyboardListener = keyboard.Listener(on_press=self.on_keypress)
        keyboardListener.start()
        keyboardListener.join()

    def setup_logger(self):
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('beba.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    def startup_message(self):
        print("BeBa")
        print("Created by Michael Kukar in 2023")
        print("Controls:")
        print("\tm - determine new mood and start relevant playlist")
        print("\tp - play/pause")
        print("\tq - quit")

    def on_keypress(self, key):
        try:
            key = key.char
        except:
            key = key.name
        logger.debug("Pressed key {0}".format(key))
        if key == self.QUIT_KEY:
            logger.info("Exiting...")
            return False
        elif key == self.MOOD_KEY:
            logger.info("Determining new mood...")
            Thread(target=self.determine_mood_and_play, args=(), name='determine_mood_and_play').start()
        elif key == self.PLAY_PAUSE_KEY:
            logger.info("Play/pause music...")
            if self.music is not None:
                Thread(target=self.music.play_pause, args=(), name='play_pause').start()

    def determine_mood_and_play(self):
        if self.mood is not None and self.music is not None:
            self.music.start_playlist_based_on_mood(self.mood.determine_mood())
            print("MOOD: {0} | PLAYLIST: {1}".format(self.mood.currentMood, self.music.playlist['name'] if self.music.playlist is not None else "None"))
