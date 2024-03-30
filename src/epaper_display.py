# Copyright Michael Kukar 2023
# based on Waveshare ePaper 2.9in v2 display
# https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/examples/epd_2in9_V2_test.py

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import sys, os
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from PIL import Image,ImageDraw,ImageFont
import logging
import textwrap
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

    FONT_8 = ImageFont.truetype(str(FONT_PATH), 8)
    FONT_10 = ImageFont.truetype(str(FONT_PATH), 10)
    FONT_12 = ImageFont.truetype(str(FONT_PATH), 12)
    FONT_18 = ImageFont.truetype(str(FONT_PATH), 18)
    FONT_14 = ImageFont.truetype(str(FONT_PATH), 14)

    IMG_SIZE = 24

    MOOD_ICON_PROMPT = """
    Pretend you are a human that can experience moods and enjoys to express them.
    You are currently experiencing the mood {mood}.
    Given a list of possible icons to express your current mood, return the name 
    of the icon that you think is the most unique, creative, and accurate expression for your mood, 
    followed by the : character. 
    After the : character give a descriptive reasoning for your choice. 
    Your response must only include exactly one : (colon).

    {mood_reaction_options}
    """
    MOOD_ICON_PROMPT_VARS = ['mood', 'mood_reaction_options']

    mood_images = ['happy']
    current_mood_icon = 'happy'
    current_mood_icon_reason  = 'none'
    last_render = {
        'mood' : '',
        'playlist' : '',
        'song' : '',
        'artist' : '',
        'mood_info' : '',
        'playlist_info' : '',
        'is_info_screen': False
    }

    is_info_screen = False

    def __init__(self, llm, version_str):
        self.version_str = version_str
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
    
    def render(self, mood_text, playlist_text, song_name_text="SONG", artist_name_text="ARTIST", mood_info_text="MOOD INFO", playlist_info_text="PLAYLIST_INFO"):
        if not self.should_refresh(mood_text, playlist_text, song_name_text, artist_name_text, mood_info_text, playlist_info_text, self.is_info_screen):
            return
        logger.info("State has changed, refreshing display...")
        Himage = Image.new('1', (self.epd.width, self.epd.height), 255)
        draw = ImageDraw.Draw(Himage)
        draw.text((85, self.epd.height-15), 'BeBa v{0}'.format(self.version_str), font = self.FONT_10, fill = 0)
        draw.text((35, 115), '{0}'.format(mood_text.upper()), font = self.FONT_14, fill = 0)
        if not self.is_info_screen:
            max_text_length = 12
            text_font = self.FONT_12
            spacing = 15
            text_lines = textwrap.fill(playlist_text, max_text_length).split('\n')
            text_lines.extend('\n')
            text_lines.extend(textwrap.fill(song_name_text, max_text_length).split('\n'))
            text_lines.extend(textwrap.fill(artist_name_text, max_text_length).split('\n'))
        else:
            max_text_length = 24
            text_font = self.FONT_8
            spacing = 10
            text_lines = textwrap.fill(mood_info_text, max_text_length).split('\n')
            #text_lines.extend(textwrap.fill(playlist_info_text, max_text_length).split('\n'))
            
        self.render_text(draw, text_lines, 35, 140, spacing, text_font)
        self.render_button_info(draw, Himage)
        if self.last_render['mood'] != mood_text:
            self.render_mood(Himage, self.determine_mood_image(mood_text))
        else:
            self.render_mood(Himage, self.current_mood_icon.lower())
        Himage = Himage.transpose(method=Image.ROTATE_180)
        self.epd.display(self.epd.getbuffer(Himage))
        self.save_last_render(mood_text, playlist_text, song_name_text, artist_name_text, mood_info_text, playlist_info_text, self.is_info_screen)

    def should_refresh(self, mood, playlist, song, artist, mood_info, playlist_info, is_info_screen):
        return any([self.last_render['mood'] != mood, 
                self.last_render['playlist'] != playlist, 
                self.last_render['song'] != song,
                self.last_render['artist'] != artist,
                self.last_render['mood_info'] != mood_info,
                self.last_render['playlist_info'] != playlist_info,
                self.last_render['is_info_screen'] != is_info_screen])

    def save_last_render(self, mood, playlist, song, artist, mood_info, playlist_info, is_info_screen):
        self.last_render['mood'] = mood
        self.last_render['playlist'] = playlist
        self.last_render['song'] = song
        self.last_render['artist'] = artist
        self.last_render['mood_info'] = mood_info
        self.last_render['playlist_info'] = playlist_info
        self.last_render['is_info_screen'] = is_info_screen
        logger.debug(self.last_render)

    def render_text(self, draw, lines, start_x, start_y, y_spacing, font_size):
        for i, line in enumerate(lines):
            draw.text((start_x, start_y + (i*y_spacing)), '{0}'.format(line), font = font_size, fill = 0)

    def render_button_info(self, draw, Himage):
        start_x = 3
        start_x_line = 30
        draw.line((start_x_line, 5, start_x_line, self.epd.height-5), fill = 0)
        Himage.paste(self.NEW_MOOD_IMG, (start_x, 17))
        Himage.paste(self.PREV_IMG, (start_x, 76))
        Himage.paste(self.PLAY_PAUSE_IMG, (start_x, 135))
        Himage.paste(self.NEXT_IMG, (start_x, 194))
        Himage.paste(self.INFO_IMG, (start_x, 253))

    def load_installed_mood_images(self):
        mood_images = []
        for mood_file in self.MOOD_IMG_DIR.iterdir():
            if mood_file.is_file():
                mood_images.append(mood_file.stem)
        self.mood_images = mood_images

    # uses mood text to determine what mood image to use
    def determine_mood_image(self, mood_text, retry=True):
        try:
            logger.debug(', '.join(self.mood_images))
            mood_icon_response = self.mood_chain.invoke({'mood' : mood_text, 'mood_reaction_options' : ', '.join(self.mood_images)})
            logger.debug("LLM response: {0}".format(mood_icon_response))
            if len(mood_icon_response['text'].split(':')) > 2: # handling extra colons
                split_response = mood_icon_response['text'].split(':')
                mood_icon_response['text'] = split_response[0] + '-'.join(split_response[1:])
            self.current_mood_icon, self.current_mood_icon_reason = [x.lower().strip() for x in mood_icon_response['text'].split(':')]
        except Exception as e:
            if retry:
                return self.determine_mood_image(mood_text, retry=False)
            else:
                raise e
        return self.current_mood_icon.lower()

    def render_mood(self, Himage, mood):
        self.MOOD_IMG_PATH = self.MOOD_IMG_DIR / "{0}.png".format(mood)
        self.MOOD_IMG = self.load_image(str(self.MOOD_IMG_PATH))
        Himage.paste(self.MOOD_IMG, (35, 20))

    def init_and_refresh(self):
        self.epd.init()
        self.epd.Clear(0xFF)

    def toggle_info_screen(self):
        self.is_info_screen = not self.is_info_screen

# run this directly to test display
if __name__ =="__main__":
    load_dotenv()
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.9,
        max_tokens=2000,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    display = EPaperDisplay(llm, "1.0")
    display.render("Batty", "Test Playlist Name", "Songname", "An Artist")
    print(display.current_mood_icon)
    print(display.current_mood_icon_reason)
