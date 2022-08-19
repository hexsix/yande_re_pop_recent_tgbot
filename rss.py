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


logger = logging.getLogger('rss')


def download_rss(rss_url: str, use_proxies: bool, proxies: Dict) -> Dict:
    logger.info('Downloading RSS ...')
    rss_json = {}
    for retry in range(3):
        if retry > 0:
            logger.info(f'The {retry + 1}th attempt, 3 attempts in total.')
        try:
            if use_proxies:
                with httpx.Client(proxies=proxies) as client:
                    response = client.get(rss_url, timeout=10.0)
                rss_json = feedparser.parse(response.text)
            else:
                with httpx.Client() as client:
                    response = client.get(rss_url, timeout=10.0)
                rss_json = feedparser.parse(response.text)
            if rss_json:
                break
        except Exception as e:
            if retry + 1 < 3:
                logger.warning(f'Failed, next attempt will start soon: {e}')
                time.sleep(6)
            else:
                logger.error(f'Failed to download RSS: {e}')
    if not rss_json:
        raise Exception('Failed to download RSS.')
    return rss_json


def parse_rss(rss_json: Dict) -> List[str]:
    logger.info('Parsing RSS ...')
    post_id_list = []
    for entry in rss_json['entries']:
        try:
            post_url = entry['link']
            post_id = post_url.split('/')[-1]
            post_id_list.append(post_id)
        except Exception as e:
            logger.warning(f'Parsing RSS Failed: {e}')
            logger.debug(f'Error rss json part: {entry}')
            continue
    logger.info(f"Parse RSS End. {len(post_id_list)}/{len(rss_json['entries'])} Succeed.")
    return post_id_list


def get_post_id_list(
    rss_url: str = configs.rss_url,
    use_proxies: bool = configs.use_proxies,
    proxies: Dict = configs.proxies
) -> List[str]:
    logger.info(f'\tRSS Section:')
    try:
        rss_json = download_rss(rss_url, use_proxies, proxies)
        logger.info('Succeed to download RSS.')
    except Exception as e:
        logger.error(f'Download RSS error, {e}')
        return []
    try:
        post_id_list = parse_rss(rss_json)
        logger.info(f'Post id list length: {len(post_id_list)}, list: {post_id_list}')
        return post_id_list
    except Exception as e:
        logger.error(f'Parse RSS error, {e}')
        return []


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
    logger.info(configs)
    _post_id_list = get_post_id_list()
