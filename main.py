#!/usr/bin/python3
from datetime import datetime

import diskcache as dc

import file_io
import events
import tracking
import twitter

# get event bus and create cache
bus = tracking.MAIN_BUS
OUTPUT_NAME = ""
LOG_NAME = ""
twitter_api = twitter.Api()
cache = dc.Cache('twt_users')
CACHE_EXPIRE = 432000  # 5 days in seconds, overridden in config


# A copy of twitter.User, for caching purposes
class FakeTwtUser:
    def __init__(self, user_id, screen_name, display_name):
        self.id = user_id
        self.screen_name = screen_name
        self.name = display_name


# Create a FakeTwtUser from twitter.User
def create_fake_twitter_user(user) -> FakeTwtUser:
    return FakeTwtUser(user.id, user.screen_name, user.name)


# Get the error code from a twitter.TwitterError
def parse_twitter_user_error_code(error: twitter.TwitterError):
    return error.message[0]['code']


# Generate text of the @ and display name of FakeTwtUser in a list
def gen_text(users: list[FakeTwtUser]) -> str:
    screens = [i.screen_name for i in users]
    names = [i.name for i in users]
    txt = ', '.join(f"{{@{t[0]}: {t[1]}}}" for t in zip(screens, names))
    if txt:
        txt = f"({len(users)}): \n {txt}"
    return str(txt)


# Get config options on tracker startup
@bus.on(events.StartMainEvent.EVENT_NAME)
def get_config(config_filename: str, cfg: dict, twt_api):
    global OUTPUT_NAME, LOG_NAME, CACHE_EXPIRE, twitter_api
    twitter_api = twt_api

    schedule_config = cfg['schedule']
    OUTPUT_NAME = schedule_config.get('output_name', 'saved_following.json')
    LOG_NAME = schedule_config.get('log_name', 'follow_log.log')
    CACHE_EXPIRE = schedule_config.get('cache_expire', 432000)


# Compare old followers/mutuals to current mutuals after all query events are completed
@bus.on(events.FinishAllQueryEvents.EVENT_NAME)
def keep_track(user_data: list[events.TwitterUserFollowingQuery]):
    # Get old user data from file
    old_info = file_io.load_follower_dict(OUTPUT_NAME)

    # Prepare a dict of current user data
    tracking_dict = {}

    last_updated = str(datetime.utcnow()) + "-UTC"

    update_text = ""

    # TODO make easier to read/follow lol
    for user in user_data:
        # Get this user's old info, if it exists, else a blank dict
        old = old_info.get(str(user.user_id), file_io.default_follower_dict)

        # Prepare a new dict of current info
        current = user.current
        current['screen_name'] = user.screen_name
        current['last_updated'] = last_updated

        tracking_dict[str(user.user_id)] = current

        # Prepare lists of changes in following/mutuals ids
        unfollow_ids = [f for f in old['followers'] if f not in current['followers']]
        unmutual_ids = [m for m in old['mutuals'] if m not in current['mutuals']]
        new_mutual_ids = [nm for nm in current['mutuals'] if nm not in old['mutuals']]
        new_follower_ids = [nf for nf in current['followers'] if nf not in old['followers']]
    
        unfollows = []
        unmutuals = []
        new_mutuals = []
        new_followers = []
    
        deleted_users = []
        suspended_users = []

        # This section checks user ids against the cache, if it doesn't exist, it queries twitter for information.
        # Takes long time on the first run
        # The process is repeated(!) for every list of changes, to get screen names of users
        # TODO D.R.Y.
        for u in unfollow_ids:
            # Look for user in cache
            _u_data = cache.get(u)

            # If they don't exist, ask twitter for the user and update the cache
            if not _u_data:
                try:
                    _u_data = create_fake_twitter_user(twitter_api.GetUser(user_id=u))
                    cache.set(u, _u_data, expire=CACHE_EXPIRE)
                except twitter.error.TwitterError as e:
                    error_code = parse_twitter_user_error_code(e)
                    if error_code == 50:
                        deleted_users.append(u)
                    elif error_code == 63:
                        suspended_users.append(u)
            if _u_data:
                unfollows.append(_u_data)
        
        for un in unmutual_ids:
            _u_data = cache.get(un)
            # u(ap)
            if not _u_data:
                try:
                    _u_data = create_fake_twitter_user(twitter_api.GetUser(user_id=un))
                    cache.set(un, _u_data, expire=CACHE_EXPIRE)
                except twitter.error.TwitterError as e:
                    error_code = parse_twitter_user_error_code(e)
                    if error_code == 50:
                        deleted_users.append(un)
                    elif error_code == 63:
                        suspended_users.append(un)
            if _u_data:
                unmutuals.append(_u_data)

        for _nm in new_mutual_ids:
            _u_data = cache.get(_nm)
            if not _u_data:
                try:
                    _u_data = create_fake_twitter_user(twitter_api.GetUser(user_id=_nm))
                    cache.set(_nm, _u_data, expire=CACHE_EXPIRE)
                except twitter.error.TwitterError as e:
                    error_code = parse_twitter_user_error_code(e)
                    if error_code == 50:
                        deleted_users.append(_nm)
                    elif error_code == 63:
                        suspended_users.append(_nm)
            if _u_data:
                new_mutuals.append(_u_data)

        for _nf in new_follower_ids:
            _u_data = cache.get(_nf)
            if not _u_data:
                try:
                    _u_data = create_fake_twitter_user(twitter_api.GetUser(user_id=_nf))
                    cache.set(_nf, _u_data, expire=CACHE_EXPIRE)
                except twitter.error.TwitterError as e:
                    error_code = parse_twitter_user_error_code(e)
                    if error_code == 50:
                        deleted_users.append(_nf)
                    elif error_code == 63:
                        suspended_users.append(_nf)
            if _u_data:
                new_followers.append(_u_data)

        # Generate text of all changes
        unfollow_text = gen_text(unfollows)
        unmutual_text = gen_text(unmutuals)
        new_mutual_text = gen_text(new_mutuals)
        new_follower_text = gen_text(new_followers)

        # If any text was generated, combine all text
        if unfollow_text or unmutual_text or new_mutual_text or new_follower_text:
            all_text = f"@{user.screen_name} ({user.user_id})"
            if unfollow_text:
                all_text += f"\nUn Followers: {unfollow_text}"
            if unmutual_text:
                all_text += f"\nUn Mutuals: {unmutual_text}"
            if new_mutual_text:
                all_text += f"\nNew Mutuals: {new_mutual_text}"
            if new_follower_text:
                all_text += f"\nNew Followers: {new_follower_text}"

            update_text = all_text + "\n"

    # Append update text to log file
    if update_text:
        update_text = f"\n{last_updated}\n{update_text}"
        file_io.append_text_to_file(update_text, LOG_NAME)

    # Update new tracking dict in file
    file_io.save_dict_to_file(tracking_dict, OUTPUT_NAME, old_info=old_info)


# Begin tracking
tracking.start()
