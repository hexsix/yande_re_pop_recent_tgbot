import asyncio
import json
import os
import pickle
import re
import time
from typing import Set

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import feedparser
import httpx

config = json.load(open("config.json", 'r', encoding='utf8'))


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class Rss:
    rss_url: str
    target: str
    already_sent: Set

    def __init__(self):
        self.rss_url = "https://rsshub.app/yande.re/post/popular_recent"
        self.target = f"https://api.telegram.org/bot{config['bot_token']}" \
                      f"/sendMessage?chat_id={config['chat_id']}&text="

    async def log(self, text, debug=config["debug"]):
        print(f"{now()} {text}")
        if debug:
            await self._send(text)

    def _load_already_sent(self):
        filepath = "already_sent.pkl"
        if os.path.exists(filepath):
            self.already_sent = pickle.load(open(filepath, 'rb'))
        else:
            self.already_sent = set()

    def _dump_already_sent(self):
        filepath = "already_sent.pkl"
        pickle.dump(self.already_sent, open(filepath, 'wb'))

    async def _send(self, text):
        for _ in range(3):
            try:
                if config["use_proxies"]:
                    async with httpx.AsyncClient(proxies=config["proxies"]) as client:
                        r = await client.post(self.target + text)
                else:
                    async with httpx.AsyncClient() as client:
                        r = await client.post(self.target + text)
                if r.json()["ok"]:
                    return True
            except Exception:
                await asyncio.sleep(2)
        return False

    async def run(self):
        await self.log(f"[INFO]: Crontab Start ...")
        # download rss
        await self.log(f"[INFO]: Downloading RSS ...")
        rss_json = None
        for _ in range(3):
            await self.log(f"[INFO]: The {_ + 1}th attempt, 3 attempts in total.")
            try:
                if config["use_proxies"]:
                    async with httpx.AsyncClient(proxies=config["proxies"]) as client:
                        r = await client.get(self.rss_url)
                else:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(self.rss_url)
                rss_json = feedparser.parse(r.text)
            except:
                await self.log(f"[WARNING]: Failed to download RSS, the next attempt will start in 2 seconds.")
                await asyncio.sleep(2)
            else:
                break
        if not rss_json:
            await self.log(f"[ERROR]: Failed to download RSS.")
            return
        await self.log(f"[INFO]: Succeed to download RSS.")

        try:
            await self.log(f"[INFO]: Loading already sent list ...")
            self._load_already_sent()
        except:
            await self.log(f"[ERROR]: Failed to load already sent list.")
        else:
            await self.log(f"[INFO]: Succeed to load already sent list.")

        # parse rss and send message
        await self.log(f"[INFO]: Now send images ...")
        for entry in rss_json["entries"]:
            try:
                post_url = entry['link']
                post_id = post_url.split('/')[-1]
                if post_id in self.already_sent:
                    continue
                score = int(re.search(r'Score:\d*', entry['description']).group().split(':')[-1])
                if score < config["score_threshold"]:
                    continue
                # s: safe, q: questionable, e: explicit
                rating = re.search(r'Rating:.', entry['description']).group().split(':')[-1]
                if rating == 'e':
                    link = re.search(r'https://files.yande.re/sample/[^"]*', entry['description']).group()
                    text = f"{link}\n{post_url}"
                else:
                    text = post_url
                if await self._send(text):
                    self.already_sent.add(post_id)
                    self._dump_already_sent()
            except:
                continue
        await self.log(f"[INFO]: End.")


async def main():
    await Rss().run()


if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    scheduler.add_job(main, 'cron', hour='*', minute='0')
    scheduler.start()
    asyncio.get_event_loop().run_forever()
