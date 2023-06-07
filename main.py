# Copyright Michael Kukar 2023

from mood import Mood

from dotenv import load_dotenv
import logging
import os
from langchain.llms import OpenAI

logger = logging.getLogger('beba')

def setup_logger():
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('beba.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def startup_message():
    print("BeBa")
    print("Created by Michael Kukar in 2023")

def setup():
    setup_logger()
    startup_message()
    load_dotenv()

if __name__ == "__main__":
    setup()
    logger.info("Starting...")
    llm = OpenAI(
        model="text-davinci-003",
        temperature=0.9,
        max_tokens=2000,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    mood = Mood(llm)
    print(mood.determine_mood())

