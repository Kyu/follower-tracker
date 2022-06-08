import twitter


# Event at the beginning of the script. Contains config data as well as Twitter API object
class StartMainEvent:
    EVENT_NAME = "start_main_event"

    def __init__(self, config_file_name: str, config: dict, twitter_api: twitter.Api):
        self.config_file_name = config_file_name
        self.config = config
        self.twitter_api = twitter_api


# Event just before the script exits. Contains no data
class FinishMainEvent(StartMainEvent):
    EVENT_NAME = "end_main_event"


# Event before any new queries happen. Contains no data
# TODO event data?
class StartQueryEvent:
    EVENT_NAME = "start_querying_all_users_event"


# Event after a single users data is queried. Contains data of that user's current of followers and mutuals
class TwitterUserFollowingQuery:
    EVENT_NAME = "twitter_user_following_query_event"

    def __init__(self, data: dict):
        self.current = data.get("current")
        self.user_id = data.get("user_id")
        self.screen_name = data.get("screen_name")


# Event after all users data is queried. Contains a list of `TwitterUserFollowingQuery`
class FinishAllQueryEvents:
    EVENT_NAME = "bulk_twitter_user_following_query_event"

    def __init__(self, events: list[TwitterUserFollowingQuery]):
        self.events = events
