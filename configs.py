"""
author: hexsix
date: 2022/08/17
description: configs
"""

import json
import os


class Configs(object):
    def __init__(self):
        if os.path.exists('configs.json'):  # self-host
            CONFIGS = json.load(open('configs.json', 'r', encoding='utf8'))
            self.debug = CONFIGS['debug']
            self.channel_id = CONFIGS['channel_id']
            self.chat_id = CONFIGS['chat_id']
            self.redis_url = CONFIGS['redis_url']
            self.rss_url = CONFIGS['rss_url']
            self.score_threshold = CONFIGS['score_threshold']
            self.tg_token = CONFIGS['bot_token']
            self.use_proxies = CONFIGS['use_proxies']
            self.proxies = CONFIGS['proxies']
        else:   # heroku
            self.debug = bool(os.environ['DEBUG'])
            self.channel_id = os.environ['CHANNEL_ID']
            self.chat_id = os.environ['CHAT_ID']
            self.redis_url = os.environ['REDIS_URL']
            self.rss_url = os.environ['RSS_URL']
            self.score_threshold = int(os.environ['SCORE_THRESHOLD'])
            self.tg_token = os.environ['TG_TOKEN']
            self.use_proxies = False
            self.proxies = {}
    
    def __str__(self):
        return f"\ndebug mode: {'on' if self.debug else 'off'}\n" \
               f"score threshold: {self.score_threshold}\n" \
               f"redis url: {self.redis_url}\n" \
               f"rss url: {self.rss_url}\n" \
               f"telegram channel id: {self.channel_id}\n" \
               f"telegram chat id: {self.chat_id}\n" \
               f"telegram token: ******\n" \
               f"use proxies: {self.use_proxies}\n" \
               f"proxies: {json.dumps(self.proxies)}\n"


configs = Configs()


if __name__ == '__main__':
    print(configs)
