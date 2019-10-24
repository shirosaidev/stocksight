#Copyright (C) Chris Park 2018-2019
#Copyright (C) Allen (Jian Feng) Xie 2019
#stocksight is released under the Apache 2.0 license. See
#LICENSE for the full license text.
FROM python:3-alpine

LABEL maintainer="Allen (Jian Feng) Xie"

WORKDIR /usr/src/app

ADD requirements.txt ./requirements.txt

RUN apk --no-cache add curl

RUN pip install --no-cache-dir -r requirements.txt

RUN [ "python", "-c", "import nltk; nltk.download('punkt')" ]

ENTRYPOINT ["sh","startup.sh"]