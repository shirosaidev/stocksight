#Copyright (C) Chris Park 2018-2019
#Copyright (C) Allen (Jian Feng) Xie 2019
#stocksight is released under the Apache 2.0 license. See
#LICENSE for the full license text.
FROM redis:5-alpine
LABEL maintainer="Allen (Jian Feng) Xie"
COPY redis.conf /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]