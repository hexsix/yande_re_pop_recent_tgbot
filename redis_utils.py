"""
author: hexsix
date: 2022/08/17
description: redis key set/del, filter already sent yande.re post
"""

import logging
from typing import List

import redis

from configs import configs


logger = logging.getLogger('redis_utils')


class Redis(object):
    def __init__(self, redis_url: str):
        self._r = redis.from_url(redis_url)

    def set(self, key: str) -> bool:
        for retry in range(5):
            if retry != 0:
                logger.info(f'The {retry + 1}th attempt to set redis, 5 attempts in total.')
            try:
                if self._r.set(key, 'sent', ex=2678400):  # expire after a month
                    logger.info(f'Succeed to set redis {key}.\n')
                    return True
            except Exception as e:
                if retry + 1 < 3:
                    logger.info(f'Failed to set redis, next attempt will start soon: {e}')
                    time.sleep(6)
                else:
                    logger.info(f'Failed: {e}')
        logger.info(f'Failed to set redis, {key} may be sent twice.\n')
        return False

    def exists(self, key: str) -> bool:
        return self._r.exists(key)


redis_client = Redis(configs.redis_url)
