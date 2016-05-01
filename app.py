import os, sys
import requests
import re
import json

from flask import Flask
from bs4 import BeautifulSoup

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Table, Column, Integer
from sqlalchemy import DateTime

import time, datetime
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
import atexit

import tweepy
from googleapiclient import discovery


##########################
##### Configuration ######
##########################

# Application settings
APP_NAME = "ESBBot"
APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"
APP_ROOT = os.path.dirname(os.path.abspath(__file__)) 
#APP_STATIC = os.path.join(APP_ROOT, 'static')

# Flask config settings
CSRF_ENABLED = True
DEBUG = False
TESTING = False
DEVELOPMENT = False

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

# Authorize Tweepy
auth = tweepy.OAuthHandler(app.config['C_KEY'], app.config['C_SECRET'])  
auth.set_access_token(app.config['A_TOKEN'], app.config['A_TOKEN_SECRET'])  
api = tweepy.API(auth)  

# Authorize Google Custom Search
service = discovery.build("customsearch", 
                          "v1",
                          developerKey=app.config['GDEV_KEY'])

# Setup chron job to refresh listings every day
cron = BackgroundScheduler(daemon=True)
# Explicitly kick off the background thread
cron.start()


##########################
##### Start Models #######
##########################

class ESBLightState(db.Model): 
    __tablename__ = 'ESBLightState'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    date = db.Column(db.Unicode(255), server_default=u'')
    description = db.Column(db.Unicode(255), server_default=u'')
    tweet = db.Column(db.Unicode(255), server_default=u'')

##########################
##### Start App ##########
##########################

def make_tweet(desc):
    # Attempt to match hashtags and mentions to description:
    # 1) Search Google for description
    # 2) Take top 10 results
    # 3) Find most frequent @'s and #'s
    try:
        # Build more accurate query by removing color information
        query = desc.split(' in honor of ')[1]
    except:
        # IF this fails, fallback to full description
        query = desc
    # Execute Google CustomSearch
    # CustomSearch engine setup for twitter.com
    res = service.cse().list(
          q=query,
          num=10,
          cx=app.config['GDEV_SEARCH'],
        ).execute()
    # Collect @'s and #'s
    ats = []
    hashes = []
    if int(res['searchInformation']['totalResults']) != 0:
        # Extract @'s and #'s
        # http://stackoverflow.com/questions/2304632/regex-for-twitter-username
        for index,item in enumerate(res['items']):
            snip = re.sub('<[^<]+?>', '', item['snippet'])
            if snip:
                ats += [i[1] for i in re.findall( r'(^|[^@\w])@(\w{1,15})\b',snip)]
                hashes += [i[1] for i in re.findall( r'(^|[^@\w])#(\w{1,15})\b',snip)]
        # Get most frequent item from list 
        # http://stackoverflow.com/questions/1518522/python-most-common-element-in-a-list
        # Default to empty if no results
        if len(ats)>0:
            at = '.@'+max(set(ats), key=ats.count)
        else:
            at = ''
        if len(hashes)>0:
            hashx = '#'+max(set(hashes), key=hashes.count)
        else:
            hashx = ''
    else:
        at = ''
        hashx = ''
    tweet = ''.join([desc,' ',at,' ',hashx])
    return tweet

# Update the database every day
@cron.scheduled_job('interval', seconds=60*60*24)
def update_database():
    ESBcal = "http://www.esbnyc.com/explore/tower-lights/calendar"
    r  = requests.get(ESBcal)
    soup = BeautifulSoup(r.text, 'html.parser')
    ESB_items = soup.find_all("li", class_="views-row")
    for item in ESB_items:
        native_date = item.find("span", class_="date-display-single").contents[0]
        stat_date = datetime.strptime(native_date, '%b %d, %Y')
        formatted_date = unicode(datetime.strftime(stat_date,'%Y-%m-%d'))
        link = item.find("a")['href']
        desc = item.find("p", class_="lighting-desc").contents[0].strip("\n ")
        exists = ESBLightState.query.filter_by(date=formatted_date).first()
        if not exists: # Create a new database item
            tweet = make_tweet(desc)
            item = ESBLightState(date=formatted_date,
                        description=desc,
                        tweet=tweet)
            db.session.add(item)
        elif stat_date > datetime.now():   #Update if in the future
            tweet = make_tweet(desc)
            exists.description = desc
            exists.tweet = tweet
    db.session.commit()

@cron.scheduled_job('interval', seconds=60*60*24)
def tweeter():
    today_date = unicode(datetime.strftime(datetime.now(),'%Y-%m-%d'))
    today_tweet = ESBLightState.query.filter_by(date=today_date).first().tweet
    api.update_status(today_tweet)

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    sys.exit(app.run(host='0.0.0.0',port=port))


