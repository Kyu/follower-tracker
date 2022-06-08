#!/usr/bin/python3
from time import sleep

import schedule
import twitter
from event_bus import EventBus

import file_io
import followers
import events

# Create event bus
MAIN_BUS = EventBus()

# Get config options
CONFIG_FILENAME = "config.json"
config = file_io.get_config(CONFIG_FILENAME)

# Logging in to twitter
twitter_config = config['credentials']
CONSUMER_KEY = twitter_config['consumer_key']
CONSUMER_SECRET = twitter_config['consumer_secret']
ACCESS_TOKEN_KEY = twitter_config['access_token_key']
ACCESS_TOKEN_SECRET = twitter_config['access_token_secret']

schedule_config = config['schedule']
OUTPUT_NAME = schedule_config.get('output_name', 'saved_following.json')
LOG_NAME = schedule_config.get('log_name', 'follow_log.log')
RUN_EVERY = schedule_config.get('run_every', 0)
SLEEP_TIME = schedule_config.get('sleep_time', 30)

tracked_users_config = config['tracked_users']
QUERY_SELF = tracked_users_config.get('self', True)
USERS_TO_QUERY = tracked_users_config.get('others', [])

# Authenticate twitter
twitter_api = twitter.Api(consumer_key=CONSUMER_KEY,
                          consumer_secret=CONSUMER_SECRET,
                          access_token_key=ACCESS_TOKEN_KEY,
                          access_token_secret=ACCESS_TOKEN_SECRET,
                          sleep_on_rate_limit=True)

# Verify authentication
verified = twitter_api.VerifyCredentials()
if verified:
    print("Twitter verified as: \n" + str(verified))
else:
    print("Could not verify twitter user, please check the information provided in the config")
    exit(1)


def query_user(user_id: int = None, screen_name: str = None) -> events.TwitterUserFollowingQuery:
    # Get a user's current followers and mutuals, and retun an event with the data
    if user_id is None:
        user_id = twitter_api.GetUser(screen_name=screen_name).user_id
    if screen_name is None:
        screen_name = twitter_api.GetUser(user_id=user_id).screen_name

    current = followers.get_user_mutuals_followers(twitter_api, user_id)

    data = dict(current=current, user_id=user_id, screen_name=screen_name)
    return events.TwitterUserFollowingQuery(data)


def do_query():
    # Get information about all users once
    MAIN_BUS.emit(events.StartQueryEvent.EVENT_NAME)
    query_users_events = []

    for usr in USERS_TO_QUERY:
        # If begins with @, get id from username. Else, use user id
        if str(usr)[0] == '@':
            user_id = twitter_api.GetUser(screen_name=usr).id
        else:
            user_id = usr

        # Query user and emit an event saying you've queried that user
        this_user = query_user(user_id=user_id)
        MAIN_BUS.emit(events.TwitterUserFollowingQuery.EVENT_NAME, this_user)

        # Keeping track of all queried users
        query_users_events.append(this_user)

    # Emit an event with data of all queried users
    MAIN_BUS.emit(events.FinishAllQueryEvents.EVENT_NAME, query_users_events)


def start():
    # Emit an event saying the script is about to start
    MAIN_BUS.emit(events.StartMainEvent.EVENT_NAME, CONFIG_FILENAME, config, twitter_api)

    # Add self to query list if needed
    if QUERY_SELF:
        USERS_TO_QUERY.append(verified.id)

    # Performs one query
    do_query()

    # Run query on schedule, if config defines one
    if RUN_EVERY > 0:
        schedule.every(RUN_EVERY).seconds.do(do_query)
        while True:
            schedule.run_pending()
            sleep(SLEEP_TIME)

    # Emit an event saying script is about to exit
    MAIN_BUS.emit(events.FinishMainEvent.EVENT_NAME, CONFIG_FILENAME, config, twitter_api)


if __name__ == '__main__':
    start()
