import argparse
import random
import os
import re
import glob
import shutil
import time
from urllib import request
import json
import subprocess
import sys

from moviepy import editor as mp
from scipy.ndimage.filters import gaussian_filter
from praw import Reddit
import pafy
from ffmpy import FFmpeg


def create_dir():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    dirn = 'data/%s' % time.strftime("%d_%m")

    if os.path.exists(dirn):
        shutil.rmtree(dirn)
    os.makedirs(dirn)
    os.chdir(dirn)


def music_download():
    with open('../../music/links.txt', 'r') as links:
        l = random.choice(list(links)).split(' - ')
        music_dur = int(l[0])
        link = 'https://www.youtube.com/watch?v=%s' % l[1]

    audio = pafy.new(link).getbestaudio()
    audio.download(filepath='music.%s' % audio.extension)

    music = glob.glob('music.*')[0]
    if 'webm' in music:
        FFmpeg(inputs={'music.webm': None}, outputs={'music.mp3': None}).run()
        os.remove(music)

    return os.path.abspath('music.mp3'), music_dur


def total_duration():
    files = [f for f in glob.glob('*.mp4') if re.match('[0-9]+.mp4', f)]
    return sum([get_duration(f) for f in files])


def get_duration(f):
    intermediate = subprocess.check_output('ffmpeg -i "%s" 2>&1 | grep Duration' % f,
            shell=True).decode().split(': ')[1].split(', ')[0].split(':')
    return int(float(intermediate[-2])*60 + float(intermediate[-1]))


def content_downloader(sub, dur):
    # get list of top content in given sub from last week
    search_limit = 100
    ro = Reddit(client_secret='<YOUR_CLIENT_SECRET>', client_id='<YOUR_CLIENT_ID>', user_agent='collects gifs for yt compilation')
    contents = ro.subreddit(sub).top('week', limit=search_limit)

    # get list of urls for 'acceptable' content
    final_urls = []
    for x in contents:
        # fancy regex for every type of imgur url
        if bool(re.match(r'http[s]?://(i\.)?imgur.com/.*?\.gif[v]?$', x.url)):
            final_urls.append(re.sub(r'\.gif[v]?$', '.mp4', x.url))
        elif bool(re.match(r'http[s]?://gfycat.com/', x.url)):
            json_url = 'https://gfycat.com/cajax/get/' + x.url.split('/')[-1]
            try:
                json_file = json.loads(request.urlopen(json_url)
                    .read().decode())
                final_urls.append(json_file["gfyItem"]["mp4Url"])
            except Exception as e:
                print('ERROR with gfycat url\n' + str(e))

        elif bool(re.match(r'http[s]?://giphy.com/', x.url)):
            # giphy has multiple ways of constructing urls for the same gif, this deals with that
            giphy_id = x.url.split('/')[-2] \
                    if x.url.split('.')[-1] == 'gif' \
                    else x.url.split('-')[-1]

            json_url = 'http://api.giphy.com/v1/gifs/ \
                    %s ?api_key=<YOUR_API_KEY>' % giphy_id
            try:
                jsonf = json.loads(request.urlopen(json_url)
                        .read().decode())
                final_urls.append(jsonf["data"]["images"]["original"]["mp4"])
            except Exception as e:
                print('ERROR with giphy url\n' + str(e))
        # TODO implement standard gif, reddit's own video and youtube support

    total_duration = 0
    audio_duration = dur
    for i, url in enumerate(final_urls):
        ext = url.split('.')[-1]
        try:
            file_name = str(i) + '.' + ext
            request.urlretrieve(url, file_name)
            f_dur = get_duration(file_name)
            if f_dur < 2:
                print('GIF is too short: %ss!' % f_dur)
                os.remove(file_name)
            elif f_dur > 15:
                os.remove(file_name)
                print('GIF is too long: %ss!' % f_dur)
            else:
                total_duration += f_dur
                if total_duration >= audio_duration:
                    os.remove(file_name)
                    print('Found enough GIF for the music!')
                    print(total_duration)
                    break
        except Exception as e:
            raise Exception(e)
    print('FINISHED!')


def blur(image):
    return gaussian_filter(image.astype(float), sigma=12)

def videofier(music_path):
    w, h = 1280, 720
    crop_size = 2
    files = glob.glob('*.mp4')
    random.shuffle(files)
    clip_list = []

    for f in files:
        clip = mp.VideoFileClip(f)
        bc_args = {'height':h}
        clip_args = {'width':w}
        center = {'x_center':w / 2}

        if clip.w / clip.h < 16 / 9:
            bc_args, clip_args = clip_args, bc_args
            center = {'y_center':h / 2}

        blurred_clip = clip.resize(**bc_args).crop(**center, **clip_args).fl_image(blur)
        clip = clip.resize(**clip_args).crop(x1=crop_size, width=w - crop_size * 2,
                y1=crop_size, height=h - crop_size * 2).margin(crop_size, color=(0, 0, 0))

        clip_list.append(mp.CompositeVideoClip([blurred_clip, clip.set_pos('center')]))

    final_clip = mp.concatenate_videoclips(clip_list).fadein(2).fadeout(2)
    final_clip.write_videofile('silent.mp4', fps=24, audio=None)

    FFmpeg(inputs={'silent.mp4': None, music_path: None}, outputs={'final.mp4': '-shortest'}).run()
    os.remove('silent.mp4')


if __name__ == '__main__':
    dirname = create_dir()

    parser = argparse.ArgumentParser()
    parser.add_argument('--subreddit', '-s', help="name of the subreddit where it gets the gifs from", type=str, default='oddlysatisfying')
    parser.add_argument('--music', '-m', help="music file path to put under the final video", type=str)
    args=parser.parse_args()

    subreddit = args.subreddit
    if args.music:
        music = args.music
        duration = get_duration(args.music)
    else:
        music, duration = music_download()

    content_downloader(sub = subreddit, dur = duration)
    videofier(music_path = music)
