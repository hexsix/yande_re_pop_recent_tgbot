"""
author: hexsix
date: 2022/08/18
description: request telegram api
"""

import logging
import time
from typing import List

import httpx
import telegram

from configs import configs


logger = logging.getLogger('telegram_api')


class Bot(object):

    def __init__(self, token=configs.tg_token):
        if configs.use_proxies:
            pp = telegram.utils.request.Request(proxy_url=configs.proxies['https://'])
            self._b = telegram.Bot(token=token, request=pp)
        else:
            self._b = telegram.Bot(token=token)

    def send_photo(self, photo: str, caption: str,
                   chat_id: str, reply_to_message_id: str = None) -> int:
        response = self._b.send_photo(chat_id=chat_id,
                                      photo=photo,
                                      caption=caption,
                                      disable_notification=True,
                                      reply_to_message_id=reply_to_message_id)
        return response.message_id
    
    def input_media_photo(self, media: str, caption: str = None):
        if caption:
            return telegram.InputMediaPhoto(media, caption)
        else:
            return telegram.InputMediaPhoto(media)
    
    def send_media_group(self, photos: List[str], caption: str,
                         chat_id: str, reply_to_message_id: str = None) -> int:
        if len(photos) < 2:
            return
        media = [self.input_media_photo(photos[0], caption)] + \
                [self.input_media_photo(photo) for photo in photos[1:]]
        response = self._b.send_media_group(chat_id=chat_id,
                                            media=media,
                                            disable_notification=True,
                                            reply_to_message_id=reply_to_message_id)
        return response.message_id
    
    def get_message_id_in_discussion(self, forward_from_message_id: int):
        time.sleep(6)   # wait for telegram api update
        updates = None
        try:
            updates = self._b.get_updates()
        except Exception as e:
            logging.error(f'Failed to get updates: {e}')
        if updates:
            for update in updates:
                try:
                    if update.message.forward_from_message_id == forward_from_message_id:
                        return update.message.message_id
                except Exception as e:
                    logging.error(f'Failed to parse update: {e}')


bot = Bot()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.info(configs)
    
    # test send_photo
    _channel_msg_id = bot.send_photo(photo="https://files.yande.re/sample/4616cac5d672d821abf7326bba2c498f/yande.re%201010879%20sample%20barbara_%28genshin_impact%29%20dress%20genshin_impact%20mochi_mochi052%20pantyhose%20skirt_lift.jpg", caption="test 13", chat_id=configs.channel_id)
    
    # test send_media_group
    # bot.send_media_group(
    #     photos=[
    #         "https://assets.yande.re/data/preview/4a/78/4a78eb95995dd81a5ddbb01508bc38c2.jpg",
    #         "https://assets.yande.re/data/preview/c5/c5/c5c56b7b4d69a14553bd47e326b77cb2.jpg"
    #     ], caption="test media group", chat_id=configs.channel_id)

    # test get_updates
    if not _channel_msg_id:
        _channel_msg_id = 1424
    _discussion_msg_id = bot.get_message_id_in_discussion(_channel_msg_id)
    logging.info(f'discussion msg id: {_discussion_msg_id}')
