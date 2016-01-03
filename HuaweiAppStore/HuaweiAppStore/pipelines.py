# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json

class HuaweiappstorePipeline(object):
    def __init__(self):
        self.f = open("HuaweiAppStoreTrending.txt", "wb")

    def process_item(self, item, spider):
        self.f.write(json.dumps(dict(item)) + "\n")
        return item
