# @ESBColorBot - Twitter Bot in Flask
@ESBColorBot is a bot that tweets out the lighting color of the Empire State Building. It is also intended to be a base and framework for building bots with more interesting utility.

@ESBColorBot has 3 main functional components:
1) update_database() - Scapes the ESB lighting calendar and dumps results into a PostgreSQL. This database can then be used for other services.
2) make_tweet() - attempts to find relevant users and hashtags on Twitter to attach to the description of the lighting. Several NLP and entity extraction APIs were tested for this function with disappointing results. Current implementation uses a Google CustomSearch (https://developers.google.com/custom-search/) pointed at twitter.com. Relevance of the suggestions will be evaluated over time. 
3) tweeter() - tweets the days ESB lighting description.

# References
This bot was inspired by:
- http://whatcoloristheempirestatebuilding.com/ and the inactive https://twitter.com/esbcolors
- https://twitter.com/empirestatebldg
- @swiftsam's https://twitter.com/esbcolor and its intense hashtags (adding the make_tweet() function was an attempt to add useful value over and above @ESBcolor)

# Is this bot well behaved?
Testing against the four tips given in http://tinysubversions.com/2013/03/basic-twitter-bot-etiquette/:
- Don’t @mention people who haven’t opted in
    - FAIL - this bot does @ mention people. However, this should be a value-add as it links accounts to a real-world event that they are associated with. For testing purposes, a '.@' is used. This may be removed in the future if the bot is good at identifying the right relevant users. If the bot is bad at identification, the feature may be disabled.
- Don’t follow Twitter users who haven’t opted in
    - PASS
- Don’t use a pre-existing hashtag
    - FAIL - this bot does use pre-existing hashtags. However, this should be a value-add as it links these hashtags to a real-world event that they are associated with. It makes not attempt to participate in trending hashtags and only tweets once a day, so it shouldn't be intrusive.
- Don’t go over your rate limits
    - PASS

