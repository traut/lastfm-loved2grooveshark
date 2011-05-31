#!/usr/bin/env python

import urllib
from xml.etree import ElementTree
import json
import time
import logging

log = logging.getLogger('lastfm2grooveshark')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


# constants

lastfm_username = 'LASTFM_USERNAME'
lastfm_key = 'LASTFM_KEY' # you can get one here http://www.last.fm/api/account

grooveshark_key = 'GROOVESHARK_KEY' # you can get key here http://apishark.com/#gettingStarted
grooveshark_gsauth = 'GSAuth' # you can get your GSAuth here https://ssl.apishark.com/generateGSAuth

playlist_name = 'lastfm-loved'

# urls
lastfm_url = "http://ws.audioscrobbler.com/2.0/?method=user.getlovedtracks&user=%(username)s&api_key=%(lastfm_key)s&limit=100000" % \
        dict(username=lastfm_username, lastfm_key=lastfm_key)

grooveshark_url = 'http://1.apishark.com/p:%s/' % grooveshark_key
grooveshark_search_url = grooveshark_url + 'searchSongs/'
grooveshark_create_playlist = 'http://1.apishark.com/createPlaylist/'


lastfm_loved_xml = urllib.urlopen(lastfm_url).read()
parsed_lastfm = ElementTree.fromstring(lastfm_loved_xml)

songs = []

skipped = []
counter = 0

def add_song(count, result):
    id = result['SongID']
    found_title = result['SongName']
    found_artist = result['ArtistName']
    found_album = result['AlbumName']
    songs.append(id)

    log.debug('%d: found: ID=%s "%s" by "%s", album "%s"' % (count, id, found_title, found_artist, found_album))

for track in parsed_lastfm.findall('*/track'):

    title = track.find('name').text
    artist = track.find('artist/name').text

    counter += 1

    log.debug('%d: Looking for "%s" by "%s"' % (counter, title, artist))

    # 1st search attempt
    search_data = urllib.urlencode(dict(query=title.encode('utf-8'), artist=artist.encode('utf-8')))
    response = json.load(urllib.urlopen(grooveshark_search_url, data=search_data))

    results = response['Result']

    if type(results) == list and len(results) > 0:
        add_song(counter, results[0])
    else:
        # 2nd search attempt
        search_data = urllib.urlencode(dict(query=('%s %s' % (title, artist)).encode('utf-8')))
        response = json.load(urllib.urlopen(grooveshark_search_url, data=search_data))

        results = response['Result']
        if type(results) == list and len(results) > 0:
            add_song(counter, results[0])
        else:
            skipped.append((title, artist))

    calls_left = response['RateLimit']['CallsRemaining']
    reset_time = response['RateLimit']['ResetTime']

    if calls_left <= 0:
        secs = abs(reset_time - int(time.time()))
        log.info("Going to sleep for %d" % secs)
        time.sleep(secs)
        log.info("Morning!")

#f = open('/tmp/songs-ok', 'w')
#f.writelines(json.dumps(songs))
#f.close()
#
#f = open('/tmp/songs-skipped', 'w')
#f.writelines(json.dumps(skipped))
#f.close()

log.info("Processed: %s" % counter)
log.info("OK: %s" % len(songs))
log.info("Skipped: %s" % len(skipped))

playlist_data = dict(gsAuth=grooveshark_gsauth, name=playlist_name, songIDs=json.dumps(songs))
playlist = json.load(urllib.urlopen(grooveshark_create_playlist, data=urllib.urlencode(playlist_data)))

if playlist['Success']:
    log.info("Playlist created: %s" % playlist['Result']['Url'])
else:
    log.error("Playlist not created: %s" % playlist['Result']['string'])





