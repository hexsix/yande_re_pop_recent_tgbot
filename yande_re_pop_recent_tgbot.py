import asyncio
import json
import os
import pickle
import re
from typing import Dict, Set

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import feedparser
import httpx

config = json.load(open("config.json", 'r', encoding='utf8'))


class Rss:
    rss_url: str
    rss_json: Dict
    already_sent: Set

    def __init__(self):
        self.rss_url = "https://rsshub.app/yande.re/post/popular_recent"

    async def download(self):
        for _ in range(3):
            try:
                if config["use_proxies"]:
                    async with httpx.AsyncClient(proxies=config["proxies"]) as client:
                        r = await client.get(self.rss_url)
                else:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(self.rss_url)
                return feedparser.parse(r.text)
            except:
                await asyncio.sleep(2)
        return None

    def _load_already_sent(self):
        filepath = "already_sent.pkl"
        if os.path.exists(filepath):
            self.already_sent = pickle.load(open(filepath, 'rb'))
        else:
            self.already_sent = set()

    def _dump_already_sent(self):
        filepath = "already_sent.pkl"
        pickle.dump(self.already_sent, open(filepath, 'wb'))

    def parse(self, rss_json):
        self._load_already_sent()
        post_urls = []
        for entry in rss_json["entries"]:
            try:
                post_url = entry['link']
                post_id = post_url.split('/')[-1]
                if post_id in self.already_sent:
                    continue
                score = int(re.search(r'Score:\d*', entry['description']).group().split(':')[-1])
                if score < config["score_threshold"]:
                    continue
                post_urls.append(post_url)
            except:
                continue
        return post_urls

    async def send(self, post_url):
        target = f"https://api.telegram.org/bot{config['bot_token']}" \
                 f"/sendMessage?chat_id={config['chat_id']}" \
                 f"&text={post_url}"
        for _ in range(3):
            try:
                if config["use_proxies"]:
                    async with httpx.AsyncClient(proxies=config["proxies"]) as client:
                        r = await client.post(target)
                else:
                    async with httpx.AsyncClient() as client:
                        r = await client.post(target)
                if r.json()["ok"]:
                    self.already_sent.add(post_url.split('/')[-1])
                    self._dump_already_sent()
                    break
            except Exception:
                await asyncio.sleep(2)


rss = Rss()


async def main():
    global rss
    rss_json = await rss.download()
    post_urls = rss.parse(rss_json)
    for post_url in post_urls:
        await rss.send(post_url)


if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    scheduler.add_job(main, 'cron', hour='*')
    scheduler.start()
    asyncio.get_event_loop().run_forever()
