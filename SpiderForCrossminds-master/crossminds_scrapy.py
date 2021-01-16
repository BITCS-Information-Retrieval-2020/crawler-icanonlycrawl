import requests
import json
from requests import exceptions
from crossminds_config import crossminds_config
import time
from multiprocessing.dummy import Pool


class crossminds_scrapy:
    def get_content(self, url):
        try:
            response = requests.get(
                url, headers={'User-Agent': crossminds_config.user_agent})
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
        except exceptions.Timeout:
            print('请求超时')
        except exceptions.HTTPError:
            print('http请求错误')
        else:
            return response.content

    def post_content(self, url, data):
        try:
            response = requests.post(
                url=url,
                data=data,
                headers={'Content-Type': 'application/json'})
            response.raise_for_status()  # 如果返回的状态码不是200， 则抛出异常;
        except exceptions.Timeout:
            print('请求超时')
        except exceptions.HTTPError:
            print('http请求错误')
        else:
            return response.content

    # def get_categaries(self):
    #     url = "https://api.crossminds.io/content/category/parents/details"
    #     content = self.get_content(url).decode()
    #     json_results = json.loads(content)["results"]
    #     subcategory = json_results[0]["subcategory"]
    #     categaries = []
    #     for categary in subcategory:
    #         categaries.append(categary["name"])
    #     print(categaries)
    #     return categaries

    # def preget_items(self, category):
    #     url = "https://api.crossminds.io/web/content/bycategory"
    #     data = {
    #         'search': {
    #             'category': category
    #         },
    #         'limit': crossminds_config.request_num,
    #         'offset': 0
    #     }
    #     result = self.post_content(url, json.dumps(data)).decode()
    #     return result

    def get_categories2(self):
        url = "https://api.crossminds.io/web/node/interest-list?offset=0&limit=10"
        content = self.get_content(url).decode()
        json_results = json.loads(content)["results"]
        categaries = []
        for result in json_results:
            categaries.append(result["label"])
        print(categaries)
        return categaries

    def preget_items2(self, category):
        url = "https://api.crossminds.io/web/node/video/name/{}?limit=1500&offset=0".format(category)
        result = self.get_content(url).decode()
        return result

    def get_items2(self):
        items = []
        categories = self.get_categories2()

        start = time.time()
        pool = Pool()
        items = list(pool.map(self.preget_items2, categories))
        end = time.time()
        pool.close()
        pool.join()
        print('info_scrapy_finished--timestamp:{:.3f}'.format(end - start))

        # for category in tqdm(categories):
        #     url = "https://api.crossminds.io/web/node/video/name/{}?limit=1500&offset=0".format(
        #         category)
        #     result = self.get_content(url).decode()
        #     items.append(result)
        return items

    # def get_items(self):
    #     # url = "https://api.crossminds.io/web/content/bycategory"
    #     categories = self.get_categaries()
    #     start = time.time()
    #     pool = Pool()
    #     items = list(pool.map(self.preget_items, categories))
    #     end = time.time()
    #     pool.close()
    #     pool.join()
    #     print('info_scrapy_finished--timestamp:{:.3f}'.format(end - start))

    #     # items = []
    #     # for category in tqdm(categories):
    #     #     # if category not in ['CVPR 2020', 'CoRL 2020', 'EMNLP 2020']:
    #     #     data = {
    #     #         'search': {
    #     #             'category': category
    #     #         },
    #     #         'limit': crossminds_config.request_num,
    #     #         'offset': 0
    #     #     }
    #     #     result = self.post_content(url, json.dumps(data)).decode()
    #     #     items.append(result)
    #     # # print(items)
    #     return items


if __name__ == '__main__':
    cm_scrapy = crossminds_scrapy()
    cm_scrapy.get_categories2()
    cm_scrapy.get_items2()
