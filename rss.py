"""
author: hexsix
date: 2022/08/17
description: rss download and parse
"""

import logging
import time
from typing import Dict, List

import feedparser
import httpx

from configs import configs


logger = logging.getLogger('rss_downloader')


def download_rss() -> Dict:
    logger.info('Downloading RSS ...')
    rss_json = {}
    for retry in range(3):
        if retry > 0:
            logger.info(f'The {retry + 1}th attempt, 3 attempts in total.')
        try:
            if configs.use_proxies:
                with httpx.Client(proxies=configs.proxies) as client:
                    response = client.get(configs.rss_url, timeout=10.0)
                rss_json = feedparser.parse(response.text)
            else:
                with httpx.Client() as client:
                    response = client.get(configs.rss_url, timeout=10.0)
                rss_json = feedparser.parse(response.text)
            if rss_json:
                break
        except Exception as e:
            if retry + 1 < 3:
                logger.info(f'Failed, next attempt will start soon: {e}')
                time.sleep(6)
            else:
                logger.info(f'Failed: {e}')
    if not rss_json:
        raise Exception('Failed to download RSS.')
    logger.info('Succeed to download RSS.\n')
    return rss_json


def parse_rss(rss_json: Dict) -> List[str]:
    logger.info('Parsing RSS ...')
    items = []
    for entry in rss_json['entries']:
        try:
            post_url = entry['link']
            post_id = post_url.split('/')[-1]
            items.append(post_id)
        except Exception as e:
            logger.info(f'Parsing RSS Failed: {e}')
            continue
    logger.info(f"Parse RSS End. {len(items)}/{len(rss_json['entries'])} Succeed.\n")
    return items


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.info(configs)
    _rss_json = download_rss()
    logging.info(_rss_json['entries'][0]['link'])
    _list_of_post = parse_rss(_rss_json)
    logging.info(_list_of_post)
