#!/usr/bin/env python

import urllib, urllib2
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

def process_search_response(response):
    found = False
    results = response['Result']

    if type(results) == list and len(results) > 0:
        found = True
        add_song(counter, results[0])

    calls_left = response['RateLimit']['CallsRemaining']
    reset_time = response['RateLimit']['ResetTime']

    if calls_left <= 0:
        secs = abs(reset_time - int(time.time()))
        log.info("Going to sleep for %d" % secs)
        time.sleep(secs)
        log.info("Morning!")

    return found


for track in parsed_lastfm.findall('*/track'):

    title = track.find('name').text
    artist = track.find('artist/name').text

    counter += 1

    log.debug('%d: looking for "%s" by "%s"' % (counter, title, artist))

    # 1st search attempt
    search_data = urllib.urlencode(dict(query=title.encode('utf-8'), artist=artist.encode('utf-8')))
    response = json.load(urllib.urlopen(grooveshark_search_url, data=search_data))

    if not process_search_response(response):
        # 2nd search attempt
        search_data = urllib.urlencode(dict(query=('%s %s' % (title, artist)).encode('utf-8')))
        response = json.load(urllib.urlopen(grooveshark_search_url, data=search_data))

        if not process_search_response(response):
            skipped.append((title, artist))


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
    googl_request = urllib2.Request("https://www.googleapis.com/urlshortener/v1/url",
        headers = { "Content-Type": "application/json" },
        data = "{ 'longUrl' : '%s' }" % playlist['Result']['Url'])
    shorten = json.load(urllib2.urlopen(googl_request))
#   log.info("Playlist created: %s" % playlist['Result']['Url'])
    log.info("Playlist created: %s" % shorten['id'])
else:
    log.error("Playlist not created: %s" % playlist['Result']['string'])
