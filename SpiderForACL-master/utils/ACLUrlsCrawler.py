import pymongo
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pdb
import os
import utils.config as config
import utils.LevelUrls as lu
import sys


def log(str):
    with open("../url.text", "a") as f:
        f.write(str)


class ACLUrlsCrawler:
    database = config.db  # 爬取的url将要保存的数据库名
    collection = "Urls"  # 爬取的url将要保存的表名
    finishflag = "finish"  # 爬取url结束后保存的表名，有内容表明可以直接从数据库中读，否则爬取url

    def __init__(self):
        os.system('')
        self.baseUrl = "https://www.aclweb.org"
        '''
        约定 https://www.aclweb.org/anthology/ 为顶层
             https://www.aclweb.org/anthology/venues/anlp/ 为2级
             https://www.aclweb.org/anthology/events/anlp-2000/ 为1级
             https://www.aclweb.org/anthology/A00-1000/ 为0级
        '''
        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)

    def getACLUrls(self):
        ACLUlrs = []
        if self.checkIfhasScrawl():
            # 已经爬取过，从数据库中获取未爬取过的url
            ACLUlrs += self.getUnvisitedUrls()
        else:
            # 爬取所有论文的url并保存在数据库中
            print("start to crawl paper urls...")
            ACLUlrs += self.getUrlsfromTopLevel(self.baseUrl + "/anthology/")
        print("urls downloading done")
        return ACLUlrs

    def get_content(self, u):
        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "\
                "Chrome/77.0.3865.90 Safari/537.36"
            response = requests.get(u, headers={'User-Agent': user_agent})
            # pdb.set_trace()
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
            response.encoding = response.apparent_encoding  # 判断网页的编码格式， 便于respons.text知道如何解码;

        except Exception:
            # print('\033'+response+'\033')
            # print("----------------")
            # print(u)
            # print("----------------")
            print("爬取错误")
        else:
            # print(response.url)
            return response.content

    def getUrlsfromFirstLevel(self, firstlevel: str):
        '''
        :param firstlevel: 1级url ttps://www.aclweb.org/anthology/events/anlp-2000/
        :return: 返回0级url
        '''
        try:
            content = self.get_content(firstlevel)
            soup = BeautifulSoup(content, 'lxml')
            papers = soup.find_all(name="p",
                                   attrs={"class": "align-items-stretch"})
            paperUrls = []
            for paper in papers:
                paperUrl = paper.find(name="strong").find("a")["href"]
                paperUrls.append(self.baseUrl + paperUrl)
            return paperUrls
        except Exception as e:
            lu.ErrorUrlManeger(firstlevel, e)
            return []

    def getUrlsfromSecondLevel(self, secondlevel: str):
        '''
        :param secondlevel: 2级url https://www.aclweb.org/anthology/venues/anlp/
                                https://www.aclweb.org/anthology/sigs/sigann/ 两种url处理方法略有不同
        :return:
            成功返回 true,urls
            出错返回 false,[]
        '''
        paperUrls = []
        FirstLevelUrls = []
        if "venues" in secondlevel:
            try:
                content = self.get_content(secondlevel)
                soup = BeautifulSoup(content, 'lxml')
                paperAccordingToYear = soup.find_all(name="div",
                                                     attrs={"class": "row"})

                for paper in paperAccordingToYear:
                    yearUrl = paper.find(name="h4").find(name="a")['href']
                    FirstLevelUrls.append(self.baseUrl + yearUrl)

                pbar = tqdm(FirstLevelUrls)
                for FirstLevelUrl in pbar:
                    pbar.set_description("Crawling %s" % FirstLevelUrl)
                    partUrls = self.getUrlsfromFirstLevel(FirstLevelUrl)
                    log("\t" + FirstLevelUrl + ":" + str(len(partUrls)) + "\n")
                    paperUrls += partUrls
                # print(paperUrls)
                return True, paperUrls
            except Exception as e:
                lu.ErrorUrlManeger(secondlevel, e)
                return False, []
        elif "sigs" in secondlevel:
            try:
                content = self.get_content(secondlevel)
                soup = BeautifulSoup(content, 'lxml')
                a_s = soup.find_all(name="a")
                for a in a_s:
                    if "volumes" in a['href']:
                        FirstLevelUrls.append(self.baseUrl + a['href'])
                pbar = tqdm(FirstLevelUrls)
                for FirstLevelUrl in pbar:
                    pbar.set_description("Crawling %s" % FirstLevelUrl)
                    partUrls = self.getUrlsfromFirstLevel(FirstLevelUrl)
                    log("\t" + FirstLevelUrl + ":" + str(len(partUrls)) + "\n")
                    paperUrls += partUrls
                # print(paperUrls)
                return True, paperUrls
            except Exception as e:
                lu.ErrorUrlManeger(secondlevel, e)
                return False, []

    def getUrlsfromTopLevel(self, toplevel: str):
        '''
        :param toplevel: 网站入口 https://www.aclweb.org/anthology/
        :return:
        '''
        secondLevelManager = lu.SecondLevelManager()
        SecondLevelUrls = []
        if secondLevelManager.getSecondLevelUrls() is None:
            content = self.get_content(toplevel)
            soup = BeautifulSoup(content, 'lxml')
            tbodies = soup.find_all(name="tbody")
            SIGsFLAG = False
            for tbody in tbodies:
                for venue in tbody.find_all(name="th"):
                    try:
                        SecondLevelUrls.append(self.baseUrl + venue.find(name="a")['href'])
                    except Exception:
                        pass

                if (SIGsFLAG is False):
                    trs = tbody.find_all(name="tr")
                    # print(trs)
                    for tr in trs:
                        try:
                            tr = BeautifulSoup(str(tr), 'lxml')
                            if (tr.find(name="th").text == "SIGs"):
                                SIGsFLAG = True
                            else:
                                continue
                            for a in tr.find_all(name="a"):
                                SecondLevelUrls.append(self.baseUrl + a['href'])
                        except Exception as e:
                            # print(tr)
                            print(e)
                            pass

            secondLevelManager.saveSecondLevelUrls(SecondLevelUrls)

        else:
            SecondLevelUrls += secondLevelManager.getSecondLevelUrls()

        paperUrls = []

        pbar = tqdm(SecondLevelUrls)
        for secondLevelUrl in pbar:
            pbar.set_description("Crawling %s" % secondLevelUrl)
            log("From " + secondLevelUrl + ":\n")
            result, partUrls = self.getUrlsfromSecondLevel(secondLevelUrl)
            if result is False:
                continue
            secondLevelManager.updateSecondLevelUrls(secondLevelUrl)

            self.saveUrls(partUrls)
            log("total paper :{length}\n".format(length=len(partUrls)))

            paperUrls += partUrls

        log("total paper in site:{length}\n".format(
            length=len(self.getAllUrls())))
        self.finishFlag()
        # print("total:{}".foramt(len(paperUrls)))
        return paperUrls

    def saveUrls(self, urls):
        '''
        保存爬取的url
        :param urls:
        :return:
        '''

        db = self.client[self.database]
        col = db[self.collection]
        urlsInDB = col.find({}, {"url": 1})
        urlsInDB = [urls['url'] for urls in urlsInDB]

        Urls = []
        for url in urls:
            if (url in urlsInDB):
                # 去重
                continue
            else:
                Urls.append({"url": url, "visit": False})
        if (len(Urls) == 0):
            return
        col.insert_many(Urls)

    def checkIfhasScrawl(self):
        '''
        检查是否已经爬取过url
        :return:
        '''
        db = self.client[self.database]
        col = db[self.finishflag]
        if (col.find_one() is not None):
            return True
        else:
            return False

    def getUnvisitedUrls(self):
        '''
        获取数据库中已保存且未爬取的url
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        urls = col.find({"visit": False}, {"url": 1})
        urls = [url['url'] for url in urls]
        return urls

    def getAllUrls(self):
        '''
            获取数据库中所有的url
            :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        urls = col.find({}, {"url": 1})
        urls = [url['url'] for url in urls]
        return urls

    def finishFlag(self):
        db = self.client[self.database]
        col = db[self.finishflag]
        col.insert_one({"finish": True})

    def updateUrl(self, url):
        '''
            已经爬过的url更新数据库的visit标记
        :param url:
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        col.update_one({"url": url}, {"$set": {"visit": True}})


if __name__ == '__main__':
    aclscrawler = ACLUrlsCrawler()
    # print(aclscrawler.getACLUrls())
    url = "https://www.aclweb.org/anthology/sigs/sigann/"
    print(aclscrawler.get_content(url))
