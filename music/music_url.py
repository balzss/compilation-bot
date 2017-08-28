import pafy

pl = 'https://www.youtube.com/playlist?list=PLDcPimbLEWH99SxqupfspMsNjuBrjEjoI'
playlist = pafy.get_playlist(pl)
with open('links.txt', 'w') as links:

    for v in playlist['items']:
        dur = v['playlist_meta']['length_seconds']
        yt_id = v['playlist_meta']['encrypted_id']

        if 120 < int(dur) < 540:
            links.write('%s - %s\n' % (dur, yt_id))
