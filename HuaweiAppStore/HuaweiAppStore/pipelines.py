# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
from scrapy.exceptions import DropItem

class HuaweiappstoreDuplicatePipeline(object):
    """
    Remove duplicate apps based on app id.
    """
    def __init__(self):
        self.appids = set()

    def process_item(self, item, spider):
        if type(self).__name__ not in getattr(spider, "pipelines", []):
            return item

        if item["appid"] in self.appids:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.appids.add(item["appid"])
            return item

class HuaweiappstoreTrendingPipeline(object):
    """
    Save trending apps in trending file.
    """
    def __init__(self):
        self.f = open("HuaweiAppStoreTrending.txt", "a")

    def process_item(self, item, spider):
        if type(self).__name__ in getattr(spider, "pipelines", []):
            self.f.write(json.dumps(dict(item)) + "\n")
        #if type(self).__name__ in getattr(spider, "pipelines", []):
        #    self.f.write("title: %s\nappid: %s\n" % (dict(item)["title"], dict(item)["appid"]))
        return item

class HuaweiappstoreTopicPipeline(object):
    """
    Save apps in different topics in different files.
    """
    def process_item(self, item, spider):
        if type(self).__name__ in getattr(spider, "pipelines", []):
            f = open("topic_output/HuaweiAppStoreTopic-%s" % item["topic"], "a")
            f.write(json.dumps(dict(item)) + "\n")
            #f.write("title: %s\nappid: %s\n" % (dict(item)["title"], dict(item)["appid"]))
            f.close()
        return item
