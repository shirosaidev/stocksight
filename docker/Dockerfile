FROM continuumio/anaconda3:5.1.0
MAINTAINER klebermagno
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y \
        libpq-dev \
        build-essential \
        git \
        sudo

RUN conda config --append channels conda-forge
RUN conda update -n base conda

RUN  pip install --no-cache-dir -I elasticsearch==5.5.3

RUN pip install requests nltk tweepy beautifulsoup4 textblob vaderSentiment
 

ENV username devel
ENV userid 1000

ARG home=/home/${username}
ARG workdir=${home}/stocksight

RUN adduser devel --uid 1000 --gecos '' --disabled-password \
    && echo "${username} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${username} \
    && chmod 0440 /etc/sudoers.d/${username}

WORKDIR ${workdir}
RUN chown ${username}:${username} ${workdir}

EXPOSE 5601

RUN cd ${workdir}

USER ${username}

RUN python -m nltk.downloader punkt

ENTRYPOINT ["tail", "-f", "/dev/null"]
