import twitter


# Return a dict of mutuals and followers of a user
def get_user_mutuals_followers(api: twitter.Api, user_id: str = None):
    following = api.GetFriendIDs(user_id=user_id)
    followers = api.GetFollowerIDs(user_id=user_id)

    mutual_1 = [i for i in following if i in followers]
    mutual_2 = [f for f in followers if f in following]
    mutual_1.extend(mutual_2)

    # set() makes sure values are never repeater
    mutuals = list(set(mutual_1))

    return {'mutuals': mutuals, 'followers': followers}


# Split some list into chunks of smaller lists of size n
def chunks(lst: list, n: int):
    chunky = []

    for i in range(0, len(lst), n):
        chunky.append(lst[i:i + n])
    return chunky


# Update the Twitter.List of a user's mutuals
def update_mutuals_list(api: twitter.Api, mutuals_list_id: int, old_mutuals_ids: list, unmutuals_ids: list,
                        new_mutuals_ids: list, deleted_ids: list, suspended_ids: list):
    mut = [i for i in new_mutuals_ids]
    real_unmut = [i for i in unmutuals_ids if i not in deleted_ids + suspended_ids]
    mut.extend([i for i in old_mutuals_ids if i not in real_unmut])

    # Can only add ~90 users at once or something? I don't remember
    mut_chunks = chunks(mut, 90)

    for i in mut_chunks:
        try:
            api.CreateListsMember(list_id=mutuals_list_id, user_id=i)
        except twitter.error.TwitterError as e:
            print(e.message[0]['message'])
