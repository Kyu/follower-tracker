# About
This is a twitter bot that checks for new followers and logs changes

## Usage
- Rename config-example.ini to config.ini
- Fill out twitter credentials
- Run main.py


#### Using pm2
- Download [PM2 Process manager](https://pm2.keymetrics.io/)
- `pm2 start main.py --interpreter python3 --interpreter-args "-u" --name "{NAME}"`
