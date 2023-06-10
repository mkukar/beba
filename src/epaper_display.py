# Copyright Michael Kukar 2023
# based on Waveshare ePaper 2.9in v2 display
# https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/examples/epd_2in9_V2_test.py

import sys, os
from PIL import Image,ImageDraw,ImageFont
import logging
from pathlib import Path
LIB_DIR = Path(os.path.dirname(os.path.realpath(__file__))).resolve().parent / "resources"/ "lib"
sys.path.append(str(LIB_DIR))
print(sys.path)
from waveshare_epd import epd2in9_V2

logger = logging.getLogger('beba')

class EPaperDisplay:

    BACKGROUND_COLOR = 0xFF # 0xFF is white, 0 is black
    FOREGROUND_COLOR = 0

    RESOURCE_DIR = Path("../resources")
    FONT_DIR = RESOURCE_DIR / "fonts"
    IMG_DIR = RESOURCE_DIR / "img"

    FONT_PATH = FONT_DIR / "Font.ttc"

    PREV_IMG_PATH = IMG_DIR / "icons8-square-box-with-a-double-arrow-for-back-button-24.png"
    NEXT_IMG_PATH = IMG_DIR / "icons8-fast-forwarding-the-music-on-a-music-application-24.png"
    PLAY_PAUSE_IMG_PATH = IMG_DIR / "icons8-play-pause-24.png"
    NEW_MOOD_IMG_PATH = IMG_DIR / "icons8-reload-turn-arrow-function-to-spin-and-restart-24.png"
    INFO_IMG_PATH = IMG_DIR / "icons8-info-24.png"

    FONT_24 = ImageFont.truetype(str(FONT_PATH), 24)
    FONT_18 = ImageFont.truetype(str(FONT_PATH), 18)

    PREV_IMG = Image.open(str(PREV_IMG_PATH))
    NEXT_IMG = Image.open(str(NEXT_IMG_PATH))
    PLAY_PAUSE_IMG = Image.open(str(PLAY_PAUSE_IMG_PATH))
    NEW_MOOD_IMG = Image.open(str(NEW_MOOD_IMG_PATH))
    INFO_IMG = Image.open(str(INFO_IMG_PATH))

    def __init__(self):
        logger.info("Setting up display...")
        self.epd = epd2in9_V2.EPD()
        self.init_and_refresh()
        logger.info("Display initialized.")
    
    def render_main(self, mood_text, playlist_text):
        Himage = Image.new('1', (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(Himage)
        draw.text((10, 0), 'BeBa v1.0', font = self.FONT_18, fill = 0)
        draw.text((10, 20), 'FEELING | LISTENING TO', font = self.FONT_18, fill = 0)
        draw.text((10, 40), '{0} | {1}'.format(mood_text, playlist_text), font = self.FONT_24, fill = 0)
        draw.line((10, 70, self.epd.width-10, 60), fill = 0)
        self.epd.display(self.epd.getbuffer(Himage))

    def render_button_info(self, Himage):
        Himage.paste((10, self.epd.height-30), self.NEW_MOOD_IMG)
        Himage.paste((40, self.epd.height-30), self.PREV_IMG)
        Himage.paste((70, self.epd.height-30), self.PLAY_PAUSE_IMG)
        Himage.paste((100, self.epd.height-30), self.NEXT_IMG)
        Himage.paste((130, self.epd.height-30), self.INFO_IMG)

    def init_and_refresh(self):
        self.epd.init()
        self.epd.Clear(0xFF)

# run this directly to test display
if __name__ =="__main__":
    display = EPaperDisplay()
    display.render_main("TEST MOOD", "TEST PLAYLIST")