"""
author: hexsix
date: 2022/08/17
description: yande.re post class
"""

import logging
from typing import List
import xml.etree.ElementTree as ET

from configs import configs
from yandere_api import api_post, api_parent


logger = logging.getLogger('yandere_post')


class Post(object):
    def __init__(self, _id: str):
        self._id = _id
        self.source = ''
        self.tags = ''
        self.author = ''
        self.chara = ''
        self.score = 0
        self.file_size = 0
        self.file_ext = ''
        self.file_url = ''
        self.sample_file_size = 0
        self.sample_url = ''
        self.rating = ''
        self.has_children = False
        self.parent_id = ""
        self.children = []

    def __eq__(self, other):
        if type(other) is type(self):
            return self._id == other._id
        else:
            return False

    def __hash__(self):
        return hash(self._id)
    
    def __str__(self):
        return f'{{id: {self._id}, source: {self.source}, author: {self.author}, chara: {self.chara}, score: {self.score}, file_url: {self.file_url}, sample_url: {self.sample_url}, has_children: {self.has_children}, parent_id: {self.parent_id}, children: {[c._id for c in self.children]}}}'
    
    def is_parent(self) -> bool:
        return not self.parent_id

    def parse_post(self):
        xml_str = api_post(self._id)
        self.parse_post_xml(xml_str)
    
    def parse_post_xml(self, xml_str: str):
        posts = ET.fromstring(xml_str)
        try:
            assert len(posts) == 1
            assert posts.attrib['count'] == '1'
        except Exception as e:
            logging.error(f'xml parse error: {e}')
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


def parse_tags(post: Post) -> Post:
    # todo: get author and character
    return post


def get_parent(post: Post) -> Post:
    if post is None or post.is_parent():
        return post
    parent_post = Post(post.parent_id)
    try:
        parent_post.parse_post()
    except Exception as e:
        logging.error(f'parse post error post id: {parent_post._id}, {e}')
        return None
    return get_parent(parent_post)


def get_children(post: Post) -> Post:
    if post.has_children == 'false':
        return post
    try:
        xml_str_0 = api_parent(post._id)
    except Exception as e:
        logging.error(f'parse post error post id: {post._id}, {e}')
        return post
    try:
        posts = parse_parent_xml(xml_str_0)
    except Exception as e:
        logging.error(f'parse post error post id: {post._id}, {e}')
        return post
    try:
        xml_str_1 = api_parent(id=post._id, holds=True)
    except Exception as e:
        logging.error(f'parse post error post id: {post._id}, {e}')
        return post
    try:
        holds_posts = parse_parent_xml(xml_str_1)
    except Exception as e:
        logging.error(f'parse post error post id: {post._id}, {e}')
        return post
    combined_posts_set = set(posts + holds_posts)
    for p in combined_posts_set:
        if p != post:
            post.children.append(p)
    return post


def parse_parent_xml(xml_str: str) -> List[Post]:
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


def rating_filter(posts: List[Post]) -> List[Post]:
    return [post for post in posts if post.score < configs.score_threshold]


if __name__ == '__main__':
    _post = Post('916812')
    _post.parse_post()
    print(_post)
    print()
    _post = get_children(_post)
    print(_post)

