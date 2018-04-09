# twitchbot
twitch irc chat bot in python

botcfg.py needs to be configured before use, you also need to get an oauth key for the twitch username you are using for the bot, hope this if of some help to someone!
bot includes functionality to thank new followers to a channel, log chat for moderation/chat recall purposes, a points system which adds points to users in the channel every 10 mins when the stream is live, also an uptime command

!calc 1 + 1               # calc the sum (+ / - *)
!quit                     # channel owner or trustedppl only only
!shout username           # shoutout to the username given, channel owner or trustedppl only
!uptime                   # time stream has been live for
!last5 username           # return last n messages from user the bot has seen (channel owner or trustedppl only)
!kudos username           # add a kudos point to username (channel owner or trustedppl only)

!xp | !level | !points    # check points (it may be flaky for recently joined users that havent been added to the system yet)
