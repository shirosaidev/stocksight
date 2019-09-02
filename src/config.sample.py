#Global Config
elasticsearch_host = "elasticsearch"
elasticsearch_port = 9200
elasticsearch_user = ""
elasticsearch_password = ""

redis_host = "redis"
redis_port = 6379

symbols = ['tsla','amd'];
follow_link = False;


#Sentiment Analyizers config
nltk_tokens_required = {
 'default': ("increase","decrease","buying","sold","buy","selling","winning","losing"),
 'tsla':  ("tesla", "@tesla", "#tesla",  "tsla", "#tsla", "elonmusk", "elon", "musk"),
 'amd': ('amd','ryzen','epyc','radeon','crossfire','threadripper')
}
nltk_tokens_ignored = ("win", "giveaway")

#Twitter Settings
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
twitter_feeds = ["@elonmusk", "@cnbc", "@benzinga", "@stockwits",
                 "@Newsweek", "@WashingtonPost", "@breakoutstocks", "@bespokeinvest",
                 "@WSJMarkets", "@stephanie_link", "@nytimesbusiness", "@IBDinvestors",
                 "@WSJDealJournal", "@jimcramer", "@TheStalwart", "@TruthGundlach",
                 "@Carl_C_Icahn", "@ReformedBroker", "@bespokeinvest", "@stlouisfed",
                 "@muddywatersre", "@mcuban", "@AswathDamodaran", "@elerianm",
                 "@MorganStanley", "@ianbremmer", "@GoldmanSachs", "@Wu_Tang_Finance",
                 "@Schuldensuehner", "@NorthmanTrader", "@Frances_Coppola", "@BuzzFeed","@nytimes"]
min_followers = 1000

#Stock Price fetcher config
weekday_start = 1
weekday_end = 5
hour_start = 9
hour_end = 18
timezone_str = 'America/Toronto'