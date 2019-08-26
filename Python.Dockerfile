FROM python:3-alpine

WORKDIR /usr/src/app

ADD requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN [ "python", "-c", "import nltk; nltk.download('punkt')" ]

ENTRYPOINT ["sh","startup.sh"]