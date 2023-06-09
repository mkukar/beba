# Copyright Michael Kukar 2023

from mood_changer import WeatherMoodChanger

import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from noaa_sdk import NOAA

logger = logging.getLogger('beba')

class Mood:

    MOOD_PROMPT = """
    Pretend you are a human that can experience moods. Given the following information, return a unique and specific mood
    that is less than three words followed by a colon. After the colon give a descriptive reasoning for the mood you are now in.
    {mood_changer_text}
    """
    MOOD_PROMPT_VARS = ['mood_changer_text']
    MOOD_SPLIT_CHARACTER = ':'

    currentMood = 'happy'

    def __init__(self, llm):
        self.llm = llm
        self.mood_prompt_template = PromptTemplate(
            input_variables=self.MOOD_PROMPT_VARS,
            template=self.MOOD_PROMPT
        )
        self.mood_chain = LLMChain(llm=self.llm, prompt=self.mood_prompt_template)
        self.weather_noaa = NOAA()
        self.mood_changers = [
            WeatherMoodChanger()
        ]

    # get relevant info that affects our LLMs mood
    def get_mood_changers(self):
        mood_changer_state = {}
        for mood_changer in self.mood_changers:
            mood_changer_state[mood_changer.get_mood_changer_topic()] = mood_changer.get_mood_changer_summary()
        return mood_changer_state

    def format_mood_changers_into_text(self, mood_changers):
        mood_changer_text = ''
        for topic, summary in mood_changers.items():
            mood_changer_text += 'the {0} is {1}, '.format(topic, summary)
        mood_changer_text = mood_changer_text.capitalize()
        mood_changer_text = mood_changer_text[:-2] + '.'
        return mood_changer_text

    def determine_mood(self):
        mood_changers = self.get_mood_changers()
        logger.debug("Mood changers: {0}".format(str(mood_changers)))
        mood_changer_text = self.format_mood_changers_into_text(mood_changers)
        logger.debug("Mood changer text: {0}".format(mood_changer_text))
        mood_response = self.mood_chain.run({'mood_changer_text' : mood_changer_text})
        logger.debug("LLM response: {0}".format(mood_response))
        self.currentMood = mood_response.split(self.MOOD_SPLIT_CHARACTER)[0].strip()
        logger.info("New mood: {0}".format(self.currentMood))
        return self.currentMood