#-*- coding: utf-8 -*-
import socket
import ssl
import botcfg # save oauth in botcfg.py
import string
import time
from threading import *
import re
from urllib import urlopen
import urllib
import urllib2, json
import datetime

import multiprocessing as mp
import sqlite3
from multiprocessing import Process, Pipe

uptimewait = False
webpatt = r"\.+[a-zA-Z]+[/]+[a-zA-Z0-9]|https://|www\.+[a-zA-Z0-9]|[a-zA-Z0-9]+\.+com"
re.purge() # some housekeeping
server = "irc.chat.twitch.tv"
port = 443
channohash = botcfg.channeltojoin  # target channel without the hashkey
channel = "#" + channohash

perm = {}
plebcheck = r"subscriber=1|badges=partner|badges=broadcaster|mod=1|bits/10000"

pcheck = False
playlistTimerCommand = "playlistTimerCommand"
ratelim = 1
perm[playlistTimerCommand] = 0
bitstotal = 0
timers = {"calc": False, "uptime": False, "wyd": False, "hwm": False, "jchk": False}
unsetpListwait = False
unsetpSubwait = False
calcwaitplz = False
waitplease = False
waitplease2 = False
wydwait = False

chkku = ""
streamStatus = "orffline"

inChan = {}
msg1 = ".me (bot): I don't like links... DansGame " # link posting timeout message
wyd = ""
fols = 0

followerList = []
lastfol = "none!"


# CONNECTION #
# init socket
self = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# connect to said socket
self.connect((server, port))
# wrap in ssl
irc = ssl.wrap_socket(self)
##################################
# Sign In  

#                                             # oauth in botcfg should look like    oa = 'oauth:abc123abc123'
irc.send("PASS " + botcfg.oa + '\r\n')        #  use  http://www.twitchapps.com/tmi/ or similar to get your oauth
irc.send("NICK " + botcfg.botnick + '\r\n')   # twitch username of the bot


# capabilities request
irc.send("CAP REQ :twitch.tv/membership" + "\r\n")
# and join channel
irc.send("JOIN " + channel + '\r\n')
##################################
# tags request (flags)
irc.send("CAP REQ :twitch.tv/tags" + "\r\n")
# commands request
irc.send("CAP REQ :twitch.tv/commands" + "\r\n")
# join message
#irc.send("PRIVMSG " + channel + " :" + ".me Kappa Kappa Kappa Kappa Kappa KappaClaus " + "\r\n")
irc.send("PRIVMSG " + channel + " :" + " KappaClaus" + "\r\n")

##############################################################
########"@"@"@"@"@"@"@"@"@"@""@"@

CHAT_MSG=re.compile(r"@.+?PRIVMSG.+?(:){1}") # New (for irc flags mode)

def liveCheck(chan):
    global streamStatus
    cliid = "/?client_id=q6batx0epp608isickayubi39itsckt"
    uptadr = "https://api.twitch.tv/kraken/streams/" + chan + cliid

    try:
        response = urllib.urlopen(uptadr)
        data = json.loads(response.read())
        if data['stream']['stream_type'] == "live":
            print "channel is live!"
            streamStatus = "live"
            return True
        if data['stream']['stream_type'] == "watch_party":
            print "this is a vod?"
            streamStatus = "vod"
            return True
        if data['stream'] == None:
            print "Offline"     
            streamStatus = "offline"
            return False
                
    except Exception as e:
        print "offline"
        streamStatus = "offline"
        return False      

def followers(conn):
    global fols

    global followerList
    global channel
    global lastfol
    cliid = "&client_id=q6batx0epp608isickayubi39itsckt"
    
    #os = 0    
    url = 'https://api.twitch.tv/kraken/channels/' + channohash + '/follows?limit=1&direction=desc' + cliid
    
    #url = json.loads(url)
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    howmuch = 0

    if data['follows'] == None:
        print "follows api issue?"
    else:
        if lastfol == "none!":
            lastfol = data['follows'][0]['user']['name']
        tempor = data['follows'][0]['user']['name']
        
        c = data['_total']
        #print c

        if fols == 0:
            fols = c
        if c > fols:
            howmuch = c - fols
            fols = c            
            if howmuch == 1:
                print "one follower - " + tempor
                
                lastfol = tempor
                if not tempor in followerList:
                    conn.send("@" + tempor + " , ")
                    followerList.append(tempor)    
                return
            if howmuch > 1 and howmuch < 99:
                print "more than one follower " + str(howmuch)
                url = 'https://api.twitch.tv/kraken/channels/ ' + channohash +  '/follows?limit=' + str(howmuch) + '&direction=desc' + cliid
                response = urllib.urlopen(url)
                data = json.loads(response.read())
                folli = ""
                while howmuch > 0:
                    howmuch -= 1
                    temps = data['follows'][howmuch]['user']['name']
                    if not temps in followerList:
                        folli += '@' + temps + ' , '
                        followerList.append(temps)

                    
                    #print "follower " + data['follows'][howmuch]['user']['name']
                    #howmuch -= 1
                
                
                print "new followers " + folli
                conn.send(folli)
                lastfol = tempor
                return

            if howmuch > 99:
                print "something went wrong. howmuch = " + str(howmuch)

         
        if c < fols:
            howmuch = fols - c
            fols = c
            print "dropped " + str(howmuch) + " follower(s)"
        if c == fols:
            print "no new followers... still " + str(c)
            if lastfol != tempor and howmuch == 0:
                print "hmmmz"
                if not tempor in followerList:
                    conn.send("@" + tempor + " , ")
                    followerList.append(tempor)
                #irc.send('PRIVMSG ' + channel + " :" + ".me bleedPurple thanks for the follow " + tempor + "\r\n")
        lastfol = tempor
                
   

def chz():
    while 1:
        try:
            chatz('c')
            time.sleep(600)
        except Exception as e:
            print e
            print "chatz went wrong? try again in 30"
            time.sleep(30)
        

def flz(conn):
    while 1:
        try:
            followers(conn)
            time.sleep(90)    
        except Exception as e:
            print e
            print "followers failed? trying again in 10s"
            time.sleep(10)
        
        

def chatz(who):

    global channohash
    if liveCheck(channohash):
        conn = sqlite3.connect(channohash + '_log.db')
        c = conn.cursor()
        url = urlopen('https://tmi.twitch.tv/group/user/' + channohash + '/chatters').read()
        url = json.loads(url)
        mods = url.get('chatters').get('moderators')
        views = url.get('chatters').get('viewers')
        print mods
        print views
        inChan = {}
        if mods != None:
            c.execute('select usr from points')


            test = c.fetchall()
            try :
                if test[0] == None:
                    test = ":"             
            except IndexError:
                print 'db empty'

            for name in (mods):
                inChan[name] = 1
                modsit = [item for item in test if item[0] == name]

                if modsit:            
                    if who == 'c' and streamStatus == "live":
                        c.execute("""update points set point = point + 10 where usr = (?)""", [name])
                        
                        #increment points and timetot
                        conn.commit()
                    if who == 'c' and streamStatus == "vod":
                        c.execute("""update points set point = point + 5 where usr = (?)""", [name])
                        #increment points and timetot
                        conn.commit()
                else:
                    date = time.strftime('%d/%m/%Y')
                    blah = "select count (*) from points"
                    c.execute(blah)
                    temp = c.fetchone()
                    #print temp[0]
                    temp = temp[0] + 1
                    blah = "insert into points"
                
                    c.execute(blah + " values (?,?,?,?,?,?,?,?)",
                    (name, 0, temp, channohash, date, 0, 0, 0))
                    conn.commit()
                    #c.executemany("""insert into usr Values (?,?,?,?,?)""", [(name, 1, temp, channohash, datenow),])
     

                    print "added user :  " + name
    
        for plebian in (views):
            inChan[plebian] = 1
            plebsit = [pleb for pleb in test if pleb[0] == plebian]

            if plebsit:
                if who == 'c' and streamStatus == "live":
                    c.execute("""update points set point = point + 10 where usr = (?)""", [plebian])
                    conn.commit()
                if who == 'c' and streamStatus == "vod":
                    c.execute("""update points set point = point + 5 where usr = (?)""", [plebian])
                    conn.commit()
            
            else:          
                date = time.strftime('%d/%m/%Y')
                
                blah = "select count (*) from points"
                c.execute(blah)
                temp = c.fetchone()               
                temp = temp[0] + 1
                blah = "insert into points"                
                c.execute(blah + " values (?,?,?,?,?,?,?,?)",
                    (plebian, 0, temp, channohash, date, 0, 0, 0))
                conn.commit()
                # c.executemany("""insert into usr Values (?,?,?,?,?)""", [(name, 1, temp, channohash, datenow),])           
                print "added user : " + plebian
        
        conn.commit()
        conn.close()
    #xyz = Timer(100, chatz, ['callme'])
    #xyz.start()                        
                                     
########

def tablecheck():
        
    connx = sqlite3.connect(channohash + "_log.db")
    cu = connx.cursor()
        
    try:            
        blah = "select * from chat"

        cu.execute(blah)       
        print "table exists already, skipping"
        return True
    except Exception as (e):
        print e
        date = time.strftime('%d/%m/%Y')
        firsts = "create table if not exists chat"            
        firststart = firsts


        firststart += """ (
                        usr text,
                        mesg text,
                        id integer primary key,
                        flags text,
                        channel text,
                        date_time text
                        
                        );"""          
            
        print "firststart ran"
        time.sleep(1)
        cu.execute(firststart)
        date = time.strftime("%Y-%m-%dT%H:%M:%S")
        print date
        strings = "insert into chat"  
        cu.execute(strings + " values (?,?,?,?,?,?)",
          ("username", "message", 1, "flags", "channel", date))
        connx.commit()       

    try:            
        blah = "select * from points"

        cu.execute(blah)
         
        connx.close()
        print "table exists already, skipping"
        return True
    except Exception as (e):
        print e            
        date = time.strftime('%d/%m/%Y')
        firsts = "create table if not exists points"            
        firststart = firsts            
        firststart += """ (
                        usr text,
                        point integer,
                        id integer primary key,
                        channel text,
                        date_created text,
                        kudos integer,
                        antikudos integer,
                        currency integer
                        
                        );"""          
            
        print "firststart ran"
        time.sleep(1)
        cu.execute(firststart)
        date = time.strftime("%Y-%m-%dT%H:%M:%S")
        print date
        strings = "insert into points"  
        cu.execute(strings + " values (?,?,?,?,?,?,?,?)",
          ("username", 1, 1, "channel", date, 1, 1, 1))
        connx.commit()
        connx.close()

def checkpoints(name):
    global ratelim
    global waitplease
    global waitplease2
    global chkpoints
    if waitplease == False:
        waitplease2 = True
        
        conn = sqlite3.connect(channohash +'_log.db')
        c = conn.cursor()
        try:
            c.execute('select point from points where usr = (?)', [name])
            chkpoints = c.fetchone()
            temps = chkpoints[0]
            if temps < 30:
                yourrank = 0
            elif temps < 60:
                yourrank = 1
            elif temps < 120:
                yourrank = 2
            elif temps < 240:
                yourrank = 3
            elif temps < 480:
                yourrank = 4
            elif temps < 960:
                yourrank = 5
            elif temps < 1920:
                yourrank = 6
            elif temps < 3840:
                yourrank = 7
            elif temps < 7860:
               
                yourrank = 8                
            elif temps < 15360:
                yourrank = 9
            elif temps < 30720:
                yourrank = 10
            elif temps < 61440:
                yourrank = 11
            elif temps < 122880:
                yourrank = 12

            #temps /= 100        
            chkpoints = str(chkpoints[0])
            stringy = user + ": Level: " + str(yourrank)
            stringy += " Points: "
            c.execute('select kudos from points where usr = (?)', [name])
            chkku = c.fetchone()
            chkku = str(chkku[0])
   
            irc.send('PRIVMSG ' + channel + " : .me " + stringy + chkpoints + " kudos: " + chkku + "\r\n")
            #ratelim += 1
        except Exception as e:
            print "someting went wrong while checking points"


        conn.close()

        waitplease2 = False

# 1 point per min
    # (1):30m (2):1h (3):2h (4):4h (5):8h (6):16h (7):32h (8):64h (9):128h (10):256h (11):512h (12):1024h
    #    30     60     120    240    480    960    1920    3840    7860      15360    30720      61440  

def permit(name):
    del perm[name]

def plebcheckk(flagz):
    if re.search(plebcheck, flags):
        return True
def queryPlz(name, ir, count):
    global ratelim
    zx = ""
    xzy = ""
    try:
        conne = sqlite3.connect(channohash + '_log.db')
        co = conne.cursor()
        print "1"
        #sigh = "select mesg from chat where usr == " + name
        #co.execute('select mesg from chat where usr = (?)', [name])        
        #co.execute(sigh)
        name = string.replace(name, "\r\n", "")
        co.execute('select mesg from chat where usr = (?) order by id desc limit ' + str(count) , [name])        
        zx = co.fetchall()
            
        for i in zx:
            print i[0]
            xzy += i[0] + " >#< "
        xzy = string.replace(xzy, "\r\n", "")
        conne.close()
        print zx
        irc.send('PRIVMSG ' + channel + ' : .me ' "Last " + str(count) + " from " + name + ": " + str(xzy) + '\r\n')
        #ratelim += 1

    except Exception as e:
        print e
        conne.close()
        
def linksQ():

    global webpatt
    conne = sqlite3.connect(channohash + '_log.db')
    co = conne.cursor()
    #thyme = time.gmtime()
    #print thyme
    co.execute('select mesg from chat where strftime("%s",date_time) > strftime("%s","now","-12 hours")')
    zx = co.fetchall()
    ltmp = " "
    for i in zx:
        #print i
        if re.search(webpatt, str(i)):
            
            #print i[0]
            if i[0] not in ltmp:
                ltmp += str(i[0]) + " # "
    ltmp = ltmp.replace("\r\n", "")
    if ltmp == " ":
        ltmp = "none"
    #print ltmp
    irc.send('PRIVMSG ' + channel + ' : .me ' + "links from last 12 hours - " + ltmp + '\r\n') 




##############################
def calcIt(v1, op, v2):
    global calcwaitplz
    if timers["calcwaitplz"] != True:
        #if calcwaitplz != True:

        try:
            if op == "+":

                answ = int(v1) + int(v2)
                irc.send('PRIVMSG ' + channel + ' :' "Answer is: " + str(answ)  + '\r\n')
            if op == "-":
                answ = int(v1) - int(v2)
                irc.send('PRIVMSG ' + channel + ' :' "Answer is: " + str(answ)  + '\r\n')
            if op == "*":
                answ = int(v1) * int(v2)
                irc.send('PRIVMSG ' + channel + ' :' "Answer is: " + str(answ)  + '\r\n')
            if op == "/":
                answ = int(v1) / int(v2)
                irc.send('PRIVMSG ' + channel + ' :' "Answer is: " + str(answ)  + '\r\n')
            timers[calcwaitplz] = True
            xy = Timer(30, uns, ["calcwaitplz"])
            xy.start()
        except Exception as e:
            print e
            print "likely NaN" # python has check for Not a number?
###############################
def unsetCalc():
    global calcwaitplz
    calcwaitplz = False
#Timers Unsetters
def unsetUt():
    print "UNSET UT"
    global uptimewait

    uptimewait = False
def unsetpList():
    global unsetpListwait
    unsetpListwait = False

def unsetpSub():
    global unsetpSubwait
    unsetpSubwait = False
def unsetWyd():

    global wydwait
    wydwait = False
    print "unset wydwait"

def uns(item):
    print "unset " + item
    timers[item] = False
##########################################################################################
#UpTime Checker
def uptimeCheck(irc):
    global channohash
    global uptimewait
    global ratelim
    cliid = "/?client_id=q6batx0epp608isickayubi39itsckt"
    #uptadr = "https://api.twitch.tv/kraken/streams/" + channohash + cliid
    uptadr = "https://api.twitch.tv/kraken/streams/" + channohash + cliid

    if uptimewait != True:
        uptimewait = True
        response = urllib.urlopen(uptadr)
        data = json.loads(response.read())
        if data['stream'] == None:
            print "Offline"
            irc.send('PRIVMSG ' + channel + " :" + ".me The Channel Appears To Be Offline..." + "\r\n")
            #ratelim += 1
        else:                     
            s = data['stream']['created_at'][0:19]
            sucess = time.mktime(datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").timetuple())
             # change timestamp to epoch time
            answer = time.time() - sucess  # get the difference
            #answer = answer + 18000 # because of timezone?
            print answer  # difference in seconds
            
            answer /= 60  # diff in minutes
            if answer > 0 and answer < 60:                # if under an hour just print minutes
                print "live for " + str(answer) + " minutes"
                irc.send('PRIVMSG ' + channel + " :" + ".me Live For: " + str(answer) + " minutes" + "\r\n")
                #ratelim += 1

            if answer >= 60:      # if over an hour change to hours and seperate whole hours from the rest
                
                answer /= 60                   # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                # answer is n.nnn
                splits = str(answer).split(".")
                #answer -= 1  # < < < < < < < < < <# idk why but it was an hour ahead of true time
                answer = splits[0]              # assuming it will be different for you.. bttv /uptime was handy
                idk = float("0." + splits[1])  # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                idk = idk * 60
                idk = str(idk).split('.')
                idk = idk[0]
                print "live for " + str(answer) + " hours and " + str(idk) + " minutes" 
                irc.send('PRIVMSG ' + channel + " :" + ".me Live For: " + str(answer) + " Hours And " + str(idk) + " Minutes" + "\r\n")
                #ratelim += 1       
        ut = Timer(30, unsetUt)
        ut.start()

def kudos(name):
    connxs = sqlite3.connect(channohash + '_log.db')
    cx = connxs.cursor()
    cx.execute("""select * from points where usr = (?)""", [name])
    tm = cx.fetchall()
    try:
        if tm[0] != None:
            cx.execute("""update points set kudos = kudos + 1 where usr = (?)""", [name])
            connxs.commit()

            irc.send("PRIVMSG " + channel + " :" + ".me KUDOS +1 " + name + "\r\n")
            #ratelim += 1    
    except Exception as e:
        irc.send("PRIVMSG " + channel + " :" + ".me sorry, " + name + " doesnt exist in database" + "\r\n")
        #ratelim += 1
        print e
    connxs.close()
###################################################################################

def follorep(self):
    global ratelim
    ratelim = 1
    ############
    try:
        if parent_conn.poll():
            folloes = " "

            x = False
            while x == False:
                try:
                    if parent_conn.poll():
                        folloes += parent_conn.recv()
                    else:
                        x = True
                except Exception as e:
                    print "end of data"
            print "folloes = "
            print folloes
            irc.send('PRIVMSG ' + channel + ' :' "Thanks for following " + folloes + '\r\n')


    except Exception as e:

        print "followers exception"
    x = Timer(10, follorep, args=(self,))
    x.start()


tablecheck()
chatz("bootup")
#ratelimit()
#followers()
conn = sqlite3.connect(channohash + '_log.db')
c = conn.cursor() 
cstrt = False
##Main Bot Start
while True:
    if cstrt == False:
        cstrt = True
        parent_conn, child_conn = Pipe()

        #ir_conn, unity_conn = Pipe()

        # chatters
        pro = mp.Process(target = chz).start() 

        # follower check
        fo = mp.Process(target = flz, args=(child_conn,)).start()

        # follower report batcher
        follorep(self)           
    
    #gets output from IRC server

    try:
        data = irc.recv(1024)
    except Exception as e:
        print e
        print "socket dropped?"
        irc.send("PART " + channel + '\r\n')
        time.sleep(3)
        irc.send("JOIN " + channel + '\r\n')

    # ping/pong

    if data == "PING :tmi.twitch.tv\r\n":
        irc.send("PONG :tmi.twitch.tv\r\n")

    user = data.split('!', 1)[-1]
    user = user.split('@')[0]
    
    message = CHAT_MSG.sub("", data)

    flags = data.split(':', 1)[0]
    #if ratelim > 15:
    print "ratelimit : " + str(ratelim)



    print "data#### " + data

    try:
        unicode(message)


    except UnicodeDecodeError:
        
        u = message

        try:
            uu = u.decode('utf8')
        except Exception as e:
            print e
            if not "@" in (message):    # moved in 1 tab here and below
                print "hmm"                
                #irc.send('PRIVMSG ' + channel + ' :' "i dont like that for some reason" + '\r\n')
                #irc.send('PRIVMSG ' + channel + ' :' ".timeout " + user + " " + "1" + '\r\n')
                #message = "a"  

    print (user + ": " + message) # new (for flags mode)
    
    try:
        unicode(message[0:15], "utf-8")
        if "tmi.twitch.tv" not in (user) and "tmi.twitch.tv" not in (message) and (user) != "":
            if "jtv MODE" not in (user) and "justinfan" not in (user) and user != "twitchnotify":
                

            
                date = time.strftime("%Y-%m-%dT%H:%M:%S")

                blah = "select count (*) from chat"
                c.execute(blah)

                temp = c.fetchone()
                #print temp[0]
                temp = temp[0] + 1
                blah = "insert into chat"
                    
                c.execute(blah + " values (?,?,?,?,?,?)",
                            (user, message, temp, flags, channohash, date))
                conn.commit()

    except Exception as (e):
        if (user) != "":
            date = time.strftime("%Y-%m-%dT%H:%M:%S")
            blah = "select count (*) from chat"
            c.execute(blah)
            temp = c.fetchone()

            #print temp[0]
            temp = temp[0] + 1
            conn.text_factory = 'utf-8'

            blah = "insert into chat"
            c.execute(blah + " values (?,?,?,?,?,?)",
                    (user, message, temp, flags, channohash, date))    
            conn.commit()
           
            conn.text_factory = 'string'




    


    if "!quit" in (message):
        if (user) == channohash or (user) in botcfg.trustedppl:
            irc.send('PRIVMSG ' + channel + " :" + "Connection Terminated... BibleThump" + "\r\n")

            irc.send('PART ' + channel + '\r\n')
            
            quit()


    if "!shout" in (message):
        if "mod=1" in (flags) or "badges=broadcaster" in (flags) or (user) in botcfg.trustedppl:
            shoutout = message.split(" ", 1)
            usr = shoutout[1]
            shoutstr = "go check out twitch.tv/" + usr
            irc.send("PRIVMSG " + channel + " :" + shoutstr + "\r\n")
            
            #ratelim += 1
            #time.sleep(0.2)
            #irc.send("PRIVMSG " + channel + " :" + shoutstr + "\r\n")
            #time.sleep(0.2)
            #irc.send("PRIVMSG " + channel + " :" + shoutstr + "\r\n")
            #time.sleep(0.2)
            #irc.send("PRIVMSG " + channel + " :" + shoutstr + "\r\n")
            #time.sleep(0.2)
            
              

    if (message) == "!uptime\r\n":

        uptimeCheck(irc)

    if (message == "!help\r\n" or message == "!commands\r\n"):
        irc.send("PRIVMSG " + channel + " :" + " command to move bot is eg. !bot -45 4 90 " + "\r\n")


    if (message) == "!level\r\n" or (message) == "!xp\r\n" or (message) == "!points\r\n":
        checkpoints(user)            

    if "!calc" in (message):
        try:
            stringy = message.split(" ")
            firts = stringy[1] # first value
            opz = stringy[2]  # operator
            secn = stringy[3] # second val
            calcIt(firts, opz, secn)
        except Exception as e:
            
            print e

    if "!last" in (message):
        try:
            if "mod=1" in (flags) or "badges=broadcaster" in (flags) or (user) in botcfg.trustedppl:
            
                messageq = message.split(" ")
                messagereqc = messageq[0]
                messageq = messageq[1]
                
                messagereqc = string.replace(messagereqc, "!last", "")
            
                print messageq
                print messagereqc
                queryPlz(str(messageq), irc, int(messagereqc))

        except Exception as e:
            print e

    if "!kudos" in (message):
        if "mod=1" in (flags) or "badges=broadcaster" in (flags) or (user) in botcfg.trustedppl:
            message = string.replace(str(message), "\r\n", "")
            message = string.replace(str(message), "@", "")
            message = message.split(" ")
             
            try:
                temps = message[1]
                kudos(temps)
                    
            except Exception as e:
                print e
                print "couldnt give kudos"            
            #c.execute('select kudos from points where usr = (?)', [message[1]])
            #temp = c.fetchone()



    time.sleep(0.1)
############################