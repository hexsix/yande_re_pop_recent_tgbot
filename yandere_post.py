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
    id: str
    src: str
    tags: str
    author: str
    chara: str
    score: int
    file_size: int
    file_ext: str
    file_url: str
    sample_file_size: int
    sample_url: str
    rating: str
    has_children: bool
    parent_id: str
    children: List[Post]

    def __init__(self, id: str):
        self.id = id
        self.parse_post()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.id == other.id
        else:
            return False

    def __hash__(self):
        return hash(self.id)
    
    def is_parent(self) -> bool:
        return not self.parent_id
    
    def get_parent(self) -> Post:
        if self.is_parent():
            return self
        parent_post = Post(self.parent_id)
        return self.get_parent(parent_post)

    def parse_post(self):
        xml_str = api_post(id)
        parse_post_xml(xml_str)
        return

    def parse_children(self):
        self.children = []
        xml_str_0 = api_parent(post.parent_id)
        posts = parse_parent_xml(xml_str_0)
        xml_str_1 = api_parent(id=post.parent_id, holds=True)
        holds_posts = parse_parent_xml(xml_str_1)
        combined_posts_set = set(posts + holds_posts)
        for p in combined_posts_set:
            if p != self:
                self.children.append(p)
        return
    
    def parse_post_xml(self, xml_str: str):
        # todo
        return
    
    def parse_parent_xml(self, xml_str: str) -> List[Post]:
        # todo
        posts = []
        return posts


def rating_filter(posts: List[Post]) -> List[Post]:
    return [post for post in posts if post.rating < configs.score_threshold]
