import json
from base64 import b64encode
from time import time
import scrapy
import requests
import re

class ChangoSpider(scrapy.Spider):
    name = "changospider"
    base_url = 'https://www.masonline.com.ar'
    page_size = 100

    def __init__(self, *args, **kwargs):
        super(ChangoSpider, self).__init__(*args, **kwargs)
        self.market_name = 'changomas'

    #Returns the hash needed to make queries
    def get_query_hash(self, url:str):
        response = requests.get(url=url)
        body = scrapy.Selector(text=response.text)
        data = body.xpath('//template[@data-varname="__STATE__"]/script/text()').get()
        data = json.loads(data)
        data = data.get('ROOT_QUERY')
        _hash=None
        #hash is included in a large and complicated key
        #it must be found and filtered
        for key in data.keys():
            if 'productSearch(' in key:
                pattern = r'"hash"\:"\b[a-fA-F0-9]{32,}\b"'
                hash_entries = re.findall(pattern, key)
                if len(hash_entries) > 0:
                    _hash = hash_entries[0].replace('"hash":', '').replace('"', '')
                    break

        return _hash

    #Returns a request to specific category and range of indexes
    def generate_request(self, category: str, _from: int, _to: int, _hash:str):
        variables = f'{{"hideUnavailableItems":true,"skusFilter":"ALL","simulationBehavior":"default","installmentCriteria":"MAX_WITH_INTEREST","productOriginVtex":false,"map":"productclusternames","query":"{category}","orderBy":"OrderByScoreDESC","from":{_from},"to":{_to},"selectedFacets":[{{"key":"productclusternames","value":"{category}"}}],"facetsBehavior":"Static","categoryTreeBehavior":"default","withFacets":false,"showSponsored":true}}'
        variables = b64encode(variables.encode('utf-8')).decode('utf-8')
        return f'{self.base_url}/_v/segment/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-AR&__bindingId=d62c820d-5adb-43a2-9d15-25ff4f3a6d2f&operationName=productSearchV3&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22{_hash}%22%2C%22sender%22%3A%22vtex.store-resources%400.x%22%2C%22provider%22%3A%22vtex.search-graphql%400.x%22%7D%2C%22variables%22%3A%22{variables}%3D%22%7D'

    def start_requests(self):

        categories = ["mas-online---almacen",
                      "bebidas",
                      "carniceria-pescaderia-y-verduleria",
                      "frescos-y-congelados",
                      "perfumeria",
                      "belleza",
                      "limpieza",
                      "bebes-y-ninos"   
                      ]

        self.query_hash = self.get_query_hash(f'{self.base_url}/{categories[0]}')
        if self.query_hash is None:
            raise Exception('Query hash not found')
        
        for category in categories:
            print(f"scraping category:{category}")
            url = self.generate_request(category=category,
                                        _from=0,
                                        _to=self.page_size - 1,
                                        _hash=self.query_hash)
            print('Request=', url)            
            params = {'category': category, 'product_index': 0}
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=params)

    def parse(self, response, category, product_index):

        #Los forros de changomas encodean el ean, le sacan el ultimo dígito y le agregan un 0 adelante
        def fix_ean(bad_ean:str) -> str:
            bad_ean = bad_ean[1:]
            digits = [int(i) for i in reversed(bad_ean)]
            checksum_digit = str((10 - (3 * sum(digits[0::2]) + (sum(digits[1::2])))) % 10)
            return bad_ean + checksum_digit


        # Get json containing products and the number of products
        jsn = json.loads(response.text)
        last_product_index = jsn['data']['productSearch']['recordsFiltered'] - 1
        products = jsn['data']['productSearch']['products']

        # Parse dictionary and return results
        for product in products:
            result = {}
            result['name'] = product.get('productName')
            result['id'] = product.get('productId')
            result['ean'] = (product.get('items', [{}])[0]
                                    .get('ean')
                             )
            if isinstance(result['ean'], str): result['ean'] = fix_ean(result['ean'])     
            result['brand'] = product.get('brand')
            result['price'] = (product.get('items', [{}])[0]
                               .get('sellers', [{}])[0]
                               .get('commertialOffer', {})
                               .get('Price')
                               )
            result['date'] = round(time())
            # result['measurement_unit'] = json.loads(product.get('properties', [{}])[0]
            #                                                .get('values', ['{}'])[0]
            #                                         ).get('measurement_unit_un')
            # result['unit_multiplier'] = json.loads(product.get('properties', [{}])[0]
            #                                                .get('values', ['{}'])[0]
            #                                         ).get('unit_multiplier_un')
            result['stock'] = (product.get('items', [{}])[0]
                               .get('sellers', [{}])[0]
                               .get('commertialOffer', {})
                               .get('AvailableQuantity')
                               )
            result['url'] = self.base_url + product['link'] if 'link' in product else ""
            result['img_url'] = (product.get('items', [{}])[0]
                                 .get('images', [{}])[0]
                                 .get('imageUrl')
                                 )

            yield (result)

        # Recursively returns next pages results to scrawler if any
        product_index += self.page_size
        if product_index > last_product_index:
            return
        next_page = self.generate_request(category=category,
                                          _from=product_index,
                                          _to=product_index + self.page_size - 1,
                                          _hash=self.query_hash)
        try:
            yield scrapy.Request(next_page,
                                 callback=self.parse,
                                 cb_kwargs={'category': category,
                                            'product_index': product_index})
        except Exception as e:
            raise e