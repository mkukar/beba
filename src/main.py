# Copyright Michael Kukar 2023

from controller import Controller

import logging

logger = logging.getLogger('beba')

VERSION = "1.5"

if __name__ == "__main__":
    controller = Controller(VERSION)
    controller.setup()
    controller.start()
