# -*- coding: UTF-8 -*-
from urllib.parse import urlencode
import requests
from lxml import etree
from pyquery import PyQuery as pq
from requests.exceptions import ConnectionError
import pymongo



client=pymongo.MongoClient('localhost')
db=client['weixin']



PROXY_POOL_URL = 'http://localhost:5000/get'
base_url='http://weixin.sogou.com/weixin?'
headers={'Cookies':'CXID=F2D57324C4F998073C16DF11422B079B; SUID=B82E100E4C238B0A59704D290009AE31; SUV=002F4373DF49686C59C714107D5B2985; ABTEST=0|1506647719|v1; IPLOC=CN4409; JSESSIONID=aaaDseV3vbItQ-o1c9y6v; ld=MZllllllll2B8zxVlllllVX2o9UlllllT1OoNZllll9lllll4ylll5@@@@@@@@@@; LSTMV=1316%2C27; LCLKINT=1176; weixinIndexVisited=1; ppinf=5|1506652711|1507862311|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyOlVMfGNydDoxMDoxNTA2NjUyNzExfHJlZm5pY2s6MjpVTHx1c2VyaWQ6NDQ6bzl0Mmx1TE5rY0hKT3RMcURfX1NPT0RNMS03b0B3ZWl4aW4uc29odS5jb218; pprdig=XUnYTiTgEJrV2Eul9Cr8-Pws6tyVA9nRu4ZkHGcJd5FVnkb9gWAgFjGY4ybex6a1vFrP2Cj4XVl3PZt_VjnZzXI1VWdQiXSnwaSQcr1Cmo-vhqd06NUCja5bteZY5GnNTYF3e1O8mzzKlrMepZp0kloSe39gzaaWsKLEqLlWGo4; sgid=29-31147699-AVnNsiafiamiaNyicawR7Pdb9YE; PHPSESSID=55v3a8ofn8lqilmf425gtboqq5; SNUID=4B87A730EEEAB403E7A330A6EFFDD5C7; ppmdig=15073446810000006c5fd7302b7a07786fe5e9f8c39a4121; sct=4',
         'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
keyword='风景'
max_count=5
proxy=None


def get_index(url,count=1):#get index
    print('Crawling',url)
    print('Try Count',count)
    global proxy
    if count >= max_count:
        print('Tried Too Many Counts')
        return None
    try:
        if proxy:
            proxies={
                'http':'http://'+proxy
            }
            # print(proxies)
            html=requests.get(url=url,headers=headers,allow_redirects=False,proxies=proxies)
        else:
            html = requests.get(url=url, headers=headers, allow_redirects=False)
        if html.status_code==200:
                data=html.text
                return data

        if html.status_code==302:
            print('302')
            proxy=get_proxy()
            if proxy:
                print('using proxy',proxy)
                return get_index(url,count)
            else:
                print('get proxy failed')
                return None
    except ConnectionError as e:
        print('ERROR Occurred',e.args)
        proxy=get_proxy()
        count+=1
        return get_index(url,count)


def parse_index(html):
    list = etree.HTML(html).xpath('//div[@class="txt-box"]/h3/a/@href')
    return list


def get_detail(url):
    print('crawing',url)
    html0 = requests.get(url=url, headers=headers, allow_redirects=False).text
    return html0


def parse_detail(html):
    if html:
        dat = pq(str(html))
        title = dat('.rich_media_title').text()
        content = dat('.rich_media_content').text()
        data = dat('#post-date').text()
        nickname = dat('.rich_media_meta_list .rich_media_meta_nickname').text()
        wechat = dat(
            '#js_content > section:nth-child(6) > section:nth-child(20) > section:nth-child(8) > section > section > section > p:nth-child(1) > strong').text()
        return {
            'title': title,
            'content': content,
            'data': data,
            'nickname': nickname,
            'wechat': wechat
        }



def save_to_mongo(data):
    if db['articles'].update({'title':data['title']},{'$set':data},True):
        print('Save To Mongo',data['title'])
    else:
        print('Save To Mongo Failed ',data['title'])



def get_html(page):
    data={
        'query':keyword,
        'type':2,
        'page':page
    }
    queries=urlencode(data)
    url=base_url+queries
    html=get_index(url)
    return html


def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
    except ConnectionError:
        return None


def main():
    for page in range(1,3):
        html=get_html(page=page)
        list=parse_index(html)
        for url in list:
            ht=get_detail(url)
            detail_data=parse_detail(ht)
            print(detail_data)
            save_to_mongo(detail_data)




if __name__ == '__main__':
    # pool=Pool()
    # pool.map(main,[ page for page in range(101) ])
    main()


