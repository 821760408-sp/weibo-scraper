#-*- coding:utf-8 -*-
import requests
import gzip
import StringIO
import ConfigParser
import sys
from bs4 import BeautifulSoup
import time
import re
import MySQLdb

_home_page = 'http://weibo.cn/'
_info_page = '/info'
_config = ConfigParser.ConfigParser()
_config.read("config.ini")

def re_get_uid(uid_str):
    import re
    patt = 'uid=([0-9]*)&rl'
    qwe = re.search(patt, uid_str)
    try:
        if qwe.group(1):
            print 'Got uid: ', qwe.group(1)
            return qwe.group(1)
        else:
            return None
    except:
        return None

def get_content(url):
    """
    Return the content of given url
    """
    cookie = _config.get("cookie", "cookie")
    cookie_dic = dict(Cookie=cookie)
    try:
        res = requests.get(url, cookies=cookie_dic, timeout=100)
    except:
        return None
    if res.status_code != requests.codes.ok:
        print "Not getting 200; status_code is: " + str(res.status_code);
        sys.exit(-1)
    return res

def get_user_info(uid):
    time_now = int(time.time())
    url = _home_page + uid + _info_page
    print url
    res = get_content(url)
    if res:
        soup = BeautifulSoup(res.text, 'html.parser')
        time.sleep(1)
        divs = soup.find_all('div', 'tip')
        person_info = divs[0].next_sibling.get_text('|', strip=True)
        name, sex, hometown = impRe(person_info)
        return (name, 0, uid, time_now, sex, hometown)
    else:
        return None

def connect_db(info):
    host = _config.get("db", "host")
    port = int(_config.get("db", "port"))
    user = _config.get("db", "user")
    passwd = _config.get("db", "passwd")
    db_name = _config.get("db", "db")
    charset = _config.get("db", "charset")
    use_unicode = _config.get("db", "use_unicode")
    try:
        db = MySQLdb.connect(host=host, port=port, user=user, passwd=passwd, db=db_name, charset=charset, use_unicode=use_unicode)
        cursor = db.cursor()
    except:
        print "Fail to connect to database"
        sys.exit(-1)
    sql = "INSERT IGNORE INTO NAME (USERNAME, LAST_VISIT, LINK_ID, ADD_TIME, SEX, HOMETOWN) VALUES(%s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, info)
    db.commit()
    print "first info inserted to database."

def impRe(person_info):
    print 'getting info from:', person_info, "......"
    pattern = u'昵称:([^\|]*)|'
    abc = re.match(pattern, person_info)
    name = abc.group(1)

    pattern = u'性别:([^\|])'
    abc = re.search(pattern, person_info)
    sex = abc.group(1)

    pattern = u'地区:([^\|]*)'
    abc = re.search(pattern, person_info)
    hometown = abc.group(1)

    return name, sex, hometown


def main():
    print "test begins..."
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    main_id = config.get("weibo", "mainID")
    url = _home_page + main_id
    # content = get_content(url)
    info = get_user_info(main_id)
    if info != None:
        print "test finished...\nconnecting to database..."
    else:
        print "test failed..."
        sys.exit(-2)
    connect_db(info)


if __name__ == "__main__":
    main()
