# coding : utf-8
import pymongo
import utils.config as config
import requests
from bs4 import BeautifulSoup
from ClashControl import ClashControl


class UrlCrawler:
    database = config.db
    urlCollection = config.url_collection
    clashControl = ClashControl()

    def __init__(self):
        '''
        爬取规则：
        从 https://portal.paperswithcode.com/ 可知paperwithcode目前有六个分类，
        分别为machine learning,computer science,physics,mathematics,astronomy
        ,statistics
        进入后默认按照trending排序,每页十个内容，内容是有限的
        进入详情后找到该项的abstract，进入arvix.org下的网页，该网页则包括了该向的所有信息，包括pdf和代码链接
        所以UrlCrawler的功能就是找到所有的 arvix.org/*
        '''
        self.portalList = [
            "https://paperswithcode.com",  # machine learning
            "https://cs.paperswithcode.com",  # computer science
            "https://physics.paperswithcode.com",  # physics
            "https://math.paperswithcode.com",  # math
            "https://astro.paperswithcode.com",  # astronomy
            "https://stat.paperswithcode.com",  # statistics
        ]

        self.portalName = ["Machine Learning", "Computer Science",
                           "Physics", "Math", "Astronomy", "Statistics"]

        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)
        self.clash_proxy = {
            "http": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port,
            "https": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port
        }

    def getProgress(self):
        with open("./progress", 'r+') as f:
            status = f.readlines()
            f.close()

        for i in range(0, len(status)):
            status[i] = status[i].rstrip('\n')
        # status line 2n = 1 indicates that
        # this part finished, 0 for un-finished
        #        line 2n+1 = x indicates that this part has crawled x pages
        for i in range(0, 12):
            if i % 2 == 1:
                continue
            if i % 2 == 0 and status[i] == '0':
                page = int(status[i + 1])
                print("Part " + self.portalName[int((i + 1) / 2)]
                      + " in progress, starting from page " + status[i + 1])
                break
            elif i % 2 == 0 and status[i] == '1':
                print(
                    "Part " + self.portalName[int((i + 1) / 2)] + " finished. Pass.")

        type = int((i + 1) / 2)
        if i < 11:
            page = int(status[i + 1])
        else:
            page = int(status[i])
        return type, page, status
        # with open("./progress", 'w') as f:
        #     for item in status:
        #         f.write(item + '\n')
        #     f.close()

    def get_content(self, url):
        try:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                         "Chrome/77.0.3865.90 Safari/537.36"
            response = requests.get(
                url, headers={'User-Agent': user_agent}, proxies=self.clash_proxy)
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
            response.encoding = response.apparent_encoding  # 判断网页的编码格式， 便于respons.text知道如何解码;
        except Exception:
            print("爬取错误")
        else:
            return response.content

    def saveUrls(self, urls):
        db = self.client[self.database]
        col = db[self.urlCollection]
        urlsInDB = col.find({}, {"url": 1})
        urlsInDB = [urls['url'] for urls in urlsInDB]

        Urls = []
        for url in urls:
            if (url in urlsInDB):
                # 去重
                continue
            else:
                Urls.append({"url": url, "visit": False})
        if len(Urls) == 0:
            return
        col.insert_many(Urls)

    def crawlUrlInPage(self, url, type):
        try:
            # current_url = self.portalList[type] + '?page=' + str(page)
            content = self.get_content(url)
            soup = BeautifulSoup(content, 'lxml')
            papers = soup.find_all("a", attrs={'class': "badge badge-dark"})
            real_urls = []
            for paper in papers:
                pwcUrl = self.portalList[type] + paper["href"].split("#")[0]
                # print(pwcUrl)
                if "/paper/" not in pwcUrl:
                    continue
                temp_content = self.get_content(pwcUrl)
                temp_soup = BeautifulSoup(temp_content, 'lxml')
                real_url = temp_soup.find_all(
                    "a", attrs={'class': "badge"})[1]['href']
                if "openreview" in real_url:
                    continue
                print(pwcUrl, real_url)
                real_urls.append(real_url)
            return real_urls, content
        # 除了return当页中的真实链接外，还要返回当页的内容，用于判断是否已经翻到结束
        except Exception as e:
            print(e)
            exit(-1)

    '''
    流程：
    1.获取当前进度，从第x个分类的第y页开始爬取；
    2.爬取完当前页后写入数据库，获取当前页的内容
    3.每爬取一页需要更新一次进度记录
    4.下一页开始前与当前页的内容进行比较，判断内容是否已经到底
    5.爬取完全部六个分类后工作结束
    '''

    def crawlAll(self):
        type, page, status = self.getProgress()
        if status[10] == '1':
            print('urlCrawl finished.')
            return

        for category in range(type, len(self.portalList)):
            print("Starting crawl " + self.portalName[category] + " from page " + str(page) + "...")
            is_end = False
            real_urls = []
            while not is_end:
                current_url = self.portalList[category] + "/?page=" + str(page)
                temp_urls, content = self.crawlUrlInPage(current_url, category)
                if temp_urls == real_urls:
                    print(
                        self.portalName[category] + " comes to an end, finish this part & update progress")
                    is_end = True
                    status[category * 2] = '1'
                    status[category * 2 + 1] = str(page - 1)
                    with open("./progress", 'w') as f:
                        for item in status:
                            f.write(item + '\n')
                        f.close()
                    break
                real_urls = temp_urls[:]
                self.saveUrls(real_urls)
                # 爬取完毕，更新状态
                print(self.portalName[category] + " page " + str(page) + " finished. Next Page...")
                page = page + 1
                status[category * 2 + 1] = str(page)
                with open("./progress", 'w') as f:
                    for item in status:
                        f.write(item + '\n')
                    f.close()
            page = 1

        print("Paper with code urls crawl finished.")


if __name__ == '__main__':
    urlCrawler = UrlCrawler()
    # urlCrawler.crawlUrl()
    urlCrawler.crawlAll()
