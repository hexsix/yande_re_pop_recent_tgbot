"""
author: hexsix
date: 2022/08/17
description: yande.re api request
"""

import logging
import time

import httpx

from configs import configs


logger = logging.getLogger('yandere_api')


def api(target: str) -> str:
    logger.info(f'yande.re api request: {target}')
    response = ''
    for retry in range(3):
        logger.info(f'The {retry + 1}th attempt, 3 attempts in total.')
        try:
            if configs.use_proxies:
                with httpx.Client(proxies=configs.proxies) as client:
                    response = client.get(target, timeout=10.0)
            else:
                with httpx.Client() as client:
                    response = client.get(target, timeout=10.0)
            if response:
                break
        except Exception as e:
            if retry + 1 < 3:
                logger.info(f'Failed, next attempt will start soon: {e}')
                time.sleep(6)
            else:
                logger.info(f'Failed: {e}')
    if not response:
        raise Exception('Failed to request api.')
    logger.info('Succeed to request api.\n')
    return response.text


def api_post(id: str) -> str:
    return api(f'https://yande.re/post.xml?tags=id:{id}')


def api_parent(id: str, holds: bool = False) -> str:
    if holds:
        return api(f'https://yande.re/post.xml?tags=parent:{id}%20holds:true')
    else:
        return api(f'https://yande.re/post.xml?tags=parent:{id}')


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.info(configs)
    # _response_text = api_parent("916812")
    # with open('sample_api_parent_result.xml', 'w', encoding='utf8') as f:
    #     f.write(_response_text)
    _response_text = api_post("916812")
    with open('sample_api_post_result.xml', 'w', encoding='utf8') as f:
        f.write(_response_text)
