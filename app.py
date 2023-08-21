from urllib import request as urlrequest
import gzip
from bs4 import BeautifulSoup
import os
import multiprocessing
import argparse
import re
import brotli


def getHeads(cookies):
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': cookies,
        'Host': 'exhentai.org',
        'Referer': 'https://exhentai.org',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
    }


def download(url, name):
    img = urlrequest.urlopen(url)
    with open(name, 'wb') as imgFile:
        imgFile.write(img.read())


def getpic(url, headers, pool, proxy=None):
    req = urlrequest.Request(url)
    if proxy:
        req.set_proxy(proxy, 'http')
    req.headers = headers

    response = urlrequest.urlopen(req)
    if response.getheader("Content-Encoding", ""):
        targetHtml = brotli.decompress(response.read())
    else:
        gzipFile = gzip.GzipFile(fileobj=response)
        #
        targetHtml = gzipFile.read().decode('utf8')
    soup = BeautifulSoup(targetHtml, features='html.parser')
    # 图片真实链接
    picSrc = soup.find(id='img').attrs['src']
    ext = picSrc.split('.')[-1]
    # 分析页码
    title = soup.title.get_text()
    title = re.sub("[\/\\\:\*\?\"\<\>\|]", "_", title)
    i2 = soup.find(id='i2')
    i2span = i2.find_all('span')
    currentPage = int(i2span[0].get_text())
    totalPage = int(i2span[1].get_text())
    # 下载图片并保存
    if not os.path.exists(title):
        os.mkdir(title)
    # download(picSrc,title+'/'+str(currentPage)+'.'+ext)
    pool.apply_async(download, (picSrc, title + '/' +
                     str(currentPage) + '.' + ext))

    # 继续爬下一页
    if currentPage < totalPage:
        netxUrl = i2.find(id='next').attrs['href']
        getpic(netxUrl, headers, pool, proxy)
    else:
        print('finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', dest='url', required=True,
                        help='start url,must be exhentai\'s gallery view page,like \'https://exhentai.org/s/0fea511044/1207481-1\'')
    parser.add_argument('-c', '--cookies', dest='cookies', required=True,
                        help='cookies,string like \'key1=54321; key2=qwerty;\'')
    parser.add_argument('-p', '--proxy', dest='proxy',
                        required=False, help='proxyIp:port,http only')
    args = parser.parse_args()
    url = args.url
    cookiesText = args.cookies
    proxy = args.proxy

    pool = multiprocessing.Pool()
    getpic(url, getHeads(cookiesText), pool, proxy)
    pool.close()
    pool.join()
    print('完成')
