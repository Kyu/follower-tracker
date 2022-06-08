# About
This is a Twitter bot that checks for your new followers and logs changes, using the twitter Api

## Usage
- Rename config-example.json to config.json
- Fill out your Twitter api credentials, as well as other optional values
- Run main.py 
- You can use the code in main.py to see how you can extend this project 
to do your own thing with the events provided in `events.py`. Events are emitted in `tracking.py`.  
  

## Requirements
Install using pip:  
- python-twitter: https://github.com/bear/python-twitter  
- schedule: https://github.com/dbader/schedule  
- event-bus: https://github.com/seanpar203/event-bus


## Config  

Config options are explained in the `_comment`
```json
{ 
  "credentials": {
    "_comment": "These keys are all found in the twitter developer dashboard: ",
    "_comment2": "https://developer.twitter.com/en/portal/dashboard",
    "consumer_key": "TWITTER_API_KEY",
    "consumer_secret": "TWITTER_API_SECRET",
    "access_token_key": "1486145328-TWITTER_ACCESS_TOKEN_KEY",
    "access_token_secret": "TWITTER_ACCESS_TOKEN_SECRET"
  },
  "schedule": {
    "_comment": "run_every: time between each user query in seconds. sleep_time: loop sleep time in seconds",
    "_comment2": "output_name: file to output user following, for comparison purposes",
    "_comment3": "log_name: file to log changes in following",
    "run_every": 0,
    "sleep_time": 30,
    "output_name": "saved_following.json",
    "log_name": "follow_log.log"
  },
  "tracked_users": {
    "_comment": "self: a boolean of whether to track script owner or not.",
    "_comment2": "others: A list of others to track. Keys can either be @UserName or just the user ID.",
    "_comment3": "Usernames MUST begin with '@'",
    "self": true,
    "others": [
      "@jack",
      1234567890
    ]
  }
}


```


## TODO  

* [x] Make an extendable Events API for users who may wish to perform their own tasks


