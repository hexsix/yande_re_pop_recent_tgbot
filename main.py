"""
author: hexsix
date: 2021/11/22
description: 
"""

import logging

from configs import configs
from rss import get_post_id_list
from yandere import Post
from telegram_api import bot
from redis_utils import redis_client


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if configs.debug else logging.DEBUG
)
logger = logging.getLogger('main')


def filter(post: Post, score_filter_enable: bool) -> bool:
    if post is None:
        return True
    if post._id == '0':
        logging.info(f'filter by post id: {post}')
        return True
    if not post.sample_url:
        logging.info(f'filter by post sample url: {post}')
        return True
    if score_filter_enable and int(post.score) < int(configs.score_threshold):
        logging.info(f'filter by post score: {post}')
        return True
    if redis_client.exists(post._id):
        logging.info(f'filter by post already sent: {post}')
        return True
    return False


def main():
    logger.info('============ App Start ============')
    post_id_list = get_post_id_list()

    for i, post_id in enumerate(post_id_list):
        logger.info(f'{i}/{len(post_id_list)}')
        post = Post(post_id)

        post.parse_self()
        logger.debug(f'post: {post}')
        if filter(post=post, score_filter_enable=True):
            continue

        post.migrate_to_parent()
        logger.debug(f'post after migrate_to_parent(): {post}')
        if filter(post=post, score_filter_enable=False):
            continue

        post.parse_tags()
        logger.debug(f'post after parse_tags(): {post}')
        if filter(post=post, score_filter_enable=False):
            continue

        post.parse_children()
        logger.debug(f'post after parse_children(): {post}')
        if filter(post=post, score_filter_enable=False):
            continue
        
        logger.info(f'post: {post}')

        if bot.send(post):
            redis_client.set(post._id)
            for child in post.children:
                redis_client.set(child._id)
        
    logger.info('============ App End ============')


if __name__ == '__main__':
    main()
