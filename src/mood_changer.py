# Copyright Michael Kukar 2023.

import os
from abc import ABC, abstractmethod
from noaa_sdk import NOAA
import logging

logger = logging.getLogger('beba')

class MoodChanger(ABC):

    @abstractmethod
    def get_mood_changer_topic(self) -> str:
        # should be the topic of the mood changer, such as "weather"
        return
    
    @abstractmethod
    def get_mood_changer_summary(self) -> str:
        # should be the summary of the current state of the mood changer, such as "partly cloudy"
        return

class WeatherMoodChanger(MoodChanger):

    TOPIC = "weather"

    def __init__(self):
        self.weather_noaa = NOAA()

    def get_mood_changer_topic(self) -> str:
        return self.TOPIC

    def get_mood_changer_summary(self) -> str:
        return next(iter(self.weather_noaa.get_forecasts(
            os.getenv('WEATHER_ZIP_CODE'), 
            os.getenv('WEATHER_COUNTRY_CODE')
            )), {'shortForecast' : ''})['shortForecast']

