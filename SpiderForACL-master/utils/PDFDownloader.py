import pymongo
import requests
from tqdm import tqdm
import utils.config as config
import LevelUrls as lu
from ContentDownloader import ContentManager
import time
from multiprocessing.dummy import Pool


class PDFManager():
    '''
    爬取论文pdf
    '''
    database = config.db
    collection = "PDF"
    paper = ContentManager.collection

    def __init__(self):
        # self.database = "ACLAnthology"

        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)
        self.pdfUrls = self.getPDFUrlsfromDB()

    def getPDFUrlsfromDB(self):
        db = self.client[self.database]
        col = db[self.collection]
        return [url['url'] for url in col.find({"visit": False})]

    def get_content(self, url):
        try:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64)"\
                " AppleWebKit/537.36 (KHTML, like Gecko)"\
                " Chrome/59.0.3071.109 Safari/537.36"
            response = requests.get(url, headers={'User-Agent': user_agent})
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
            # 判断网页的编码格式， 便于respons.text知道如何解码;
            response.encoding = response.apparent_encoding
        except Exception:
            print("爬取错误")
        else:
            return response.content

    def downloadFile(self, url, fileName):
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"\
            " Chrome/59.0.3071.109 Safari/537.36"
        r = requests.get(url, headers={'User-Agent': user_agent}, stream=True)
        with open(fileName, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return

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

    def reset(self):
        '''
        所有的pdf url visit置false
        :return:
        '''
        db = self.client[self.database]
        col = db[self.collection]
        col.update_many({}, {"$set": {"visit": False}})

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

    def pdfrun(self, pdfurl):
        try:
            # pbar.set_description("Crawling %s" % pdfurl)
            pdfurlSplit = pdfurl.split("/")
            fileName = pdfurlSplit[len(pdfurlSplit) - 1]
            self.downloadFile(pdfurl, "./data/PDFs/" + fileName)
            self.updateUrl(pdfurl, "/data/PDFs/" + fileName)
        except Exception as e:
            lu.ErrorUrlManeger(pdfurl, e)

    def run(self):
        start = time.time()
        pool = Pool()
        for _ in tqdm(pool.imap(self.pdfrun, self.pdfUrls), total=len(self.pdfUrls)):
            pass
        # pool.map(self.pdfrun,self.pdfUrls)
        end = time.time()
        pool.close()
        pool.join()
        print('PDFfinished--timestamp:{:.3f}'.format(end - start))
        # pbar = tqdm(self.pdfUrls)
        # for pdfurl in pbar:
        # 	try:
        # 		pbar.set_description("Crawling %s" % pdfurl)
        # 		pdfurlSplit = pdfurl.split("/")
        # 		fileName = pdfurlSplit[len(pdfurlSplit) - 1]
        # 		self.downloadFile(pdfurl, "./data/PDFs/" + fileName)
        # 		self.updateUrl(pdfurl, "/data/PDFs/" + fileName)
        # 	except Exception as e:
        # 		lu.ErrorUrlManeger(pdfurl,e)
        print('PDF downloading done--timestamp:{:.3f}'.format(end - start))


if __name__ == '__main__':
    pdfManager = PDFManager()
    pdfManager.reset()
