# Copyright Michael Kukar 2023

from controller import Controller

import logging

logger = logging.getLogger('beba')


if __name__ == "__main__":
    controller = Controller()
    controller.setup()
    controller.start()


