import scrapy
import json
from scrapy.selector import Selector
from HuaweiAppStore.items import HuaweiAppStoreItem
from HuaweiAppStore.items import HuaweiAppStoreTopicAppItem

class HuaweiAppStoreTopicSpider(scrapy.Spider):
    """
    Scrape all apps in different topics into different topic files.
    Each file name is unique by topic name.
    """

    name = "huawei_appstore_topic"
    allowed_domains = ["huawei.com"]
    start_urls = ["http://appstore.huawei.com/topics/30"]
    titles = set()
    pipelines = ["HuaweiappstoreDuplicatePipeline", \
            "HuaweiappstoreTopicPipeline"]

    def parse(self, response):
        has_content = False
        #First, crawl all topic in current page
        for topic in Selector(response)\
                .xpath("//img[contains(@class, 'topic')]"):
            title = topic.xpath("@title").extract()[0]
            if title in self.titles:
                continue
            self.titles.add(title)

            has_content = True
            yield scrapy.Request(topic.xpath("../@href").extract()[0] + "/1",\
                    self.parse_helper)

        #Then, try find next page
        if has_content:
            yield scrapy.Request(self.get_next_page(response.url), self.parse)
        
            
    def parse_helper(self, response):
        has_content = False
        topic = Selector(response)\
                .xpath("//div[@class='topic-item-info content']/h4/text()")\
                .extract_first()

        #First, crawl all application in this page
        for app in Selector(response).xpath("//div[@class='nofloat']"):
            has_content = True

            item = HuaweiAppStoreTopicAppItem()
            item["topic"] = topic.encode("utf-8")
            item["title"] = app.xpath(".//img[@class='app']/@title")\
                    .extract_first().encode("utf-8")
            item["appid"] = app.xpath(".//a[1]/@href")\
                    .re('http://appstore.huawei.com:80/app/(C\d+)')[0]
            item["image"] = app.xpath(".//img[@class='app']/@lazyload")\
                    .extract_first().encode("utf-8")
            item["desc"] = u''.join(app.xpath(".//p[@class='ft-light']/text()")\
                    .extract()).encode("utf-8")
            yield item

        #Then, try find next page
        if has_content:
            yield scrapy.Request(\
                    self.get_next_page(response.url), self.parse_helper)

    def get_next_page(self, curr_url):
        """
        Get url of next page.
        URL is of this form: http://xxx.xxx/1, http://xxx.xxx/2 ...
        We simply add page index by 1
        """
        split_position = curr_url.rfind("/")
        next_url = curr_url[:split_position + 1] +\
            str(int(curr_url[split_position + 1:]) + 1)
        return next_url

