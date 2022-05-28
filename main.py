#!/usr/bin/python3
from datetime import datetime
from time import sleep

import schedule
import twitter

import file_io
import followers

CONFIG_FILENAME = "config.json"
config = file_io.get_config(CONFIG_FILENAME)

# Logging in to twitter
twitter_config = config['credentials']
CONSUMER_KEY = twitter_config['consumer_key']
CONSUMER_SECRET = twitter_config['consumer_secret']
ACCESS_TOKEN_KEY = twitter_config['access_token_key']
ACCESS_TOKEN_SECRET = twitter_config['access_token_secret']

lists_config = config['lists']
MUTUALS_LIST_ID = lists_config['mutuals_list_id']

schdeule_config = config['schedule']
OUTPUT_NAME = schdeule_config.get('output_name', 'saved_following.json')
LOG_NAME = schdeule_config.get('log_name', 'follow_log.log')
RUN_EVERY = schdeule_config.get('run_every', 3600)
SLEEP_TIME = schdeule_config.get('sleep_time', 30)

twitter_api = twitter.Api(consumer_key=CONSUMER_KEY,
                          consumer_secret=CONSUMER_SECRET,
                          access_token_key=ACCESS_TOKEN_KEY,
                          access_token_secret=ACCESS_TOKEN_SECRET)

verified = twitter_api.VerifyCredentials()
if verified:
    print("Twitter verified as: \n" + str(verified))
else:
    print("Could not verify twitter user, check info")
    exit(1)


def parse_twitter_user_error_code(error):
    return error.message[0]['code']


def already_parsed(_id, lists):
    for i in lists:
        for p in i:
            if p.id == _id:
                return p


def gen_text(users: list) -> str:
    screens = [i.screen_name for i in users]
    names = [i.name for i in users]
    txt = ', '.join(f"{{@{t[0]}: {t[1]}}}" for t in zip(screens, names))
    return str(txt)


def main():
    print("Running main")
    current = followers.get_current_mutuals_followers(twitter_api)
    old = file_io.load_follower_dict(OUTPUT_NAME)

    # {screen_name: name}
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

    for u in unfollow_ids:
        try:
            unfollows.append(twitter_api.GetUser(user_id=u))
        except twitter.error.TwitterError as e:
            error_code = parse_twitter_user_error_code(e)
            if error_code == 50:
                deleted_users.append(u)
            elif error_code == 63:
                suspended_users.append(u)

    for un in unmutual_ids:
        ap = already_parsed(un, [unfollows])
        if ap:
            unmutuals.append(ap)
        else:
            try:
                unmutuals.append(twitter_api.GetUser(user_id=un))
            except twitter.error.TwitterError as e:
                error_code = parse_twitter_user_error_code(e)
                if error_code == 50:
                    deleted_users.append(un)
                elif error_code == 63:
                    suspended_users.append(un)

    for _nm in new_mutual_ids:
        ap = already_parsed(_nm, [unfollows, unmutuals])
        if ap:
            new_mutuals.append(ap)
        else:
            try:
                new_mutuals.append(twitter_api.GetUser(user_id=_nm))
            except twitter.error.TwitterError as e:
                error_code = parse_twitter_user_error_code(e)
                if error_code == 50:
                    deleted_users.append(_nm)
                elif error_code == 63:
                    suspended_users.append(_nm)

    for _nf in new_follower_ids:
        ap = already_parsed(_nf, [unfollows, unmutuals, new_mutuals])
        if ap:
            new_followers.append(ap)
        else:
            try:
                new_followers.append(twitter_api.GetUser(user_id=_nf))
            except twitter.error.TwitterError as e:
                error_code = parse_twitter_user_error_code(e)
                if error_code == 50:
                    deleted_users.append(_nf)
                elif error_code == 63:
                    suspended_users.append(_nf)

    if MUTUALS_LIST_ID:
        followers.update_mutuals_list(twitter_api, MUTUALS_LIST_ID, old['mutuals'], unmutual_ids, new_mutual_ids,
                                      deleted_users, suspended_users)

    unfollow_text = gen_text(unfollows)
    unmutual_text = gen_text(unmutuals)
    new_mutual_text = gen_text(new_mutuals)
    new_follower_text = gen_text(new_followers)

    if unfollow_text or unmutual_text or new_mutual_text or new_follower_text:
        now = str(datetime.now().isoformat(' '))
        print(f"\nChanges detected at {now}")

        with open(LOG_NAME, 'a', encoding="utf-8") as file:
            file.write(f"{now}:\n")
            if unfollow_text:
                file.write(f"Unfollowers:\n{unfollow_text}\n")
            if unmutual_text:
                file.write(f"Unmutuals:\n{unmutual_text}\n")
            if new_mutual_text:
                file.write(f"New mutuals:\n{new_mutual_text}\n")
            if new_follower_text:
                file.write(f"New followers:\n{new_follower_text}\n")
            file.write("\n\n")

    file_io.save_dict_to_file(current, OUTPUT_NAME)
    print("Completed main")


if __name__ == '__main__':
    print('\nStarting program...')
    main()
    if RUN_EVERY > 0:
        schedule.every(RUN_EVERY).seconds.do(main)
        while True:
            schedule.run_pending()
            sleep(SLEEP_TIME)
    print("Program done!")
