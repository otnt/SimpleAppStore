# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class HuaweiAppStoreItem(scrapy.Item):
    title = scrapy.Field()
    appid = scrapy.Field()
    image = scrapy.Field()
    desc = scrapy.Field()

class HuaweiAppStoreTopicAppItem(scrapy.Item):
    topic = scrapy.Field()
    title = scrapy.Field()
    appid = scrapy.Field()
    image = scrapy.Field()
    desc = scrapy.Field()
