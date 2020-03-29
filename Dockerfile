FROM python:3.6

LABEL maintainer="shirosai"

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

COPY sentiment.py ./
COPY stockprice.py ./
COPY startup.sh ./

ENV PYTHONIOENCODING=utf8

ENTRYPOINT [ "bash", "startup.sh" ]