#!/usr/bin/python3
from datetime import datetime
from time import sleep
from configparser import ConfigParser
import pickle

import twitter
import schedule


config = ConfigParser()
config.read('config.ini')


# Logging in to twitter
twitter_config = config['credentials']

CONSUMER_KEY = twitter_config['consumer_key']
CONSUMER_SECRET = twitter_config['consumer_secret']
ACCESS_TOKEN_KEY = twitter_config['access_token_key']
ACCESS_TOKEN_SECRET = twitter_config['access_token_secret']

OUTPUT_NAME = twitter_config.get('output_name', fallback='saved.pk1')
LOG_NAME = twitter_config.get('log_name', fallback='follow_log.log')

lists_config = config['lists']
MUTUALS_LIST_ID = lists_config['mutuals_list_id']

twitter_api = twitter.Api(consumer_key=CONSUMER_KEY,
                          consumer_secret=CONSUMER_SECRET,
                          access_token_key=ACCESS_TOKEN_KEY,
                          access_token_secret=ACCESS_TOKEN_SECRET)

verified = twitter_api.VerifyCredentials()
if verified:
    print("Twitter verified as: " + str(verified))
else:
    print("Could not verify twitter user, check info")
    exit(1)


def get_current_mutuals_followers():
    following = twitter_api.GetFriendIDs()
    followers = twitter_api.GetFollowerIDs()

    mutual_1 = [i for i in following if i in followers]
    mutual_2 = [f for f in followers if f in following]
    mutual_1.extend(mutual_2)

    mutuals = list(set(mutual_1))

    return {'mutuals': mutuals, 'followers': followers}


def save_dict_to_file(dct):
    with open(OUTPUT_NAME, 'wb') as file:
        pickle.dump(dct, file, -1)


def load_dict_from_file():
    try:
        with open(OUTPUT_NAME, 'rb') as file:
            dct = pickle.load(file)
    except FileNotFoundError:
        with open(OUTPUT_NAME, 'wb') as file:
            dc = {'mutuals': [], 'followers': []}
            pickle.dump(dc, file, -1)
            return dc

    return dct


def main():
    print("yuh")
    current = get_current_mutuals_followers()
    old = load_dict_from_file()
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

    def update_mutuals_list(old_mutuals_ids, unmutuals_ids, new_mutuals_ids, deleted_ids, suspended_ids):
        mut = [i for i in new_mutuals_ids]
        real_unmut = [i for i in unmutuals_ids if i not in deleted_ids + suspended_ids]
        mut.extend([i for i in old_mutuals_ids if i not in real_unmut])

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            chunky = []

            for i in range(0, len(lst), n):
                chunky.append(lst[i:i + n])
            return chunky

        mut_chunks = chunks(mut, 90)

        for i in mut_chunks:
            try:
                twitter_api.CreateListsMember(list_id=MUTUALS_LIST_ID, user_id=i)
            except Exception as e:
                print(e.message[0]['message'])


    def parse_user_error(error):
        return e.message[0]['code']


    def already_parsed(_id, lists):
        for i in lists:
            for p in i:
                if p.id == _id:
                    return p

    for u in unfollow_ids:
        try:
            unfollows.append(twitter_api.GetUser(user_id=u))
        except twitter.error.TwitterError as e:
            error_code = parse_user_error(e)
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
                error_code = parse_user_error(e)
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
                error_code = parse_user_error(e)
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
            except twitter.error.TwitterError:
                error_code = parse_user_error(e)
                if error_code == 50:
                    deleted_users.append(_nf)
                elif error_code == 63:
                    suspended_users.append(_nf)
    if MUTUALS_LIST_ID:
        update_mutuals_list(old['mutuals'], unmutual_ids, new_mutual_ids, deleted_users, suspended_users)

    def gen_text(ls):
        screens = [i.screen_name for i in ls]
        names = [i.name for i in ls]
        txt = ', '.join('{{@{0}: {1}}}'.format(*t) for t in zip(screens, names))
        return str(txt)

    unfollow_text = gen_text(unfollows)
    unmutual_text = gen_text(unmutuals)
    new_mutual_text = gen_text(new_mutuals)
    new_follower_text = gen_text(new_followers)

    if unfollow_text or unmutual_text or new_mutual_text or new_follower_text:
        now = str(datetime.now().isoformat(' '))
        print("\nChanges detected at {}".format(now))

        with open(LOG_NAME, 'a') as file:
            file.write("{}:\n".format(now))
            if unfollow_text:
                file.write("Unfollowers:\n{}\n".format(unfollow_text))
            if unmutual_text:
                file.write("Unmutuals:\n{}\n".format(unmutual_text))
            if new_mutual_text:
                file.write("New mutuals:\n{}\n".format(new_mutual_text))
            if new_follower_text:
                file.write("New followers:\n{}\n".format(new_follower_text))
            file.write("\n\n")

    save_dict_to_file(current)
    print("aye")



if __name__ == '__main__':
    schedule.every(60).minutes.do(main)
    print('\nStarting..')
    main()
    while True:
        schedule.run_pending()
        sleep(30)
