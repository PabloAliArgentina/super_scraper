# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import pymongo


class SacPipeline:
    def process_item(self, item, spider):
        return item

class MockPipeline:

    @classmethod
    def from_crawler(cls, crawler):
        print ('DEBUG_from_crawler.somevalue', crawler.settings.get('SOME_VALUE'))

class ValidatePipeline:
    def __init__(self) -> None:
        self.mandatory_fields = ['ean', 'name', 'price']

    def process_item(self, item, spider):
        for field in self.mandatory_fields:
            value = item.get(field)
            if (    (value is None) 
                or  (value == '')
                or  (value == 0)
            ):
                raise DropItem(f'Missing or wrong value ({value}) in field: {field}')
                
        return item

class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        uri = crawler.settings.get('MONGO_MARKET_URI')
        db = crawler.settings.get('MONGO_MARKET_DATABASE')
        return cls( mongo_uri=uri,
                    mongo_db=db,
                )
            
    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.coll = self.db[spider.market_name]
        self.coll.drop()

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.coll.insert_one(ItemAdapter(item).asdict()) 
        return item

class MongoMergerPipeline:

    def __init__(self, mongo_uri, mongo_db, mongo_coll):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_coll = mongo_coll

    @classmethod
    def from_crawler(cls, crawler):
        uri = crawler.settings.get('MONGO_MERGER_URI')
        db = crawler.settings.get('MONGO_MERGER_DATABASE')
        coll = crawler.settings.get('MONGO_MERGER_COLLECTION')
        return cls( mongo_uri=uri,
                    mongo_db=db,
                    mongo_coll=coll
                )
            
    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.coll = self.db[self.mongo_coll]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):

        ean = item.get('ean')
        if ean is None: return

        market = spider.market_name
        price = item.get('price')
        name = item.get('name')
        brand = item.get('brand')
        img_url = item.get('img_url')
        date = item.get('date')
        document = self.coll.find_one_and_update({'ean': ean},
                                                 {'$set':
                                                    {'ean': ean,
                                                     'name': name,
                                                    f'markets.{market}': {'price': price,
                                                                        'date': date
                                                                        },
                                                    }
                                                    },
                                                    upsert=True,
                                                    return_document=pymongo.ReturnDocument.AFTER
                    )        
        if (document.get('brand') in (None, '')):
            self.coll.update_one({'_id': document['_id']},
                                 {'$set':{
                                        'brand': brand 
                                    }
                                 }
            )
        if (document.get('img_url') in (None, '')):
            self.coll.update_one({'_id': document['_id']},
                                 {'$set':{
                                        'img_url': img_url 
                                    }
                                 })
        return item