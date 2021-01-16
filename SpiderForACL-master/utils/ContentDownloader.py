import sys
import pymongo
import requests
from bs4 import BeautifulSoup
import utils.config as config
from ACLUrlsCrawler import ACLUrlsCrawler
sys.path.append('./utils/')


class ContentManager():
    '''
    爬取论文的基本内容
    '''
    database = config.db
    collection = "basicInfo"
    urlCollection = ACLUrlsCrawler.collection

    def __init__(self):
        # self.database = database
        self.client = pymongo.MongoClient(host=config.host,
                                          port=config.port,
                                          username=config.username,
                                          password=config.psw,
                                          authSource=self.database)

    def get_content(self, url):
        try:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"\
                " Chrome/59.0.3071.109 Safari/537.36"
            response = requests.get(url, headers={'User-Agent': user_agent})
            # 如果返回的状态码不是200， 则抛出异常;
            response.raise_for_status()
            # 判断网页的编码格式， 便于respons.text知道如何解码;
            response.encoding = response.apparent_encoding
        except Exception:
            print(url + "   爬取错误")
        else:
            return response.content

    def parse(self, content):
        soup = BeautifulSoup(content, 'lxml')
        title = soup.title.string
        # print(title)
        citation_author_raw = soup.find_all('meta')
        citation_authors = []
        for citation_author in citation_author_raw:
            try:
                if (citation_author.attrs['name'] == "citation_author"):
                    citation_authors.append(citation_author.attrs['content'])
            except Exception:
                pass

        try:
            # 去掉字符串"abstract"
            abstract_tag = soup.find("div", class_="acl-abstract")
            abstract_raw = abstract_tag.text[8:]
            abstract_words_raw = abstract_raw.split(' ')
            abstract_words = []
            for word in abstract_words_raw:
                if word != '':
                    if (word.endswith("\n")):
                        abstract_words.append(word[:-1])
                    else:
                        abstract_words.append(word)
            abstract = " ".join(abstract_words)
        except Exception:
            abstract = ""

        detail_tags = soup.find("div", class_="acl-paper-details").find("dl")
        key_tags = detail_tags.find_all("dt")
        value_tags = detail_tags.find_all("dd")
        details = {}
        for key, value in zip(key_tags, value_tags):
            if (key.text[:-1] == "Dataset"):
                url = value.find("a")['href']
                details[key.text[:-1]] = url
                # downloadFile(url,"./PDFs/"+str(num)+".pdf")
            elif (key.text[:-1] == "Video"):
                url = value.find("a")['href']
                details[key.text[:-1]] = url
            else:
                details[key.text[:-1]] = value.text

        if ("publicationOrg" not in details.keys()):
            details["publicationOrg"] = ""
        if ("Year" not in details.keys()):
            details["Year"] = ""
        if ("PDF" not in details.keys()):
            details["PDF"] = ""
        if ("URL" not in details.keys()):
            details["URL"] = ""
        if ("Dataset" not in details.keys()):
            details["Dataset"] = ""
        if ("Video" not in details.keys()):
            details["Video"] = ""

        return {
            "title": title,
            "authors": ", ".join(citation_authors),
            "abstract": abstract,
            "publicationOrg": details['Publisher'],
            "year": details['Year'],
            "pdfUrl": details['PDF'],
            "pdfPath": "",
            "publicationUrl": details['URL'],
            "codeUrl": "",
            "datasetUrl": details['Dataset'],
            "videoUrl": details['Video'],
            "videoPath": ""
        }

    def savePaperInfo(self, paperInfo):
        db = self.client[self.database]
        col = db[self.collection]
        # 检查标题重复
        if (col.find_one({"title": paperInfo["title"]}) is not None):
            return

        # todo: _id
        col.insert_one(paperInfo)

    def updateUrl(self, url):
        '''
            已经爬过的url更新数据库的visit标记
        :param url:
        :return:
        '''
        db = self.client[self.database]
        col = db[self.urlCollection]
        col.update_one({"url": url}, {"$set": {"visit": True}})
        # col.update_many({}, {"$set": {"visit": False}})

    def reset_id(self):
        db = self.client[self.database]
        col = db[self.collection]
        paperInfo = col.find()
        id = 1
        for paper in paperInfo:
            # print(paper)
            # pdb.set_trace()
            col.update_one({"_id": paper['_id']}, {"$set": {"_id": id}})
            id += 1
        # print(paperInfo[0])

    def run(self, url):
        '''
            爬取，保存并返回论文pdf url和视频 url
        :param url:
        :return:
        '''

        paperInfo = self.parse(self.get_content(url))
        self.savePaperInfo(paperInfo)
        return paperInfo['pdfUrl'], paperInfo['videoUrl']


if __name__ == "__main__":
    contentManager = ContentManager()
    contentManager.reset_id()
