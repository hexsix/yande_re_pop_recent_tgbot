"""
author: hexsix
date: 2021/11/22
description: 写给 heroku 云服务
"""

import os
import re
import time
from typing import Any, Dict, List

import httpx
import feedparser
import redis


REDIS = redis.from_url(os.environ['REDIS_URL'])


def download() -> Any:
    print('Downloading RSS ...')
    for retry in range(3):
        print(f'The {retry + 1}th attempt, 3 attempts in total.')
        try:
            with httpx.Client() as client:
                response = client.get(os.environ['RSS_URL'], timeout=10.0)
            rss_json = feedparser.parse(response.text)
            if rss_json:
                break
        except:
            print('Failed to download RSS, the next attempt will start in 6 seconds.')
            time.sleep(6)
    if not rss_json:
        raise Exception('Failed to download RSS.')
    print('Succeed to download RSS.\n')
    return rss_json


def parse(rss_json: Dict) -> List[Dict[str, Any]]:
    print('Parsing RSS ...')
    items = []
    for entry in rss_json['entries']:
        try:
            item = dict()
            item['post_url'] = entry['link']
            item['post_id'] = item['post_url'].split('/')[-1]
            item['score'] = int(
                re.search(r'Score:\d*', entry['description']).group().split(':')[-1])
            item['sample'] = re.search(
                r'https://files.yande.re/sample/[^"]*', entry['description']).group()
            items.append(item)
        except Exception as e:
            print(f'Exception: {e}')
            continue
    print(f"Parse RSS End. {len(items)}/{len(rss_json['entries'])} Succeed.\n")
    return items


def filter(item: Dict[str, Any]) -> bool:
    if item['score'] < int(os.environ['SCORE_THRESHOLD']):
        return True
    if REDIS.exists(item['post_id']):
        return True
    return False


def send(photo: str, caption: str) -> bool:
    print(f'Send pid: {caption} ...')
    target = f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendPhoto"
    params = {
        'chat_id': os.environ['CHAT_ID'],
        'photo': photo,
        'caption': caption
    }
    try:
        with httpx.Client() as client:
            response = client.post(target, params=params)
        print(f'Telegram api returns {response.json()}')
        if response.json()['ok']:
            print(f'Succeed to send {caption}.')
            return True
        else:
            print(f'Telegram api returns {response.json()}')
            print(f'photo: {photo}, caption: {caption}')
    except Exception as e:
        print(f'Exception: {e}')
        pass
    print(f'Failed to send {caption}.\n')
    return False


def redis_set(post_id: str) -> bool:
    for retry in range(5):
        print(f'The {retry + 1}th attempt to set redis, 5 attempts in total.')
        try:
            if REDIS.set(post_id, 'sent', ex=2678400):  # expire after a month
                print(f'Succeed to set redis {post_id}.\n')
                return True
        except:
            print('Failed to set redis, the next attempt will start in 6 seconds.')
            time.sleep(6)
    print(f'Failed to set redis, {post_id} may be sent twice.\n')
    return False


def main():
    print('============ App Start ============')
    rss_json = download()
    items = parse(rss_json)
    filtered_items = [item for item in items if not filter(item)]
    print(f'{len(filtered_items)}/{len(items)} filtered by already sent / score threshold.\n')
    count = 0
    for item in filtered_items:
        if send(item['sample'], item['post_url']):
            redis_set(item['post_id'])
            count += 1
    print(f'{count}/{len(filtered_items)} Succeed.')
    print('============ App End ============')


if __name__ == '__main__':
    main()
