#Global Config
elasticsearch_host = "elasticsearch"
elasticsearch_port = 9200
elasticsearch_user = ""
elasticsearch_password = ""

#Sentiment Analyizers config
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
nltk_tokens_required = {
 'default': ("increase","decrease","buying","sold","buy","selling","winning","losing"),
 'tsla':  ("tesla", "@tesla", "#tesla",  "tsla", "#tsla", "elonmusk", "elon", "musk"),
 'amd': ('amd','ryzen','epyc','radeon','crossfire','threadripper')
}
nltk_tokens_ignored = ("win", "Win", "giveaway", "Giveaway")
twitter_feeds = ["@elonmusk", "@cnbc", "@benzinga", "@stockwits",
                 "@Newsweek", "@WashingtonPost", "@breakoutstocks", "@bespokeinvest",
                 "@WSJMarkets", "@stephanie_link", "@nytimesbusiness", "@IBDinvestors",
                 "@WSJDealJournal", "@jimcramer", "@TheStalwart", "@TruthGundlach",
                 "@Carl_C_Icahn", "@ReformedBroker", "@bespokeinvest", "@stlouisfed",
                 "@muddywatersre", "@mcuban", "@AswathDamodaran", "@elerianm",
                 "@MorganStanley", "@ianbremmer", "@GoldmanSachs", "@Wu_Tang_Finance",
                 "@Schuldensuehner", "@NorthmanTrader", "@Frances_Coppola", "@BuzzFeed","@nytimes"]
sentiment_frequency = 3600

#Stock Price fetcher config
price_frequency = 900
weekday_start = 1
weekday_end = 5
hour_start = 9
hour_end = 18
timezone_str = 'America/Toronto'