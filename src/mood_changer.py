# Copyright Michael Kukar 2023.

import os
from abc import ABC, abstractmethod
from noaa_sdk import NOAA
import logging
import requests, json
import random

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
        shortForecast = next(iter(self.weather_noaa.get_forecasts(
            os.getenv('WEATHER_ZIP_CODE'), 
            os.getenv('WEATHER_COUNTRY_CODE')
            )), {'shortForecast' : ''})['shortForecast']
        return "The weather is {0}".format(shortForecast).replace(':', '-')


class BooksMoodChanger(MoodChanger):

    BASE_ENDPOINT = "https://api.nytimes.com/"
    LIST_NAMES_URI = "svc/books/v3/lists/names.json"
    LIST_INFO_URI = "svc/books/v3/lists/current/{0}.json"

    TOPIC = "books"

    literature_lists = []

    def get_list_names(self):
        response = requests.get("{0}{1}?api-key={2}".format(self.BASE_ENDPOINT, self.LIST_NAMES_URI, os.getenv('NYTIMES_API_KEY')))
        if not response.ok:
            logger.error("Error with request, will not be able to use the topic {0}".format(self.get_mood_changer_topic()))
            logger.error("{0}".format(response))
            return []
        else:
            list_data = json.loads(response.content)
            if 'results' in list_data:
                return [x['list_name_encoded'] for x in list_data['results']]
            else:
                logger.error("Error with format of list_data, will not be able to use the topic {0}".format(self.get_mood_changer_topic()))
                logger.error(list_data)
                return []

    def get_list_data(self, list_name):
        response = requests.get("{0}{1}?api-key={2}".format(self.BASE_ENDPOINT, self.LIST_INFO_URI.format(list_name), os.getenv('NYTIMES_API_KEY')))
        if not response.ok:
            logger.error("Error with request, will not be able to use the topic {0}".format(self.get_mood_changer_topic()))
            logger.error("{0}".format(response))
            return []
        else:
            list_data = json.loads(response.content)
            return list_data['results']['books']

    def get_mood_changer_topic(self) -> str:
        return self.TOPIC

    def get_mood_changer_summary(self) -> str:
        # gets random book that it "read" recently
        self.literature_lists = self.get_list_names()
        random_list = random.choice(self.literature_lists)
        lit_data = self.get_list_data(random_list)
        self.current_book = random.choice(lit_data)
        return 'You have recently read {0} by {1} with the description {2}'.format(self.current_book['title'], self.current_book['author'], self.current_book['description']).replace(':', '-')


class MoviesMoodChanger(MoodChanger):

    BASE_ENDPOINT = "https://api.nytimes.com/"
    CRITIC_PICS_URI = "svc/movies/v2/reviews/picks.json"

    TOPIC = "movies"

    def get_movie_critic_picks(self):
        response = requests.get("{0}{1}?api-key={2}".format(self.BASE_ENDPOINT, self.CRITIC_PICS_URI, os.getenv('NYTIMES_API_KEY')))
        if not response.ok:
            logger.error("Error with request, will not be able to use the topic {0}".format(self.get_mood_changer_topic()))
            logger.error("{0}".format(response))
            return []
        else:
            list_data = json.loads(response.content)
            return list_data['results']


    def get_mood_changer_topic(self) -> str:
        return self.TOPIC
    
    def get_mood_changer_summary(self) -> str:
        # gets a random movie from critics picks that it "watched" recently
        self.critic_picks = self.get_movie_critic_picks()
        self.current_movie = random.choice(self.critic_picks)
        return 'You have recently watched {0} with the summary {1}'.format(self.current_movie['display_title'], self.current_movie['summary_short']).replace(':', '-')


class NewsMoodChanger(MoodChanger):

    TOPIC = "news"
    # see possible sections here https://developer.nytimes.com/docs/top-stories-product/1/overview
    NEWS_SECTIONS = ['home', 'science', 'arts', 'business', 'fashion', 'food', 'health', 'home', 'opinion', 'politics', 'sports', 'technology', 'theater', 'travel', 'us', 'world']
    BASE_ENDPOINT = "https://api.nytimes.com/"
    TOP_STORIES_URI = "svc/topstories/v2/{0}.json"

    def get_mood_changer_topic(self) -> str:
        return self.TOPIC
    
    def get_news_stories(self, section):
        response = requests.get("{0}{1}?api-key={2}".format(self.BASE_ENDPOINT, self.TOP_STORIES_URI.format(section), os.getenv('NYTIMES_API_KEY')))
        if not response.ok:
            logger.error("Error with request, will not be able to use the topic {0}".format(self.get_mood_changer_topic()))
            logger.error("{0}".format(response))
            return []
        else:
            list_data = json.loads(response.content)
            return list_data['results']

    def get_mood_changer_summary(self) -> str:
        # flips to a random page of the newspaper and reads an article
        section = random.choice(self.NEWS_SECTIONS)
        articles = self.get_news_stories(section)
        self.current_article = {}
        while 'section' not in self.current_article or 'title' not in self.current_article or 'abstract' not in self.current_article:
            # sometimes has ads, etc. that are not really "articles" in the API response
            self.current_article = random.choice(articles)
        return 'You have recently read an article in the {0} section with the title {1} and abstract {2}'.format(self.current_article['section'], self.current_article['title'], self.current_article['abstract']).replace(':', '-')