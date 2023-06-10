# Copyright Michael Kukar 2023

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging, os

logger = logging.getLogger('beba')

class Music:

    SEARCH_BY_MOOD_PROMPT = """
    Pretend you are a human experiencing the mood of {mood}. Given that mood, what type of music would you search for? 
    This search can include specific genres, decades, and or artists or can be more generic depending on what you believe
    the mood should evoke. For example, your search could be "Upbeat Pop" or it could be "60s pop rock inspired by the beatles"
    Make your search as specific, unique and verbose as possible while being under ten words followed by a colon. 
    After the colon give your descriptive reasoning for deciding this search. Your response must only include exactly one colon.
    """
    SEARCH_BY_MOOD_VARS = ['mood']

    USER_SCOPE = 'user-read-playback-state,user-modify-playback-state'

    device = None
    playlist = None
    search_query = ''
    search_query_reason = ''

    def __init__(self, llm):
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=self.USER_SCOPE))
        self.llm = llm
        self.search_by_mood_template = PromptTemplate(
            input_variables=self.SEARCH_BY_MOOD_VARS,
            template=self.SEARCH_BY_MOOD_PROMPT
        )
        self.search_by_mood_chain = LLMChain(llm=self.llm, prompt=self.search_by_mood_template)
        self.setup_device_id(os.getenv('SPOTIFY_DEVICE_NAME'))

    def setup_device_id(self, device_name):
        devices = self.spotify.devices()
        logger.debug("Spotify devices: {0}".format(devices))
        if devices is None or len(devices) == 0:
            logger.error("No available devices found!")
            return
        for device in devices['devices']:
            if device['name'] == device_name:
                self.device = device
        if self.device is None:
            logger.error("Could not find a device with name {0}".format(device_name))

    def find_playlist(self, search_query):
        results = self.spotify.search(q=search_query, type='playlist')
        if results is not None and len(results) > 0:
            playlist = results['playlists']['items'][0]
            logger.debug("Found playlist: {0}".format(playlist))
            return playlist
        else:
            logger.error("Could not find a playlist for this search query {0}".format(search_query))
            return None

    def get_search_query_from_mood(self, mood):
        logger.debug("Getting search query based on mood {0}".format(mood))
        llm_response = self.search_by_mood_chain.run({'mood' : mood})
        logger.debug("LLM response: {0}".format(llm_response))
        if len(llm_response.split(':')) > 2: # handling extra colons
            split_response = llm_response.split(':')
            llm_response = split_response[0] + '-'.join(split_response[1:])
        self.search_query, self.search_query_reason = [x.strip() for x in llm_response.split(':')]
        return self.search_query
    
    def start_playlist_based_on_mood(self, mood):
        search_query = self.get_search_query_from_mood(mood)
        self.playlist = self.find_playlist(search_query)
        if self.playlist is not None and self.device is not None:
            logger.info("Starting playback of playlist {0}...".format(self.playlist))
            self.spotify.start_playback(context_uri=self.playlist['uri'], device_id=self.device['id'])
        else:
            logger.error("Could not start playback as playlist or device is not present.")
    
    def play_pause(self):
        logger.debug(self.spotify.currently_playing())
        if self.device is not None:
            if self.spotify.currently_playing() is not None:
                logger.info("Pausing playback...")
                self.spotify.pause_playback(device_id=self.device['id'])
            else:
                logger.info("Resuming playback...")
                self.spotify.start_playback(device_id=self.device['id'])

    def next_track(self):
        if self.device is not None:
            if self.spotify.currently_playing() is not None:
                logger.info("Skipping to next track...")
                self.spotify.next_track()

    def previous_track(self):
        if self.device is not None:
            if self.spotify.currently_playing() is not None:
                logger.info("Skipping to previous track...")
                self.spotify.previous_track()
