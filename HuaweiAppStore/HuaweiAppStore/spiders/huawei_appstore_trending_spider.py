#!/usr/bin/python
# -*- coding: utf-8 -*-

import scrapy
import json
import sys
from scrapy.selector import Selector
from HuaweiAppStore.items import HuaweiAppStoreItem

class HuaweiAppStoreTrendingSpider(scrapy.Spider):
    """
    Scrape information of trending app in Huawei Application Store
    Information includes: title, appid, icon url, description
    
    Since link to next page is dynamically loaded by javascript, which is 
    nontrivial to get, we traverse all number in trending link from 1 to ...
    Also, Huawei AppStore would give response even when requesting a page
    whose number is after last page. Eg. currently last page is 41, when we
    request for page 42, it won't return 404. Rather, it would return page
    with empty list. So we check whether list is empty or not to determine
    termination of scraping.
    """

    name = "huawei_appstore_trending"
    allowed_domains = ["huawei.com"]
    start_urls = ["http://appstore.huawei.com/more/all/40"]
    pipelines = ["HuaweiappstoreDuplicatePipeline",\
            "HuaweiappstoreTrendingPipeline"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse, meta={\
                    'splash': {\
                    'endpoint': 'render.html',\
                    'args': {'wait': 0.5}\
                }\
            })

    def parse(self, response):
        #First, scrape all apps' info in this page
        for app in Selector(response)\
                .xpath("//div[contains(@class, 'list-game-app')]"):
            game_info = app.xpath("div[@class='game-info  whole']")

            item = HuaweiAppStoreItem()
            item['image'] = app.xpath("./div[@class='game-info-ico']/a\
                    /img/@src").extract()[0]
            item['title'] = game_info.xpath("./h4[@class='title']/a\
                    /text()").extract()[0].encode("utf-8")
            item['appid'] = game_info.xpath("./h4[@class='title']/a/@href")\
                    .re('http://appstore.huawei.com:80/app/(C\d+)')[0]
            item['desc'] = u''.join(game_info.xpath("./div[@class='game-info-dtail part']\
                    /p[@class='content']/text()").extract()).encode("utf-8")
            yield item
            
        #Then, try to find next page, if exist
        next_page = Selector(response).xpath("//div[@class='page-ctrl ctrl-app']/a").extract()
        #If could not find this div, splash must be wrong
        if len(next_page) == 0:
            print "Javascript could not fetch! Please make sure splash is running and setting is corrent!"
            sys.exit(1)
        if len(next_page) >= 2 and next_page[-2].find("下一页".decode("utf-8")) != -1:
            next_url = Selector(response)\
                    .xpath("//div[@class='page-ctrl ctrl-app']/a[last()-1]/@href")\
                    .extract_first()
            yield scrapy.Request(next_url, self.parse, meta={\
                'splash': {\
                    'endpoint': 'render.html',\
                    'args': {'wait': 0.5}\
                }\
            })
