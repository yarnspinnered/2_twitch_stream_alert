import requests, os, sys
import slacker
import pandas as pd
from datetime import datetime
import time
import sched
import psutil
import twitch_tracker

#api keys stored at cfg_loc.csv
def csv_to_dict(cfg_loc, api_name):
    total_dict = pd.read_csv(cfg_loc)
    total_dict.index = total_dict["site"]
    final = total_dict.loc[(api_name)].to_dict()
    return final

# Expects a list of streamers in followed_streamers.txt in same directory as TwitchAlert
def get_followed_streamers():
    result = {}
    f = open(os.getcwd() + "\\followed_streamers.txt")
    for line in f:
        result[line.rstrip().lower()] = False
    return result

def time_passed(time):
        start_time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
        now = datetime.utcnow()
        return str(now - start_time)

#stream object to contain relevant info about a stream
class stream():
    def __init__(self, stream_dict):
        self.viewers = stream_dict["viewers"]
        channel_dict = stream_dict["channel"]
        self.game = channel_dict["game"]
        self.streamer = channel_dict["name"]
        self.language = channel_dict["language"]
        self.logo = channel_dict["logo"]
        self.online_time = time_passed(stream_dict["created_at"])
        self.url = channel_dict["url"]
        
    def __repr__(self):
        return str([self.game, self.language, self.streamer, self.logo, self.online_time])

        
def ping_streams():
    followed = twitch_tracker.stream_status
    sched_obj = twitch_tracker.sched_obj
    bot = twitch_tracker.slack_bot
    url = 'https://api.twitch.tv/kraken/streams?channel=' + (",".join(followed.keys()))
    response = requests.get(url)
    current_streams = []
    for stream_dict in response.json()["streams"]:
        current_streams.append(stream(stream_dict))
    # loop to check any new streams that appeared since last check
    for strim in current_streams:
        if strim.streamer in followed.keys():
            if followed[strim.streamer] == False:
                bot.chat.post_message("#twitchstreams", strim.streamer + " playing " + strim.game + " at " + strim.url + " for " + strim.online_time)
                followed[strim.streamer] = True
    # loop to change the status of any previously online streams that went offline
    for followed_streamer in followed.keys():
        if followed_streamer not in [x.streamer for x in current_streams]:
            followed[followed_streamer] = False
    #start a new delayed run of ping_streams
    sched_obj.enter(60, 2, ping_streams, ())
    sched_obj.run()
    return followed

def main(args):
    slack_up = False
    while not slack_up:
        list_of_proc = [psutil.Process(p).name() for p in psutil.pids()]
        slack_up = "slack.exe" in list_of_proc
        time.sleep(10)
    twitch_tracker.stream_status = get_followed_streamers()
    bot_key = csv_to_dict("C:\\Users\\User\\Documents\\PythonScripts\\config.csv", "slack")["key"]
    twitch_tracker.slack_bot = slacker.Slacker(bot_key)
    twitch_tracker.sched_obj = sched.scheduler(time.time, time.sleep)
    ping_streams()


if __name__ == "__main__":
    main(sys.argv)
    
