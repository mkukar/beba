# Copyright Michael Kukar 2023
# based on Waveshare ePaper 2.9in v2 display
# https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/examples/epd_2in9_V2_test.py

from langchain.llms import OpenAI
from dotenv import load_dotenv
import sys, os
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from PIL import Image,ImageDraw,ImageFont
import logging
from pathlib import Path
LIB_DIR = Path(os.path.dirname(os.path.realpath(__file__))).resolve().parent / "resources"/ "lib"
sys.path.append(str(LIB_DIR))
from waveshare_epd import epd2in9_V2

logger = logging.getLogger('beba')

class EPaperDisplay:

    BACKGROUND_COLOR = 0xFF # 0xFF is white, 0 is black
    FOREGROUND_COLOR = 0

    RESOURCE_DIR = Path(os.path.dirname(os.path.realpath(__file__))).resolve().parent / "resources"
    FONT_DIR = RESOURCE_DIR / "fonts"
    IMG_DIR = RESOURCE_DIR / "img"
    MOOD_IMG_DIR = IMG_DIR / "moods"

    FONT_PATH = FONT_DIR / "Font.ttc"

    PREV_IMG_PATH = IMG_DIR / "icons8-prev-square-24.png"
    NEXT_IMG_PATH = IMG_DIR / "icons8-next-square-24.png"
    PLAY_PAUSE_IMG_PATH = IMG_DIR / "icons8-play-pause-square-24.png"
    NEW_MOOD_IMG_PATH = IMG_DIR / "icons8-reload-turn-arrow-function-to-spin-and-restart-24.png"
    INFO_IMG_PATH = IMG_DIR / "icons8-info-24.png"

    FONT_10 = ImageFont.truetype(str(FONT_PATH), 10)
    FONT_12 = ImageFont.truetype(str(FONT_PATH), 12)
    FONT_18 = ImageFont.truetype(str(FONT_PATH), 18)
    FONT_14 = ImageFont.truetype(str(FONT_PATH), 14)

    IMG_SIZE = 24

    MOOD_ICON_PROMPT = """
    Pretend you are a human that can experience moods. You are currently experiencing the mood {mood}.
    Given a list of possible emoji reactions to express your current mood, return the emoji reaction name 
    that you think is most fitting for your mood, followed by a colon. 
    After the colon give a descriptive reasoning for your choice. Your response must only include exactly one colon.

    {mood_reaction_options}
    """
    MOOD_ICON_PROMPT_VARS = ['mood', 'mood_reaction_options']

    mood_images = ['happy']
    current_mood_icon = 'happy'
    current_mood_icon_reason  = 'none'
    current_mood_text = ""

    is_info_screen = False

    def __init__(self, llm):
        self.llm = llm
        self.mood_prompt_template = PromptTemplate(
            input_variables=self.MOOD_ICON_PROMPT_VARS,
            template=self.MOOD_ICON_PROMPT
        )
        self.mood_chain = LLMChain(llm=self.llm, prompt=self.mood_prompt_template)
        logger.info("Loading icons and mood images...")
        self.PREV_IMG = self.load_image(str(self.PREV_IMG_PATH))
        self.NEXT_IMG = self.load_image(str(self.NEXT_IMG_PATH))
        self.PLAY_PAUSE_IMG = self.load_image(str(self.PLAY_PAUSE_IMG_PATH))
        self.NEW_MOOD_IMG = self.load_image(str(self.NEW_MOOD_IMG_PATH))
        self.INFO_IMG = self.load_image(str(self.INFO_IMG_PATH))
        self.load_installed_mood_images()
        logger.info("Setting up display...")
        self.epd = epd2in9_V2.EPD()
        self.init_and_refresh()
        logger.info("Display initialized.")

    # ensures image works on epaper (converts transparent -> white)
    def load_image(self, image_path):
        raw_image = Image.open(image_path)
        new_image = Image.new("RGBA", raw_image.size, "WHITE")
        new_image.paste(raw_image, (0,0), raw_image)
        new_image.convert("RGB")
        return new_image

    def render(self, mood_text, playlist_text, song_name_text, artist_name_text, mood_info_text, playlist_info_text):
        if not self.is_info_screen:
            self.render_main(mood_text, playlist_text, song_name_text, artist_name_text)
        else:
            self.render_info(mood_text, playlist_text, mood_info_text, playlist_info_text)

    def render_main(self, mood_text, playlist_text, song_name_text="SONG", artist_name_text="ARTIST"):
        Himage = Image.new('1', (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(Himage)
        draw.text((240, 0), 'BeBa v1.0', font = self.FONT_12, fill = 0)
        draw.text((110, 10), '{0}'.format(mood_text), font = self.FONT_18, fill = 0)
        if len(playlist_text) > 30:
            playlist_font = self.FONT_12
        elif len(playlist_text) > 20:
            playlist_font = self.FONT_14
        else:
            playlist_font = self.FONT_18
        draw.text((110, 32), '{0}'.format(playlist_text), font = playlist_font, fill = 0)
        draw.text((110, 55), '{0}'.format(song_name_text), font = self.FONT_12, fill = 0)
        draw.text((110, 70), 'by {0}'.format(artist_name_text), font = self.FONT_12, fill = 0)
        self.render_button_info(draw, Himage)
        if self.current_mood_text != mood_text:
            self.render_mood(Himage, self.determine_mood_image(mood_text))
        else:
            self.render_mood(Himage, self.current_mood_icon.lower())
        self.current_mood_text = mood_text
        self.epd.display(self.epd.getbuffer(Himage))

    def split_strings(self, string_input, max_length):
        return [string_input[i:i+max_length] for i in range(0, len(string_input), max_length)]

    def render_info(self, mood_text, playlist_text, mood_info_text, playlist_info_text):
        Himage = Image.new('1', (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(Himage)
        info_strings = []
        string_size = 40
        info_strings.extend(self.split_strings(mood_info_text, string_size))
        info_strings.extend(self.split_strings("{0} {1}".format(playlist_text, playlist_info_text), string_size))
        draw.text((240, 0), 'BeBa v1.0', font = self.FONT_12, fill = 0)
        startY = 10
        yIncrement = 10
        for info_str in info_strings:
            draw.text((110, startY), '{0}'.format(info_str), font = self.FONT_10, fill = 0)
            startY += yIncrement
        self.render_button_info(draw, Himage)
        if self.current_mood_text != mood_text:
            self.render_mood(Himage, self.determine_mood_image(mood_text))
        else:
            self.render_mood(Himage, self.current_mood_icon.lower())
        self.current_mood_text = mood_text
        self.epd.display(self.epd.getbuffer(Himage))

    def render_button_info(self, draw, Himage):
        draw.line((10, self.epd.width-35, self.epd.height-10, self.epd.width-35), fill = 0)
        Himage.paste(self.NEW_MOOD_IMG, (17, self.epd.width-28))
        Himage.paste(self.PREV_IMG, (76, self.epd.width-28))
        Himage.paste(self.PLAY_PAUSE_IMG, (135, self.epd.width-28))
        Himage.paste(self.NEXT_IMG, (194, self.epd.width-28))
        Himage.paste(self.INFO_IMG, (253, self.epd.width-28))

    def load_installed_mood_images(self):
        mood_images = []
        for mood_file in self.MOOD_IMG_DIR.iterdir():
            if mood_file.is_file():
                mood_images.append(mood_file.stem)
        self.mood_images = mood_images

    # uses mood text to determine what mood image to use
    def determine_mood_image(self, mood_text):
        logger.debug(', '.join(self.mood_images))
        mood_icon_response = self.mood_chain.run({'mood' : mood_text, 'mood_reaction_options' : ', '.join(self.mood_images)})
        logger.debug("LLM response: {0}".format(mood_icon_response))
        if len(mood_icon_response.split(':')) > 2: # handling extra colons
            split_response = mood_icon_response.split(':')
            mood_icon_response = split_response[0] + '-'.join(split_response[1:])
        self.current_mood_icon, self.current_mood_icon_reason = [x.lower().strip() for x in mood_icon_response.split(':')]
        return self.current_mood_icon.lower()

    def render_mood(self, Himage, mood):
        self.MOOD_IMG_PATH = self.MOOD_IMG_DIR / "{0}.png".format(mood)
        self.MOOD_IMG = self.load_image(str(self.MOOD_IMG_PATH))
        Himage.paste(self.MOOD_IMG, (10, 0))

    def init_and_refresh(self):
        self.epd.init()
        self.epd.Clear(0xFF)

    def toggle_info_screen(self):
        self.is_info_screen = not self.is_info_screen

# run this directly to test display
if __name__ =="__main__":
    load_dotenv()
    llm = OpenAI(
        model="text-davinci-003",
        temperature=0.9,
        max_tokens=2000,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    display = EPaperDisplay(llm)
    display.render_main("Unsure", "TEST PLAYLIST")
