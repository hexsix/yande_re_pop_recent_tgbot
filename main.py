"""
author: hexsix
date: 2021/11/22
description: 写给 heroku 云服务
"""

import os
import re
from typing import Any, Dict, List

import feedparser


def download() -> Any:
    print('Downloading RSS ...')
    for retry in range(3):
        print(f'The {retry + 1}th attempt, 3 attempts in total.')
        try:
            with httpx.Client() as client:
                response = client.get(os.environ['RSS_URL'], timeout=10.0)
            rss_json = feedparser.parse(response.text)
        except:
            print('Failed to download RSS, the next attempt will start in 6 seconds.')
            time.sleep(6)
    if not rss_json:
        raise Exception('Failed to download RSS.')
    print('Succeed to download RSS.')
    return rss_json


def parse(rss_json: Dict) -> List[Dict[str, Any]]:
    print('Parsing RSS ...')
    items = []
    for entry in rss_json['entries']:
        try:
            item = dict()
            item['post_url'] = entry['link']
            item['post_id'] = item['post_url'].split('/')[-1]
            item['score'] = int(re.search(r'Score:\d*', entry['description']).group().split(':')[-1])
            item['sample'] = re.search(r'https://files.yande.re/sample/[^"]*', entry['description']).group()
            items.append(item)
        except:
            continue
    print(f'Parse RSS End. {len(items)}/{len(rss_json['entries'])} Succeed.')
    return items


def filter(item: Dict[str, Any]) -> bool:
    return True


def send(photo: str, caption: str) -> bool:
    target = f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendPhoto"
    params = {
        'chat_id': os.environ['CHAT_ID'],
        'photo': photo,
        'caption': caption
    }
    for retry in range(3):
        print(f'The {retry + 1}th attempt, 3 attempts in total.')
        try:
            with httpx.Client() as client:
                response = client.post(target, params=params)
            print(f'Telegram api returns {response.json()}')
            if response.json()['ok']:
                print(f'Succeed to send {caption}.')
                return True
        except:
            pass
        print(f'Failed to send {caption}, the next attempt will start in 6 seconds.')
        time.sleep(6)
    print(f'Failed to send {caption}.')
    return False


def main():
    print('============ App Start ============')
    rss_json = download()
    items = parse(rss_json)
    count = 0
    for item in items:
        if filter(item):
            continue
        if send(item):
            count += 1
    print(f'{count}/{len(items)} Succeed.')
    print('============ App End ============')


if __name__ == '__main__':
    main()
