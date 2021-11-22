"""
author: hexsix
date: 2021/11/22
description: 写给 heroku 云服务
"""

import os

if __name__ == '__main__':
    print(os.environ['SCORE_THRESHOLD'])
