# coding : utf-8
import time
import pymongo
import requests
from tqdm import tqdm
import utils.config as config
from utils.ClashControl import ClashControl
from multiprocessing.dummy import Pool


class PDFDownloader():
    database = config.db
    collection = config.pdf_Collection
    paper = config.info_collection

    def __init__(self):
        # self.database = "ACLAnthology"

        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)
        self.pdfUrls = self.getPDFUrlsfromDB()
        self.clashControl = ClashControl()
        self.clash_proxy = {
            "http": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port,
            "https": "http://" + self.clashControl.clash_host + ":" + self.clashControl.proxy_port
        }

    def getPDFUrlsfromDB(self):
        db = self.client[self.database]
        col = db[self.collection]
        return [url['url'] for url in col.find({"visit": False})]

    def get_content(self, url):
        try:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                         " Chrome/59.0.3071.109 Safari/537.36"
            response = requests.get(url, headers={'User-Agent': user_agent})
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
            response.encoding = response.apparent_encoding
            # 判断网页的编码格式， 便于respons.text知道如何解码;
        except Exception:
            print("爬取错误")
        else:
            return response.content

    def reset(self):
        '''
        所有的pdf url visit置false
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        col.update_many({}, {"$set": {"visit": False}})

    def updateUrl(self, url, filePath):
        '''
            已经爬过的pdf更新数据库的visit标记
        :param url:
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        ACLAnthology = db[self.paper]
        # visit标记设为true
        col.update_one({"url": url}, {"$set": {"visit": True}})
        # 更新paper信息中的pdf的文件路径
        ACLAnthology.update_one({"pdfUrl": url},
                                {"$set": {
                                    "pdfPath": filePath
                                }})

    def addUrl(self, url):
        '''
            加入待爬取的pdf的url
        :param url:
        :return:
        '''
        if (url == ""):
            return
        db = self.client[self.database]
        col = db[self.collection]
        if col.find_one({"url": url}) is None:
            col.insert_one({"url": url, "visit": False})
        return

    def downloadFile(self, url, fileName):
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                     " Chrome/59.0.3071.109 Safari/537.36"
        r = requests.get(
            url, headers={'User-Agent': user_agent}, proxies=self.clash_proxy, stream=True)
        with open(fileName, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return

    def downloadAll(self):
        pbar = tqdm(self.pdfUrls)
        count = 0
        # pool = Pool()
        for pdfurl in pbar:
            try:
                pbar.set_description("Crawling %s" % pdfurl)
                pdfurlSplit = pdfurl.split("/")
                fileName = pdfurlSplit[len(pdfurlSplit) - 1]
                print("Downloading: " + pdfurl + ", filename: " + fileName)
                self.downloadFile(pdfurl, "./data/PDFs/" + fileName)
                self.updateUrl(pdfurl, "/data/PDFs/" + fileName)
                count = count + 1
                if count > 10:
                    if self.clashControl.changeRandomAvailableProxy():
                        count = 0
                        time.sleep(5)
            except Exception as e:
                print("Error in " + pdfurl + ", info:", e)
                continue
        print("PDF downloading done")


if __name__ == '__main__':
    pdfDownloader = PDFDownloader()
    # pdfDownloader.reset()
    pdfDownloader.downloadAll()
