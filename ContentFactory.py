# -*- coding:utf-8 -*-

import ConfigParser
import sys,re
from bs4 import BeautifulSoup as bs
from utils/util import *
import time
import re
import threading
import Queue

# home_uri = 'http://weibo.cn/u/'
home_uri = 'http://weibo.cn/'
# page_uri = '/profile?page='
page_uri = '?page='
page_limit = 20

class ContentFactory(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        threading.Thread.__init__(self)

        self.total = 0
        self.retweet = 0
        self.end = False

        cf = ConfigParser.ConfigParser()
        cf.read("config.ini")
        host = cf.get("db", "host")
        port = int(cf.get("db", "port"))
        user = cf.get("db", "user")
        passwd = cf.get("db", "passwd")
        db_name = cf.get("db", "db")
        charset = cf.get("db", "charset")
        use_unicode = cf.get("db", "use_unicode")
        self.db = MySQLdb.connect(host=host, port=port, user=user, passwd=passwd, db=db_name, charset=charset, use_unicode=use_unicode)
        self.cursor = self.db.cursor()

    def run(self):
        while not self.queue.empty():
            t = self.queue.get()
            self.user_id = t[0]
            print 'start processing user:', self.user_id
            self.target = home_uri + str(self.user_id) + page_uri
            for page_num in range(1, page_limit):
                self.get_tweet(self.target + str(page_num))
                if self.end: # if there's no more tweets for this user
                    self.end = False
                    break
            if self.total == 0:
                print "no tweet..."
                sys.exit(-3)

            sql = "UPDATE NAME SET CONTENT_VISIT=%s, CONTENT_TOTAL=%s, CONTENT_RETWEET=%s WHERE LINK_ID=%s"
            self.cursor.execute(sql, (1, self.total, self.retweet, self.user_id))
            self.total = 0
            self.retweet = 0
            print "finishing", self.user_id

    def get_tweet(self, url):
        time.sleep(5)
        content = get_content(url)
        if content:
            # print content.text
            soup = bs(content.text, 'html.parser')
            tweets = [x.get_text('|', strip=True).split('|')[0] for x in soup.find_all('div') if 'class' in x.attrs if x.attrs['class'] == ['c']]
            for x in range(len(tweets) - 2):
                self.sans_retweet(tweets[x])
            print 'number of tweets for this page:', len(tweets)
            if len(tweets) == 2:
                self.end = True
            #print self.retweet
            if len(tweets) > 20:
                print "wocao... you bei fenghao la"
                sys.exit(5)

    def sans_retweet(self, tweet):
        self.total += 1
        pattern = u'转发'
        pattern2 = u'［'
        pattern3 = u'＃'
        if re.match(pattern, tweet) == None:
        ## insert to database
            if re.match(pattern2, tweet) == None:
                if re.match(pattern3, tweet) == None:
                    sql = "INSERT IGNORE INTO CONTENT (LINK_ID, CONTENT) VALUES(%s, %s)"
                    self.cursor.execute(sql, (self.user_id, tweet))
        else:
            self.retweet += 1


class UpdateContent(object):
    def __init__(self):
        cf = ConfigParser.ConfigParser()
        cf.read("config.ini")
        host = cf.get("db","host")
        port = int(cf.get("db","port"))
        user = cf.get("db","user")
        passwd = cf.get("db","passwd")
        db_name = cf.get("db","db")
        self.content_thread_amount = int(cf.get("content_thread_amount", "content_thread_amount"))
        try:
            self.db = MySQLdb.connect(host=host, port=port, user=user, passwd=passwd, db=db_name)
            print "Connected to db."
        except:
            print "Can't connect to db."
            sys.exit(-1)
        self.cursor = self.db.cursor()

    def run(self):
        queue = Queue.Queue()
        threads = []
        sql = "SELECT LINK_ID FROM NAME LIMIT 100;" # for Social Hacking, 100 is enough #TODO: make it a clp (command-line parameter)
        self.cursor.execute(sql)
        res = self.cursor.fetchall() # res is a list
        print res # debug
        i = 0
        for row in res:
            user_id = str(row[0])
            print user_id
            queue.put([user_id, i])
            i = i + 1
        thread_amount = self.content_thread_amount
        for i in range(thread_amount):
            threads.append(ContentFactory(queue))
        for i in range(thread_amount):
            threads[i].start()
            # print str(threads[i]) + "begins"
        for i in range(thread_amount):
            threads[i].join()
        self.db.close()
        print '------- all tasks done -------'


def main():
    app = UpdateContent()
    app.run()

if __name__ == '__main__':
    main()
