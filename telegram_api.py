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
from yandere import Post


logger = logging.getLogger('telegram_api')


class Bot(object):

    def __init__(self, token=configs.tg_token):
        if configs.use_proxies:
            pp = telegram.utils.request.Request(proxy_url=configs.proxies['https://'])
            self._b = telegram.Bot(token=token, request=pp)
        else:
            self._b = telegram.Bot(token=token)
    
    def send_message(self, text: str, chat_id: str, reply_to_message_id: str = None) -> int:
        response = self._b.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id
        )
        return response.message_id

    def send_document(self, document, filename: str,
                      chat_id: str, reply_to_message_id: str = None) -> int:
        time.sleep(6)
        response = self._b.send_document(
            chat_id=chat_id,
            document=document,
            reply_to_message_id=reply_to_message_id,
            filename=filename
        )
        return response.message_id

    def send_photo(self, photo: str, caption: str,
                   chat_id: str, reply_to_message_id: str = None) -> int:
        time.sleep(6)
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
        time.sleep(6)
        if len(photos) < 2:
            return
        media = [self.input_media_photo(photos[0], caption)] + \
                [self.input_media_photo(photo) for photo in photos[1:]]
        response = self._b.send_media_group(chat_id=chat_id,
                                            media=media,
                                            disable_notification=True,
                                            reply_to_message_id=reply_to_message_id)
        return response[0].message_id
    
    def get_message_id_in_discussion(self, forward_from_message_id: int):
        updates = None
        for retry in range(3):
            try:
                time.sleep(30)   # wait for telegram api update
                updates = self._b.get_updates()
            except Exception as e:
                logger.error(f'Failed to get updates: {e}')
            if updates:
                for update in updates:
                    try:
                        if update.message.forward_from_message_id == forward_from_message_id:
                            return update.message.message_id
                    except Exception as e:
                        logger.debug(f'Failed to parse update: {e}')
                        continue
        return -1

    def construct_caption(self, post: Post) -> str:
        caption = ''
        if post.author:
            caption += f'author: {post.author}\n'
        if post.chara:
            caption += f'character: {post.chara}\n'
        if post.source:
            caption += f'source: {post.source}\n'
        caption += f'https://yande.re/post/show/{post._id}'
        return caption

    def send(self, post: Post) -> bool:
        caption = self.construct_caption(post)
        if post.children:
            return self.send_group(post, caption)
        else:
            return self.send_single(post, caption)
    
    def send_group(self, post: Post, caption: str) -> bool:
        try:
            message_id = self.send_media_group(
                photos=([post.sample_url] + [child.sample_url for child in post.children])[:10],
                caption=caption,
                chat_id=configs.channel_id
            )
        except Exception as e:
            logger.error(f'send group faild: {e}')
            return False
        discussion_msg_id = self.get_message_id_in_discussion(message_id)
        if discussion_msg_id == -1:
            logger.error(f'get discussion message id failed.')
            return False
        st = 10
        while 1:
            photos = ([post.sample_url] + [child.sample_url for child in post.children])[st:st+10]
            if not photos:
                break
            try:
                self.send_media_group(
                    photos=photos,
                    caption=caption,
                    chat_id=configs.chat_id,
                    reply_to_message_id=discussion_msg_id
                )
            except Exception as e:
                logger.error(f'send group reply faild: {e}')
        self.send_reply_file(post, discussion_msg_id)
        for child in post.children:
            self.send_reply_file(child, discussion_msg_id)
        return True
    
    def send_single(self, post: Post, caption: str) -> bool:
        try:
            message_id = self.send_photo(
                photo=post.sample_url,
                caption=caption,
                chat_id=configs.channel_id
            )
        except Exception as e:
            logger.error(f'send photo faild: {e}')
            return False
        discussion_msg_id = self.get_message_id_in_discussion(message_id)
        if discussion_msg_id == -1:
            logger.error(f'get discussion message id failed.')
            return False
        self.send_reply_file(post, discussion_msg_id)
        return True

    def send_reply_file(self, post: Post, discussion_msg_id: int) -> bool:
        if configs.use_proxies:
            with httpx.Client(proxies=configs.proxies) as client:
                try:
                    response = client.get(post.file_url, timeout=10.0)
                except Exception as e:
                    logger.error(f'get document failed: {e}')
                    return False
        else:
            with httpx.Client() as client:
                try:
                    response = client.get(post.file_url, timeout=10.0)
                except Exception as e:
                    logger.error(f'get document failed: {e}')
                    return False
        try:
            self.send_document(
                document=response.content,
                chat_id=configs.chat_id,
                reply_to_message_id=discussion_msg_id,
                filename=f'{post._id}.{post.file_ext}'
            )
        except Exception as e:
            logger.error(f'send document failed: {e}')
            self.send_message(
                text=f'send {post._id}.{post.file_ext} failed.',
                chat_id=configs.chat_id,
                reply_to_message_id=discussion_msg_id
            )
            return False
        return True


bot = Bot()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
    logging.info(configs)
    
    # test send_photo
    _channel_msg_id = None
    # _channel_msg_id = bot.send_photo(photo="https://files.yande.re/sample/4616cac5d672d821abf7326bba2c498f/yande.re%201010879%20sample%20barbara_%28genshin_impact%29%20dress%20genshin_impact%20mochi_mochi052%20pantyhose%20skirt_lift.jpg", caption="test 13", chat_id=configs.channel_id)
    
    # test send_media_group
    # bot.send_media_group(
    #     photos=[
    #         "https://assets.yande.re/data/preview/4a/78/4a78eb95995dd81a5ddbb01508bc38c2.jpg",
    #         "https://assets.yande.re/data/preview/c5/c5/c5c56b7b4d69a14553bd47e326b77cb2.jpg"
    #     ], caption="test media group", chat_id=configs.channel_id)

    # test get_updates
    if not _channel_msg_id:
        _channel_msg_id = 1528
    _discussion_msg_id = bot.get_message_id_in_discussion(_channel_msg_id)
    logger.info(f'discussion msg id: {_discussion_msg_id}')
