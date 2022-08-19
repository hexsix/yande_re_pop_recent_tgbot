"""
author: hexsix
date: 2021/11/22
description: 写给 heroku 云服务
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List

import httpx
import feedparser
import redis

from configs import configs
from rss import download_rss, parse_rss
from yandere_post import Post, get_parent, get_children
from telegram_api import bot
from redis_utils import redis_client


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('main')


def filter(post: Post) -> bool:
    if post is None:
        return True
    if not post.sample_url:
        return True
    if int(post.score) < int(configs.score_threshold):
        return True
    if redis_client.exists(post._id):
        return True
    return False


def main():
    logging.info('============ App Start ============')
    rss_json = download_rss()
    rss_results = parse_rss(rss_json)       # a list of yande.re post id
    # filtered_items = [item for item in items if not filter(item)]
    posts = [Post(post_id) for post_id in rss_results]
    logging.info(f'posts: {[post._id for post in posts]}')
    for post in posts:
        try:
            post.parse_post()
        except Exception as e:
            logging.error(f'parse post error: {e}')
    posts = [get_parent(post) for post in posts]
    filtered_posts = [post for post in posts if not filter(post)]
    logging.info(f'filtered posts: {[post._id for post in filtered_posts]}')
    logging.info(f'{len(filtered_posts)}/{len(posts)} filtered by already sent / score threshold.\n')
    posts = []
    for post in filtered_posts:
        posts.append(get_children(post))
        # posts.append(get_children(parse_tags(post)))
    count = 0
    for post in posts:
        logging.info(f'post: {post}')
        if bot.send(post):
            redis_client.set(post._id)
            count += 1
    logging.info(f'{count}/{len(filtered_posts)} Succeed.')
    logging.info('============ App End ============')


if __name__ == '__main__':
    main()
