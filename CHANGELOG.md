# stocksight Change Log

## [0.1-b.5] = 2019-01-11
### changed
- set encoding to utf-8 and checked for bytes when writing to twitteruserids.txt

## [0.1-b.4] = 2018-12-10
### fixed
- TypeError: can't concat str to bytes when writing to twitteruserids.txt

## [0.1-b.3] = 2018-11-23
### added
- requirements.txt for installing python requirements with pip
- config.py.sample has new setting for specifying elasticsearch host/ip, port, username and password, copy to your config file

## [0.1-b.2] = 2018-10-10
### added
- cli option -n --newsheadlines to fetch and analyze stock symbol headlines from yahoo finance website instead of twitter
- cli option --frequency to control how often news headlines are retrieved
- cli option --followlinks to follow any links in news headlines and scrape any relevant text on landing page
- additional mappings for newsheadline docs in elasticsearch indices
### changed
- code cleanup

## [0.1-b.1] = 2018-10-09
### note
- first release
