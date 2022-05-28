import twitter


def get_user_following_ids(api: twitter.Api, name: str):
    next_cursor = -1
    ids = []
    while next_cursor != 0:
        # GetFriendIDsPaged
        # GetFollowerIDsPaged
        page = api.GetFriendsPaged(screen_name=name, cursor=next_cursor)
        next_cursor = page[0]
        ids.extend([x.id for x in page[2]])
    print(ids)


def get_current_mutuals_followers(api: twitter.Api):
    following = api.GetFriendIDs()
    followers = api.GetFollowerIDs()

    mutual_1 = [i for i in following if i in followers]
    mutual_2 = [f for f in followers if f in following]
    mutual_1.extend(mutual_2)

    mutuals = list(set(mutual_1))

    return {'mutuals': mutuals, 'followers': followers}


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    chunky = []

    for i in range(0, len(lst), n):
        chunky.append(lst[i:i + n])
    return chunky


def update_mutuals_list(api: twitter.Api, mutuals_list_id: int, old_mutuals_ids: list, unmutuals_ids: list,
                        new_mutuals_ids: list, deleted_ids: list, suspended_ids: list):
    mut = [i for i in new_mutuals_ids]
    real_unmut = [i for i in unmutuals_ids if i not in deleted_ids + suspended_ids]
    mut.extend([i for i in old_mutuals_ids if i not in real_unmut])

    mut_chunks = chunks(mut, 90)

    for i in mut_chunks:
        try:
            api.CreateListsMember(list_id=mutuals_list_id, user_id=i)
        except twitter.error.TwitterError as e:
            print(e.message[0]['message'])
