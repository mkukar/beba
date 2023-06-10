# beba
 Music curated by an AI through mood

## Requirements
- Spotify API key
- OpenAI API key
- Python 3+

### Optional
- NYTimes API Key (used to get news, movies, books to determine mood)

## Setup

1. Install dependencies

    `pip install -r requirements.txt`

2. Set API keys and playback device info in `.env` file
    - _You can use the `.env.template` file as reference (rename to .env with your configuration set)_

## Run

`python src/main.py`

- Use keyboard to control (play/pause, start new mood, etc.)
- NEW_MOOD_TIMER_MINUTES will automatically generate a new mood and kick off the playlist it found every X minutes (defaults to every hour)

## Troubleshooting

See log file generated with name `beba.log`

## Etymology
Named after Bela Bartok, a founder of ethnomusicology.
https://en.wikipedia.org/wiki/B%C3%A9la_Bart%C3%B3k

## Author
 Michael Kukar

## License
See LICENSE.md file