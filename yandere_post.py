"""
author: hexsix
date: 2022/08/17
description: yande.re post class
"""

import logging
from typing import Dict, List
import xml.etree.ElementTree as ET

from yandere_api import api_post


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

    def __init__(self, id: str):
        pass
    
    def init(self, id: str):
        self.id = id
        self.parse()
    
    def parse(self):
        response_xml = api_post(self.id)
        # todo: parse response_xml


class Parent(object):
    parent: Post
    children: List[Post]

    def __init__(self):
        pass

    def init(self, id: str):
        response_xml = api_parent(id)
        # todo parse response_xml


class Posts(object):
    dic: Dict[str, Post]

    def __init(self):
        pass


POSTS = Posts()
