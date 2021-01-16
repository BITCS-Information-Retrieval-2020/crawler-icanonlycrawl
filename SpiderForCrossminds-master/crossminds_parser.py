import json
from tqdm import tqdm
from crossminds_saver import crossminds_saver
from crossminds_scrapy import crossminds_scrapy
from bs4 import BeautifulSoup
import re
import time
from multiprocessing.dummy import Pool


class crossminds_parser:
    def parse_title(self, item):
        # todo:title处理 不同会议的怎么处理
        raw_title = item["title"]
        return raw_title

    def parse_author(self, item, rawpdfurl):
        authors = ''
        if 'arxiv.org/abs' in rawpdfurl:
            try:
                result = crossminds_scrapy().get_content(rawpdfurl).decode()
                soup = BeautifulSoup(result, 'lxml')
                div = soup.find('div', class_='authors')
                a = div.find_all('a')
                for i in a:
                    authors += i.get_text() + ','
                authors = authors[:-1]
            except Exception:
                print("parse_author error")
        # authors从description里找 没有的话再直接用json中的author字段
        # authors部分比起摘要变化太多了，正则表达式实在不会写了，就直接用json中的字段吧
        if authors == '' or authors is None:
            authors = item["author"]["name"]
        return authors

    def parse_publicationorg(self, item):
        string = ' '
        publicationorg = string.join(item["category"][0].split(' ')[0:-1])
        return publicationorg

    def parseurl_fromweb(self, item):
        rawpdfurl = ''
        rawcodeurl = ''
        _id = item["foreign_id"]
        url = "https://crossminds.ai/video/{}/".format(_id)
        result = crossminds_scrapy().get_content(url).decode()
        soup = BeautifulSoup(result, 'lxml')
        divs = soup.find('div', class_='video-attached-link')
        if divs is not None:
            a = divs.find_all('a')
            for i in a:
                spans = i.find_all('span')
                # print(spans)
                for span in spans:
                    text = span.contents[0]
                    # print("text: " ,text)
                    if text == "Paper Link":
                        rawpdfurl = i["href"]
                    elif text == "Code Link":
                        rawcodeurl = i["href"]
                if rawpdfurl != '' and rawcodeurl != '':
                    break
        return rawpdfurl, rawcodeurl

    def parseurl_fromdescription(self, item):
        rawpdfurl = ''
        rawcodeurl = ''
        string = item["description"]
        # print("description: \n", string)
        urls = re.findall(
            'https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]',
            string)
        # print("urls: ", urls)
        for url in urls:
            if "github.com" in url:
                rawcodeurl = url
            if "arxiv.org" in url:
                rawpdfurl = url
            if "aclweb.org/" in url:
                rawpdfurl = url
            if rawpdfurl != '' and rawcodeurl != '':
                break
        return rawpdfurl, rawcodeurl

    def parse_url(self, item):
        rawpdfurl = ''
        rawcodeurl = ''
        pdfurl1 = ''
        codeurl1 = ''
        pdfurl2 = ''
        codeurl2 = ''
        # 从网页中解析出url
        try:
            pdfurl1, codeurl1 = self.parseurl_fromweb(item)
        except Exception:
            print("url解析错误")
        # 从description中解析
        try:
            pdfurl2, codeurl2 = self.parseurl_fromdescription(item)
        except Exception:
            print("url解析错误")
        if pdfurl1 != '':
            rawpdfurl = pdfurl1
        else:
            rawpdfurl = pdfurl2
        if codeurl1 != '':
            rawcodeurl = codeurl1
        else:
            rawcodeurl = codeurl2
        # 处理得到的url
        pdfurl = ''
        codeurl = ''
        if "arxiv.org" in rawpdfurl:
            pdfurl = rawpdfurl.replace('abs', 'pdf') + '.pdf'
        if "aclweb.org" in rawpdfurl:
            pdfurl = rawpdfurl[:-1] + ".pdf"
        codeurl = rawcodeurl
        return rawpdfurl, pdfurl, codeurl

    def parse_abstractfromrawpdf(self, item, rawpdfurl):
        # print("rawpdfurl:", rawpdfurl)
        if 'arxiv.org/abs' in rawpdfurl:
            # 如果返回的pdfurl是arxiv的，可以从arxiv中解析abstract
            abstract = ''
            result = crossminds_scrapy().get_content(rawpdfurl).decode()
            soup = BeautifulSoup(result, 'lxml')
            blockquotes = soup.find('blockquote', class_="abstract mathjax")
            # print(blockquotes)
            if blockquotes is not None:
                abstract = blockquotes.contents[2].strip()
                # print(abstract)
            return abstract

    def parse_abstractfromcurpage(self, item):
        # 从当前paper的description中解析，先判断有无abstract字样，有的话根据回车提取？
        description = item["description"]
        # print(description)
        abstract = ''
        if re.search('abstract', description, re.IGNORECASE) is not None:
            result = re.findall('(?i)abstract.*\n*.*\n*', description)
            # print("result: \n",result)
            result = re.sub('(?i)abstract[^(a-z|A-Z|0-9)]*', '', result[0])
            result = re.sub('\n.*', '', result)
            result = result.strip()
            if result != '' and result[-1] == '\"':
                result = result[:-1]
            # print("result: \n",result)
            if len(result) > 100:
                abstract = result
            return abstract
        else:
            return abstract

    def parse_abstract(self, item, rawpdfurl):
        abstract = ''
        try:
            abstract = self.parse_abstractfromrawpdf(item, rawpdfurl)
        except Exception:
            print("parse_abstractfromrawpdf error")
        if abstract == '' or abstract is None:
            try:
                abstract = self.parse_abstractfromcurpage(item)
            except Exception:
                print("parse_abstractfromcurpage error")
        return abstract

    def perparse(self, item):
        # for i in tqdm(range(len(json_results))):
        #     item = json_results[i]
        title = self.parse_title(item)
        videourl = item["video_url"]
        year = item["created_at"][0:4]
        publicationorg = self.parse_publicationorg(item)
        rawpdfurl, pdfurl, codeurl = self.parse_url(item)
        dataseturl = ''
        videopath = ''
        pdfpath = ''
        abstract = self.parse_abstract(item, rawpdfurl)
        authors = self.parse_author(item, rawpdfurl)
        publicationurl = ''
        _id = item["foreign_id"]

        # videopath = oral_video_download(videourl, title)
        # pdfpath = pdf_download(pdfurl, title)

        paperinfo = {
            "_id": _id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "publicationOrg": publicationorg,
            "year": year,
            "pdfUrl": pdfurl,
            "pdfPath": pdfpath,
            "publicationUrl": publicationurl,
            "codeUrl": codeurl,
            "datasetUrl": dataseturl,
            "videoUrl": videourl,
            "videoPath": videopath
        }

        crossminds_saver().save_paperinfo(paperinfo)

    def parser(self, items):
        json_results = []
        for i in range(len(items)):
            for j in range(len(json.loads(items[i])["results"])):
                json_results.append(json.loads(items[i])["results"][j])

        start = time.time()
        pool = Pool()
        for _ in tqdm(pool.imap(self.perparse, json_results), total=len(json_results)):
            pass
        # pool.apply(self.perparse,json_results)
        end = time.time()
        pool.close()
        pool.join()
        print('BASIC-finished--timestamp:{:.3f}'.format(end - start))
        # for i in tqdm(range(len(json_results))):
        #     item = json_results[i]
        #     title = self.parse_title(item)
        #     videourl = item["video_url"]
        #     year = item["created_at"][0:4]
        #     publicationorg = self.parse_publicationorg(item)
        #     rawpdfurl, pdfurl, codeurl = self.parse_url(item)
        #     dataseturl = ''
        #     videopath = ''
        #     pdfpath = ''
        #     abstract = self.parse_abstract(item, rawpdfurl)
        #     authors = self.parse_author(item, rawpdfurl)
        #     publicationurl = ''
        #     _id = item["_id"]

        #     # videopath = oral_video_download(videourl, title)
        #     # pdfpath = pdf_download(pdfurl, title)

        #     paperinfo = {
        #         "_id": _id,
        #         "title": title,
        #         "authors": authors,
        #         "abstract": abstract,
        #         "publicationOrg": publicationorg,
        #         "year": year,
        #         "pdfUrl": pdfurl,
        #         "pdfPath": pdfpath,
        #         "publicationUrl": publicationurl,
        #         "codeUrl": codeurl,
        #         "datasetUrl": dataseturl,
        #         "videoUrl": videourl,
        #         "videoPath": videopath
        #     }

        #     # print("id: ", _id)
        #     # print("title: ", title)
        #     # print("authors: ", authors)
        #     # print("abstract: ", abstract)
        #     # print("year: ", year)
        #     # print("publicationOrg: ", publicationorg)
        #     # print("pdfurl: ", pdfurl)
        #     # print("pdfPath: ", pdfpath)
        #     # print("videoUrl: ", videourl)
        #     # print("videoPath: ", videopath)
        #     # print("datasetUrl: ", dataseturl)
        #     # print("publicationUrl: ", publicationurl)
        #     # print("codeurl: ", codeurl)

        #     crossminds_saver().save_paperinfo(paperinfo)
