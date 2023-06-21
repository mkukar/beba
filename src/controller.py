# Copyright Michael Kukar 2023

from dotenv import load_dotenv
import logging
import os
from langchain.llms import OpenAI
from sshkeyboard import listen_keyboard, stop_listening
from threading import Thread, Timer, Lock

from mood import Mood
from music import Music
if os.name != 'nt': # don't import if windows
    from epaper_display import EPaperDisplay

logger = logging.getLogger('beba')

class Controller:

    CHANGE_MOOD_KEY = 'm'
    PLAY_PAUSE_KEY = 'p'
    QUIT_KEY = 'q'
    NEXT_KEY = 'n'
    PREV_KEY = 'p'
    INFO_KEY = 'i'

    llm = None
    mood = None
    music = None

    screen_enabled = False
    screen = None

    mood_lock = Lock()
    display_lock = Lock()

    def setup(self):
        load_dotenv()
        self.setup_logger()
        self.load_key_configuration()
        logger.info("Setting up...")
        self.llm = OpenAI(
            model="text-davinci-003",
            temperature=0.9,
            max_tokens=2000,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        self.mood = Mood(self.llm)
        self.music = Music(self.llm)
        self.startup_message()
        if os.getenv('RASPBERRY_PI_SCREEN') is not None and os.getenv('RASPBERRY_PI_SCREEN').lower() == "true":
            self.screen = EPaperDisplay(self.llm)
            self.screen_enabled = True
        logger.info("Running...")

    def load_key_configuration(self):
        self.CHANGE_MOOD_KEY = os.getenv('CHANGE_MOOD_KEY').strip() if os.getenv('CHANGE_MOOD_KEY') is not None else self.CHANGE_MOOD_KEY
        self.PLAY_PAUSE_KEY = os.getenv('PLAY_PAUSE_KEY').strip() if os.getenv('PLAY_PAUSE_KEY') is not None else self.PLAY_PAUSE_KEY
        self.QUIT_KEY = os.getenv('QUIT_KEY').strip() if os.getenv('QUIT_KEY') is not None else self.QUIT_KEY
        self.NEXT_KEY = os.getenv('NEXT_KEY').strip() if os.getenv('NEXT_KEY') is not None else self.NEXT_KEY
        self.PREV_KEY = os.getenv('PREV_KEY').strip() if os.getenv('PREV_KEY') is not None else self.PREV_KEY
        self.INFO_KEY = os.getenv('INFO_KEY').strip() if os.getenv('INFO_KEY') is not None else self.INFO_KEY

    def start(self):
        keyboard_listener = Thread(target=listen_keyboard, args=(self.on_keypress,))
        keyboard_listener.start()
        self.start_mood_timer()
        self.display_refresh_timer()
        keyboard_listener.join()

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
        print("\t{0} - determine new mood and start relevant playlist".format(self.CHANGE_MOOD_KEY))
        print("\t{0} - get info on mood".format(self.INFO_KEY))
        print("\t{0} - play/pause".format(self.PLAY_PAUSE_KEY))
        print("\t{0} - next".format(self.NEXT_KEY))
        print("\t{0} - prev".format(self.PREV_KEY))
        print("\t{0} - quit".format(self.QUIT_KEY))

    def on_keypress(self, key):
        logger.debug("Pressed key {0}".format(key))
        if key == self.QUIT_KEY:
            logger.info("Exiting...")
            stop_listening()
        elif key == self.CHANGE_MOOD_KEY:
            logger.info("Determining new mood...")
            Thread(target=self.determine_mood_and_play, args=(), name='determine_mood_and_play').start()
        elif key == self.PLAY_PAUSE_KEY:
            logger.info("Play/pause music...")
            if self.music is not None:
                Thread(target=self.music.play_pause, args=(), name='play_pause').start()
        elif key == self.INFO_KEY:
            logger.info("Displaying info...")
            Thread(target=self.get_reasoning_info, args=(), name='get_reasoning_info').start()
        elif key == self.NEXT_KEY:
            logger.info("Next track...")
            if self.music is not None:
                Thread(target=self.next_track, args=(), name='next_track').start()
        elif key == self.PREV_KEY:
            logger.info("Previous track...")
            if self.music is not None:
                Thread(target=self.prev_track, args=(), name='prev_track').start()

    def determine_mood_and_play(self):
        logger.debug("Aquiring mood lock...")
        with self.mood_lock:
            logger.debug("Mood lock aquired.")
            if self.mood is not None and self.music is not None:
                self.music.start_playlist_based_on_mood(self.mood.determine_mood())
                print("MOOD: {0} | PLAYLIST: {1}".format(self.mood.current_mood, self.music.playlist['name'] if self.music.playlist is not None else "None"))
                if self.screen_enabled and self.screen is not None:
                    self.refresh_rpi_display()
            logger.debug("Releasing mood lock...")

    def get_reasoning_info(self):
        if self.mood is not None and self.music is not None:
            print("Mood Reasoning: {0}".format(self.mood.current_mood_reason))
            print("Playlist Reasoning: {0}".format(self.music.search_query_reason))
            self.toggle_info_display()

    def next_track(self):
        self.music.next_track()
        if self.screen_enabled:
            self.refresh_rpi_display()

    def prev_track(self):
        self.music.previous_track()
        if self.screen_enabled:
            self.refresh_rpi_display()

    def refresh_rpi_display(self):
        if self.screen_enabled and self.screen is not None and self.mood is not None and self.music is not None:
            logger.debug("Aquiring display lock...")
            with self.display_lock:
                logger.debug("Display lock aquired.")
                self.screen.render(self.mood.current_mood, self.music.playlist['name'] if self.music.playlist is not None else "N/A", self.music.get_track_name(), self.music.get_artist(), self.mood.current_mood_reason, self.music.search_query_reason)
            logger.debug("Releasing display lock.")

    def toggle_info_display(self):
        if self.screen_enabled and self.screen is not None and self.mood is not None and self.music is not None:
            logger.debug("Aquiring display lock...")
            with self.display_lock:
                logger.debug("Display lock aquired.")
                self.screen.toggle_info_screen()
                self.screen.render(self.mood.current_mood, self.music.playlist['name'] if self.music.playlist is not None else "N/A", self.music.get_track_name(), self.music.get_artist(), self.mood.current_mood_reason, self.music.search_query_reason)
            logger.debug("Releasing display lock.")

    def display_refresh_timer(self):
        # refreshes the display periodically
        disp_refresh_daemon = Timer(30.0, self.display_refresh_timer)
        disp_refresh_daemon.daemon = True
        disp_refresh_daemon.start()
        self.refresh_rpi_display()

    def start_mood_timer(self):
        # default to every hour if environment not set
        durationMinutes = int(os.getenv('NEW_MOOD_TIMER_MINUTES')) if os.getenv('NEW_MOOD_TIMER_MINUTES') is not None else 60.0
        logger.info("Starting a new mood timer for {0} minutes from now...".format(durationMinutes))
        timer_daemon = Timer(60.0 * (float(durationMinutes)), self.start_mood_timer)
        timer_daemon.daemon = True
        timer_daemon.start()
        self.determine_mood_and_play()
