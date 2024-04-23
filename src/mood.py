# Copyright Michael Kukar 2023

from mood_changer import *

import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from noaa_sdk import NOAA
import os
import importlib

logger = logging.getLogger('beba')

class Mood:

    MOOD_PROMPT = """
    Pretend you are a human that can experience moods and feelings and enjoys expressing them. 
    Given the following information, return a unique, creative, and specific mood or feeling
    that is a single word followed by a colon. Your mood should be intuitive and simple.
    Your mood should not be reflective, introspective, intrigued, stimulated, enlighted, inspired 
    or a similar type of mood that is vague or uninteresting.
    After the colon give a descriptive reasoning for the mood you are now in.
    Your response must only include exactly one colon.
    {mood_changer_text}
    """
    MOOD_PROMPT_VARS = ['mood_changer_text']
    MOOD_SPLIT_CHARACTER = ':'

    current_mood = 'happy'
    current_mood_reason = ''

    def __init__(self, llm):
        self.llm = llm
        self.mood_prompt_template = PromptTemplate(
            input_variables=self.MOOD_PROMPT_VARS,
            template=self.MOOD_PROMPT
        )
        self.mood_chain = LLMChain(llm=self.llm, prompt=self.mood_prompt_template)
        self.weather_noaa = NOAA()
        self.mood_changers = self.get_enabled_mood_changers()

    def get_enabled_mood_changers(self):
        mood_changers = []
        mood_topics_enabled = [x.capitalize().strip() for x in os.getenv('MOOD_TOPICS_ENABLED').strip().split(',')] if os.getenv('MOOD_TOPICS_ENABLED') else []
        module =  importlib.import_module("mood_changer")
        for mood_topic in mood_topics_enabled:
            try:
                moodChangerClass = getattr(module, "{0}MoodChanger".format(mood_topic))
                mood_changers.append(moodChangerClass())
            except Exception as e:
                logger.warning("Could not find mood changer with name {0}, will not enable.".format(mood_topic))
        return mood_changers

    # get relevant info that affects our LLMs mood
    def get_mood_changers(self):
        mood_changer_state = {}
        for mood_changer in self.mood_changers:
            mood_changer_state[mood_changer.get_mood_changer_topic()] = mood_changer.get_mood_changer_summary()
        return mood_changer_state

    def format_mood_changers_into_text(self, mood_changers):
        mood_changer_text = ''
        for topic, summary in mood_changers.items():
            mood_changer_text += "{0}\n".format(summary)
        return mood_changer_text

    def determine_mood(self, retry=True):
        try:
            mood_changers = self.get_mood_changers()
            logger.debug("Mood changers: {0}".format(str(mood_changers)))
            mood_changer_text = self.format_mood_changers_into_text(mood_changers)
            logger.debug("Mood changer text: {0}".format(mood_changer_text))
            mood_response = self.mood_chain.invoke({'mood_changer_text' : mood_changer_text})
            logger.debug("LLM response: {0}".format(mood_response))
            if len(mood_response['text'].split(':')) > 2: # handling extra colons
                split_response = mood_response['text'].split(':')
                mood_response['text'] = split_response[0] + '-'.join(split_response[1:])
            self.current_mood, self.current_mood_reason = [x.strip() for x in mood_response['text'].split(self.MOOD_SPLIT_CHARACTER)]
            logger.info("New mood: {0}".format(self.current_mood))
        except Exception as e:
            if retry:
                logger.warning("Determining mood failed due to {0}, retrying...".format(e))
                return self.determine_mood(retry=False)
            else:
                logger.error(e)
                raise e
        return self.current_mood
