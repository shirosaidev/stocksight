# stocksight Change Log

## [0.2] = 2019-09-22
### major changes
- Dockerized the system.  CLI scripts are retired.
    - All settings are fetched from src/config.yml.
- Replaced ElasticSearch 5.6 with ElasticSearch 7.3.
- Added Redis for caching.
- Automated requirements installation and kibana dashboard setup.
- Converted original scripts to modules and classes to simplify the process of building new extensions
- Data mapping have changed.
    - Each Symbol has it's own set of index. One for sentiment and one for price.
    - See src/Stocksight/EsMap for mapping details
- Sentiment and price crawlers are spawned concurrently based on your specified stock symbols.
- Improved memory footprint by spawning python instances when it's needed.

### added
- Added SeekingAlpha crawler
- Added integration test cases
- Added support for generating random proxy and random user-agent.
  - may not be useful for sophisticated blockers.

### issues:
- SeekingAlpha blocks frequent accesses with 403.  Follow_link is disabled for it.


## [0.1-b.6] = 2019-07-15
### fixed
- "TypeError: sequence item 0: expected str instance, int found" traceback error when running with -f twitteruserids.txt

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
