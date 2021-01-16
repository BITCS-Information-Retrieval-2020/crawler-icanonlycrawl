# coding : utf-8
import json

import pymongo
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import utils.config as config
from utils.ClashControl import ClashControl
from utils.PDFDownloader import PDFDownloader
import time
from multiprocessing.dummy import Pool


class detailInfoCrawler:
    database = config.db
    url_collection = config.url_collection
    info_collection = config.info_collection
    clashControl = ClashControl()

    def __init__(self):
        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)
        self.clash_proxy = {
            "http": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port,
            "https": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port
        }
        self.pdfDownLoader = PDFDownloader()

    def get_content(self, u):
        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "\
                "Chrome/77.0.3865.90 Safari/537.36"
            response = requests.get(u, headers={'User-Agent': user_agent})
            # pdb.set_trace()
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
            response.encoding = response.apparent_encoding  # 判断网页的编码格式， 便于respons.text知道如何解码;

        except Exception:
            print("爬取错误")
        else:
            return response.content

    def getUnvisitedUrls(self):
        '''
        获取数据库中已保存且未爬取的url
        :return:
        '''
        db = self.client[self.database]
        col = db[self.url_collection]
        urls = col.find({"visit": False}, {"url": 1})
        urls = [url['url'] for url in urls]
        return urls

    def updateUrl(self, url):
        '''
            已经爬过的url更新数据库的visit标记
        :param url:
        :return:
        '''
        db = self.client[self.database]
        col = db[self.url_collection]
        col.update_one({"url": url}, {"$set": {"visit": True}})

    def getDetailInfo(self, url):
        content = self.get_content(url)
        soup = BeautifulSoup(content, 'lxml')

        title = soup.find("h1", attrs={'class': "title"}).text[6:]
        authors = soup.find("div", attrs={'class': "authors"}).text
        abstract = soup.find("blockquote", attrs={
                             'class': "abstract"}).text[12:]
        year = soup.find("div", attrs={'class': "dateline"}).text
        pdfUrl = "https://arxiv.org" + \
            soup.find("a", attrs={'class': "download-pdf"})['href'] + '.pdf'

        extra_content = requests.get(
            "https://arxiv.paperswithcode.com/api/v0/papers/" + url.split('/')[-1]).content

        publicationUrl = json.loads(extra_content)['paper_url']  # pub_url
        # codeUrl = soup.find_all("div", attrs={'class': "tab"})
        if json.loads(extra_content)['official'] is not None:
            codeUrl = json.loads(extra_content)['official']['url']
        else:
            codeUrl = ""
        detailInfo = {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "publicationOrg": "arxiv.org",
            "year": year,
            "pdfUrl": pdfUrl,
            "pdfPath": "",
            "publicationUrl": publicationUrl,
            "codeUrl": codeUrl,
            "datasetUrl": "",
            "videoUrl": "",
            "videoPath": ""
        }
        return detailInfo

    def saveDetailInfo(self, detailInfo):
        db = self.client[self.database]
        col = db[self.info_collection]
        # 检查标题重复
        if (col.find_one({"title": detailInfo["title"]}) is not None):
            return
        # todo: _id
        col.insert_one(detailInfo)

    def crawlperInfo(self, url):
        try:
            # pbar.set_description("Crawling %s" % url)
            detailInfo = self.getDetailInfo(url)
            self.saveDetailInfo(detailInfo)
            print(detailInfo)
            pdfurl = detailInfo["pdfUrl"]
            self.pdfDownLoader.addUrl(pdfurl)
            self.updateUrl(url)
        except Exception:
            print("Error in " + url + ", pass")
            return

    def crawlAllInfo(self):
        '''
        1.获取所有unvisitedurl
        2.解析这些url
        3.更新unvisitedurl的状态，写入解析出来的detailInfo
        '''
        urls = self.getUnvisitedUrls()
        start = time.time()
        pool = Pool()
        for _ in tqdm(pool.imap(self.crawlperInfo, urls), total=len(urls)):
            pass
        # pool.map(self.crawlperInfo,urls)
        end = time.time()
        pool.close()
        pool.join()
        print('BasicInfofinished--timestamp:{:.3f}'.format(end - start))
        # for url in pbar:
        #     try:
        #         pbar.set_description("Crawling %s" % url)
        #         detailInfo = self.getDetailInfo(url)
        #         self.saveDetailInfo(detailInfo)
        #         print(detailInfo)
        #         pdfurl = detailInfo["pdfUrl"]
        #         self.pdfDownLoader.addUrl(pdfurl)
        #         self.updateUrl(url)
        #     except Exception:
        #         print("Error in " + url + ", pass")
        #         continue
        print("Detail info crawler finished.")


if __name__ == '__main__':
    detailInfoCrawler = detailInfoCrawler()
    detailInfoCrawler.crawlAllInfo()
