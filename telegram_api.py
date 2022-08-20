"""
author: hexsix
date: 2022/08/18
description: request telegram api
"""

import logging
import os
import time
from typing import List
from urllib.parse import urlparse

import httpx
import telegram

from configs import configs
from yandere import Post


logger = logging.getLogger('telegram_api')


class Bot(object):

    def __init__(self, token=configs.tg_token):
        if configs.use_proxies:
            pp = telegram.utils.request.Request(
                proxy_url=configs.proxies['https://'])
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
                                      parse_mode=telegram.constants.PARSEMODE_MARKDOWN_V2,
                                      reply_to_message_id=reply_to_message_id)
        return response.message_id

    def send_media_group(self, photos: List[str], caption: str,
                         chat_id: str, reply_to_message_id: str = None) -> int:
        time.sleep(6)
        if len(photos) < 2:
            return
        media = [telegram.InputMediaPhoto(media=photos[0], caption=caption, parse_mode=telegram.constants.PARSEMODE_MARKDOWN_V2)] + \
                [telegram.InputMediaPhoto(photo) for photo in photos[1:]]
        response = self._b.send_media_group(chat_id=chat_id,
                                            media=media,
                                            disable_notification=True,
                                            reply_to_message_id=reply_to_message_id)
        return response[0].message_id

    def get_message_id_in_discussion(self, forward_from_message_id: int):
        updates = None
        for retry in range(3):
            try:
                time.sleep(3)   # wait for telegram api update
                updates = self._b.get_updates(offset=-66)
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
        def escape(text: str) -> str:
            escape_chars = [
                '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for escape_char in escape_chars:
                text = text.replace(escape_char, '\\' + escape_char)
            return text
        caption = ''
        if post.author:
            caption += f'author: {post.author}\n'
        if post.chara:
            caption += f'character: {post.chara}\n'
        if post.source:
            # if 'pixiv' in post.source:
            #     # https://www.pixiv.net/artworks/100632821
            #     caption += f'source: [pixiv]({post.source})\n'
            # elif 'fantia' in post.source:
            #     # https://fantia.jp/posts/1090194
            #     caption += f'source: [fantia]({post.source})\n'
            # elif 'fanbox' in post.source:
            #     # https://www.fanbox.cc/@yuge/posts/4280870 https://haishiki.fanbox.cc/posts/3238509
            #     caption += f'source: [fanbox]({post.source})\n'
            # elif 'arca.live' in post.source:
            #     # https://arca.live/b/commission/56783762
            #     caption += f'source: [arca\\.live]({post.source})\n'
            # elif 'twitter' in post.source:
            #     # https://twitter.com/oponzponpon/status/1560624550932811776
            #     caption += f'source: [twitter]({post.source})\n'
            if 'pximg' in post.source:
                # https://i.pximg.net/img-original/img/2021/10/31/20/14/31/93820205_p0.png
                try:
                    pixiv_id = os.path.basename(post.source).split('_')[0]
                    caption += f'source: [{escape("www.pixiv.net")}]({escape("https://www.pixiv.net/artworks/" + pixiv_id)})\n'
                except Exception as e:
                    logger.error(
                        f'parse pximg url error, post.source: {post.source}, {e}')
                    caption += f'source: {escape(post.source)}\n'
            else:
                try:
                    urlparse_result = urlparse(post.source)
                    if urlparse_result.hostname:
                        caption += f'source: [{escape(urlparse_result.hostname)}]({post.source})\n'
                    else:
                        caption += f'source: {escape(post.source)}\n'
                except Exception as e:
                    caption += f'source: {escape(post.source)}\n'
        caption += escape(f'https://yande.re/post/show/{post._id}')
        return caption

    def send(self, post: Post) -> bool:
        caption = self.construct_caption(post)
        if post.has_children == 'true' and post.children:
            return self.send_group(post, caption)
        else:
            return self.send_single(post, caption)

    def send_group(self, post: Post, caption: str) -> bool:
        try:
            message_id = self.send_media_group(
                photos=([post.sample_url] +
                        [child.sample_url for child in post.children])[:10],
                caption=caption,
                chat_id=configs.channel_id
            )
        except Exception as e:
            logger.error(f'send group faild: {e}')
            return False
        discussion_msg_id = self.get_message_id_in_discussion(message_id)
        if discussion_msg_id == -1:
            logger.error(f'get discussion message id failed.')
            return True
        for st in range(10, 91, 10):
            photos = ([post.sample_url] +
                      [child.sample_url for child in post.children])[st:st+10]
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
            return True
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

    def get_post(_id):
        __post = Post(_id)
        __post.parse_self()
        __post.migrate_to_parent()
        __post.parse_children()
        return __post

    # fantia group
    _post = get_post('1009459')
    bot.send(_post)

    # pximg group
    _post = get_post('1011371')
    bot.send(_post)

    # text photo
    _post = get_post('1011311')
    bot.send(_post)

    # fanbox group
    _post = get_post('909228')
    bot.send(_post)

    # twitter photo
    _post = get_post('1011349')
    bot.send(_post)

    # www.route2.co.jp photo
    _post = get_post('1011680')
    bot.send(_post)
    
