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

## TODO  

* [x] Make an extendable Events API for users who may wish to perform their own tasks


