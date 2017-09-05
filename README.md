## What is this?
A python script that creates a compilation video with music from gifs from a given subreddit. [Here is an example
video.]()

## What does it need?
Python3 and FFmpeg.

## How to use it?
- clone or download the repo
- inside the repo make a virtualenv (for 3.6): `python3 -m venv bot-env`
- activate virtualenv (for 3.6): `source bot-env/bin/activate`
- install dependencies: `pip3 install -r requirements.txt`
- run script: `python3 app.py`
- or run script with options (see details below): `python3 app.py -s woahdude -m ~/Downloads/random-song.mp3`

## What command line options does it have?
- specifying the subreddit (defaults to [r/oddlysatisfying]()): `--subreddit [SUB NAME]` or `-s [SUB NAME]`
- specifying the background music (defaults to a random track [from here]()): `--music [MUSIC PATH]` or `-m [MUSIC PATH]`
