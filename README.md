# yande.re popular recent telegram bot

A telegram bot for rss yande.re popular recent

The route of RSSHub is /yande.re/post/popular_recent

## Sample

https://t.me/yandere_pop_recent

## Usage

1. Ask bot father to create a bot and get token
2. Create a group/channel for you and bot, say to bot "/hello @bot"
3. Open "https://api.telegram.org/bot{token}/getUpdates" and get chat_id
4. The create an app on heroku
5. Add `Config Var` below on heroku settings
6. Install Add-on `Heroku Scheduler`, it is free
7. Finally run Scheduler as you like

## Config Vars

```
RSS_URL=https://rsshub.app/yande.re/post/popular_recent
TG_TOKEN=1234567890:abcdefghijklmnopqrstuvwxyz
CHAT_ID=-0987654321
SCORE_THRESHOLD=0
```
