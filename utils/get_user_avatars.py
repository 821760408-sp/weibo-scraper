'''
infomation Url: https://weibo.cn/id/infomation
'''

import requests
import ConfigParser
from bs4 import BeautifulSoup as bs
import shutil
# import time


home_uri = 'http://weibo.cn/'
avatar_uri = '/avatar?rl=0'

config = ConfigParser.ConfigParser()
config.read('../config.ini')

def get_url_id_list(list_path):
    with open(list_path, 'r') as f:
        usr_ids = [x.split('\t')[1] for x in f.readlines()]
    if usr_ids is not None:
        usr_id_list = set(usr_ids)
    return usr_id_list

def run(usr_id_list):
    for usr_id in usr_id_list:
        url = ''.join([home_uri, usr_id, avatar_uri])
        img_url = get_usr_avatar_url(url)
        save_path = ''.join(['../avatars/', usr_id, '.jpg'])
        get_usr_avatar(img_url, save_path)

def get_url_content(url):
    cookie = config.get('cookie', 'cookie')
    try:
        res = requests.get(url, cookies=dict(Cookie=cookie), timeout=100)
    except:
        return None
    if res.status_code != requests.codes.ok:
        print "Not getting 200; status_code is: " + str(res.status_code);
        sys.exit(-1)
    return res

def get_usr_avatar_url(url):
    # time.sleep(2)
    res = get_url_content(url)
    if res:
        soup = bs(res.text, 'html.parser')
        img_url = soup.find('img').get('src')
        return img_url

def get_usr_avatar(img_url, save_path):
    res = requests.get(img_url, stream=True)
    if res.status_code == requests.codes.ok:
        with open(save_path, 'wb') as f:
            res.raw.decode_content = True
            shutil.copyfileobj(res.raw, f)

def main():
    tweet_list_path = '../tweet-list-alleng.txt'
    usr_id_list = get_url_id_list(tweet_list_path)
    run(usr_id_list)

if __name__ == '__main__':
    main()