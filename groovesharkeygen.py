#!/usr/bin/env python

import urllib
import json
import md5
from sys import argv, exit

if len(argv) != 3:
  exit("Please provide your Grooveshark username and password as arguments.")

gl = argv[1]
gp = argv[2]

# Getting Grooveshark API key and endpoint URL
params = "user=%s&pass=%s" % (gl, gp)
gshark_response = urllib.urlopen("https://ssl.apishark.com/generateAPIKey", data=params)  
result = gshark_response.read()

if result.rfind("is now") == -1 : print "Error getting API URL"
else: 
  a = result.rfind("is now")
  grooveshark_url = result[a+8:a+32]
  print "API URL: %s" % grooveshark_url

# Getting Grooveshark API authorization key
gp = md5.new(gp)
params = md5.new("%s%s" % (gl, gp.hexdigest()))
params = urllib.urlencode(dict(username=gl, token=params.hexdigest()))
gshark_response = json.load(urllib.urlopen("http://1.apishark.com/genGSAuth/", data=params))
if gshark_response['Success']:
  grooveshark_gsauth = gshark_response['Result']
  print "GSAuth: %s" % grooveshark_gsauth
else:
  print "Error getting GSAuth string"
  print "Authentication failed. Please check your username and password."





