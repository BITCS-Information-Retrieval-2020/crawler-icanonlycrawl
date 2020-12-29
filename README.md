# 爬虫模块
## 模块要求
- CrossMinds必选，要保证爬到的论文中有一定比例包含oral视频，爬取到的必须是视频的文件，记录下url地址。
- 除CrossMinds外再至少选择一个站点爬取，爬取的站点越多，包含的字段越多，爬到的数据越多，最终得分越高。
- 爬到的数据必须存储到MongoDB( [https://www.mongodb.com](https://www.mongodb.com) )中，供后续模块访问使用。字段必须定义清晰。
- 论文标题，作者等文本字段直接存在数据库里，视频，PDF等二进制文件存在磁盘上，数据库里保存文件的路径。
- 爬虫可以是简单地一次性把数据爬完，也可以是增量式爬取，时时更新，可以是单线程，也可以是多线程，或使用线程池。总之，爬虫的性能越强，越健壮，得分越多。
- 最后需要提供爬到数据的统计信息。
- 推荐使用Python Scrapy爬虫库：( [https://scrapy.org](https://scrapy.org) )
- 用Python的Flake8( [https://flake8.pycqa.org/en/latest/](https://flake8.pycqa.org/en/latest/) )库检查代码是否规范
- 模块接口要求：爬虫模块最终需要交给检索模块一个MongoDB数据库和磁盘文件。
## 小组成员及分工
1. 基础爬虫  
詹亘泽：ACL Anthology网站爬取；  
徐伊玲、谭小焱：CrossMinds网站爬取。  
2. 性能优化  
张峄天、张悉伦、何亮丽  
## 与检索模块的对接字段
<https://github.com/BITCS-Information-Retrieval-2020/search-rattailcollagen1/blob/master/searcher/data/dataFlow/fromCrawler.json>

