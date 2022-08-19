"""
author: hexsix
date: 2022/08/19
description: yande.re post class, include api request
"""

import logging
import time
from typing import Dict
import xml.etree.ElementTree as ET

import httpx

from configs import configs


logger = logging.getLogger('yandere')


class Post(object):
    _id = ''
    source = ''
    tags = ''
    author = ''
    chara = ''
    score = 0
    file_size = 0
    file_ext = ''
    file_url = ''
    sample_file_size = 0
    sample_url = ''
    rating = ''
    has_children = ''
    parent_id = ''
    children = []
    use_proxies = False
    proxies = {}

    def __init__(self, _id: str,
                 use_proxies: bool = configs.use_proxies,
                 proxies: Dict = configs.proxies):
        self._id = _id
        self.use_proxies = use_proxies
        self.proxies = proxies

    def __eq__(self, other):
        if type(other) is type(self):
            return self._id == other._id
        else:
            return False

    def __hash__(self):
        return hash(self._id)

    def __str__(self):
        return f'{{id: {self._id}, source: {self.source}, author: {self.author}, chara: {self.chara}, score: {self.score}, file_url: {self.file_url}, sample_url: {self.sample_url}, has_children: {self.has_children}, parent_id: {self.parent_id}, children: {[c._id for c in self.children]}}}'

    def __repr__(self):
        return self.__str__()

    def api(self, target: str) -> str:
        time.sleep(0.6)
        response = ''
        for retry in range(3):
            if retry > 0:
                logger.info(f'The {retry + 1}th attempt, 3 attempts in total.')
            try:
                if self.use_proxies:
                    with httpx.Client(proxies=self.proxies) as client:
                        response = client.get(target, timeout=10.0)
                else:
                    with httpx.Client() as client:
                        response = client.get(target, timeout=10.0)
                if response:
                    break
            except Exception as e:
                if retry + 1 < 3:
                    logger.warning(f'Failed, next attempt will start soon: {e}')
                    time.sleep(6)
                else:
                    logger.info(f'Failed: {e}')
        if not response:
            raise Exception('Failed to request api.')
        return response.text

    def api_post(self, _id: str) -> str:
        return self.api(f'https://yande.re/post.xml?tags=id:{_id}')

    def api_parent(self, id: str, holds: bool = False) -> str:
        if holds:
            return self.api(f'https://yande.re/post.xml?tags=parent:{id}%20holds:true')
        else:
            return self.api(f'https://yande.re/post.xml?tags=parent:{id}')

    def api_tags(self, tag: str) -> str:
        # todo
        return self.api(f'https://yande.re/tags.xml?')

    def is_parent(self) -> bool:
        return not self.parent_id
    
    def migrate_to_parent(self):
        if self.is_parent():
            return
        self._id = self.parent_id
        self.parse_self()

    def parse_self(self):
        try:
            xml_str = self.api_post(self._id)
            logger.debug(xml_str)
        except Exception as e:
            logger.error(f'Parse post error: {self._id}, {e}')
            self._id = '0'
            return
        try:
            self.parse_post_xml(xml_str)
        except Exception as e:
            logger.error(f'Parse post error: {self._id}, {e}')
            self._id = '0'

    def parse_children(self):
        if self.has_children == 'false':
            return
        try:
            xml_str_0 = self.api_parent(self._id)
            logger.debug(xml_str_0)
            try:
                posts = self.parse_parent_xml(xml_str_0)
            except Exception as e:
                logger.error(f'Parse children error post id: {self._id}, {e}')
                self._id = '0'
                return
        except Exception as e:
            logger.error(f'Parse children error: {self._id}, {e}')
            self._id = '0'
            return
        try:
            xml_str_1 = self.api_parent(self._id, holds=True)
            logger.debug(xml_str_1)
            try:
                holds_posts = self.parse_parent_xml(xml_str_1)
            except Exception as e:
                logger.error(f'Parse children error post id: {self._id}, {e}')
                self._id = '0'
                return
        except Exception as e:
            logger.error(f'Parse children error: {self._id}, {e}')
            self._id = '0'
            return
        combined_posts_set = set(posts + holds_posts)
        for p in combined_posts_set:
            if p != self:
                self.children.append(p)

    def parse_tags(self):
        # todo
        pass

    def parse_post_xml(self, xml_str: str):
        posts = ET.fromstring(xml_str)
        try:
            assert len(posts) == 1
            assert posts.attrib['count'] == '1'
        except Exception as e:
            logger.error(f'xml parse error: {e}')
            return
        for post in posts:
            # post.attrib['id']
            self.tags = post.attrib['tags']
            self.score = post.attrib['score']
            self.file_size = post.attrib['file_size']
            self.file_ext = post.attrib['file_ext']
            self.file_url = post.attrib['file_url']
            self.sample_file_size = post.attrib['sample_file_size']
            self.sample_url = post.attrib['sample_url']
            self.source = post.attrib['source']
            self.rating = post.attrib['rating']
            self.has_children = post.attrib['has_children']
            self.parent_id = post.attrib['parent_id']
        return
    
    def parse_parent_xml(self, xml_str: str):
        posts = ET.fromstring(xml_str)
        ps = []
        for post in posts:
            p = Post(post.attrib['id'])
            p.tags = post.attrib['tags']
            p.score = post.attrib['score']
            p.file_size = post.attrib['file_size']
            p.file_ext = post.attrib['file_ext']
            p.file_url = post.attrib['file_url']
            p.sample_file_size = post.attrib['sample_file_size']
            p.sample_url = post.attrib['sample_url']
            p.source = post.attrib['source']
            p.rating = post.attrib['rating']
            p.has_children = post.attrib['has_children']
            p.parent_id = post.attrib['parent_id']
            ps.append(p)
        return ps
    
    def parse_tag_xml(self, xml_str: str) -> int:
        # 0: normal
        # 1: author
        # 2: chara
        # 3: work
        # todo
        return 0


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )
    _post = Post('993734')
    _post.parse_self()
    logger.info(f'post: {_post}')
    _post.migrate_to_parent()
    logger.info(f'parent: {_post}')
    _post.parse_children()
    logger.info(f'after parse children: {_post}, sample child: {_post.children[0]}')
