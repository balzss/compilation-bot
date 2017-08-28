from praw import Reddit
import pafy
from ffmpy import FFmpeg

import random
import os
import re
import glob
import shutil
import time
from urllib import request
import json
import subprocess

from moviepy import editor as mp
from scipy.ndimage.filters import gaussian_filter


def create_dir(remove=True):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    dirn = 'data/%s' % time.strftime("%d_%m")
    if remove:
        if os.path.exists(dirn):
            shutil.rmtree(dirn)
        os.makedirs(dirn)
    os.chdir(dirn)


def music_magic():
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

    return music_dur


def total_duration():
    files = [f for f in glob.glob('*.mp4') if re.match('[0-9]+.mp4', f)]
    return sum([get_duration(f) for f in files])


def get_duration(f):
    intermediate = subprocess.check_output('ffmpeg -i %s 2>&1 | grep Duration' % f,
            shell=True).decode().split(': ')[1].split(', ')[0].split(':')

    if int(intermediate[1]) > 0 or int(intermediate[0]) > 0:
        return 0

    return int(float(intermediate[-1]))


def content_downloader(sub, dur):

    # get list of top content in given sub from last week
    search_limit = 100
    ro = Reddit(client_secret='RBDf_ezpW5XTWINEkyTR_ToEpsw', client_id='N686mJvyudlTnw', user_agent='collects gifs for yt compilation')
    contents = ro.subreddit(sub).top('week', limit=search_limit)

    # get list of urls for 'acceptable' content
    final_urls = []
    for x in contents:
        if bool(re.match(r'http[s]?://(i\.)?imgur.com/.*?\.gif[v]?$', x.url)):
            final_urls.append(re.sub(r'\.gif[v]?$', '.mp4', x.url))

        elif bool(re.match(r'http[s]?://gfycat.com/', x.url)):
            json_url = 'https://gfycat.com/cajax/get/' + x.url.split('/')[-1]

            # TODO use requests
            try:
                json_file = json.loads(request.urlopen(json_url)
                    .read().decode())
                final_urls.append(json_file["gfyItem"]["mp4Url"])
            except Exception as e:
                print('ERROR with gfycat url\n' + str(e))

        elif bool(re.match(r'http[s]?://giphy.com/', x.url)):
            # TODO look into giphy url parsing
            giphy_id = x.url.split('/')[-2] \
                    if x.url.split('.')[-1] == 'gif' \
                    else x.url.split('-')[-1]

            # TODO use requests
            json_url = 'http://api.giphy.com/v1/gifs/ \
                    %s ?api_key=dc6zaTOxFJmzC' % giphy_id
            try:
                jsonf = json.loads(request.urlopen(json_url)
                        .read().decode())
                final_urls.append(jsonf["data"]["images"]["original"]["mp4"])
            except Exception as e:
                print('ERROR with giphy url\n' + str(e))
        # TODO implement standard gif support

    total_duration = 0
    audio_duration = dur
    for i, url in enumerate(final_urls):
        ext = url.split('.')[-1]
        try:
            file_name = str(i) + '.' + ext
            request.urlretrieve(url, file_name)
            f_dur = get_duration(file_name)
            if f_dur < 2 or f_dur > 15:
                os.remove(file_name)
                print('TTOO LONG, or too short')
                print(f_dur)
            else:
                total_duration += f_dur
                if total_duration >= audio_duration:
                    os.remove(file_name)
                    print('LONG ENOUGH!')
                    print(total_duration)
                    break
        except Exception as e:
            print('---\n!ERROR:\n' + str(e) + '---\n')

    print('FINISHED!')


def blur(image):
    return gaussian_filter(image.astype(float), sigma=12)

def videofier():
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

        blurred_clip = clip.resize(**bc_args) \
                .crop(**center, **clip_args).fl_image(blur)
        clip = clip.resize(**clip_args) \
                .crop(x1=crop_size, width=w - crop_size * 2,
                y1=crop_size, height=h - crop_size * 2) \
                .margin(crop_size, color=(0, 0, 0))

        clip_list.append(mp.CompositeVideoClip(
                [blurred_clip, clip.set_pos('center')]))

    final_clip = mp.concatenate_videoclips(clip_list).fadein(2).fadeout(2)
    final_clip.write_videofile('final.mp4', fps=24, audio=None)

    FFmpeg(inputs={'final.mp4': None, 'music.mp3': None},
            outputs={'upload.mp4': '-shortest'}).run()


if __name__ == '__main__':
    create_dir()
    duration = music_magic()
    content_downloader('oddlysatisfying', duration)
    videofier()
