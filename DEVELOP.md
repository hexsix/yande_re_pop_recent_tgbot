# DEVELOP Doc

todo

1. Request Rsshub and parse with feedparser. Get a yande.re post list.
2. Request api to get the parent post of each post.
3. Filter low rating post.
4. Filter sent post with redis.
5. For each post that has not been sent, request api to get it's child posts. (including `tag=holds:true`)
6. Finally send to the channel together, and set already sent key in redis.
