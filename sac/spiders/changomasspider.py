import json
import re
from time import time
import scrapy


class ChangomasSpider(scrapy.Spider):
    name = "changomasspider"
    base_url = 'https://www.masonline.com.ar/'

    def __init__(self, *args, **kwargs):
        super(ChangomasSpider, self).__init__(*args, **kwargs)
        self.market_name = 'changomas'

    def start_requests(self):
        base_url = self.base_url
        query='?map=productClusterIds'
        urls = [f"{base_url}268",   #almacen
                f"{base_url}3431",  #carnicería, pescadería, verdulería
                f"{base_url}3432",  #Frescos y congelados
                f"{base_url}3433",  #Bebidas
                f"{base_url}3455",  #Perfumería
                f"{base_url}3434",  #Belleza
                f"{base_url}272",   #Limpieza
                f"{base_url}273",   #Bebés y niños
                ]

        for url in urls:
            params = {'page_number': 1, 'base_url': url, 'query': query}
            yield scrapy.Request(url=url+query, callback=self.parse, cb_kwargs=params)

    def parse(self, response, page_number, base_url, query):

        # Finds the line containing the data to render products
        content_lines = response.text.splitlines()
        data = ''
        for index, line in enumerate(content_lines):
            if 'data-varname="__STATE__"' in line.replace(' ', ''):
                data = content_lines[index + 1]
                break
        data = data.replace('<script>', '').replace('</script>', '')
        data_json = json.loads(data)

        # firts step is to get product's ids
        products_ids = []
        pattern = r'^Product:sp-(\d+)[^.]*$'
        for key, item in data_json.items():
            if bool(re.match(pattern, key)):
                if 'cacheId' in item:
                    products_ids.append(item['cacheId'])

        if (len(products_ids) == 0): return  # It means there's no more products

        # Now some fields can be reached straighforward
        # price = name = url = unit = ean = image_url = None
        for id in products_ids:

            price = (data_json.get(f'$Product:{id}.priceRange.sellingPrice', {})
                     .get('lowPrice')
                     )
            name = (data_json.get(f'Product:{id}', {})
                    .get('productName')
                    )
            url = (data_json.get(f'Product:{id}', {})
                   .get('linkText')
                   )
            brand = (data_json.get(f'Product:{id}', {})
                   .get('brand')
                   )
            pr_id = (data_json.get(f'Product:{id}', {})
                   .get('productId')
                   )
            

            # # Find deeper fields in properties :
            # for key, item in data_json.items():
            #     pattern = fr'^Product:{id}.properties.(\d+)$'
            #     if bool(re.match(pattern, key)):
            #         if 'name' in item:
            #             if item['name'].lower() == 'PrecioPorUnd':
            #                 unit = (item['values']['json'][0])


            # Find image url and ean requires a tricky and even deeper search into specific .items field:
            for key, item in data_json.items():
                pattern = fr'^Product:{id}.items'
                if bool(re.match(pattern, key)):
                    if 'images' in item:
                        if type(item['images']) == list:
                            if 'id' in item['images'][0]:
                                image_id = item['images'][0]['id'].replace('image:', '')
                                if image_id in data_json:
                                    image_url = data_json[image_id]['imageUrl']
                    if 'ean' in item:
                        ean = item['ean']

            yield {'name': name,
                   'ean': ean,
                   'id': pr_id,
                   'brand': brand,
                   'price': price,
                   'date': (round(time())),
                #    'unit': unit,
                   'url': self.base_url + url + '/p',
                   'image_url': image_url
                   }


        # #Recursively returns next pages results to scrawler
        next_page = f'{base_url}{query}&page={page_number + 1}'
        try:
            yield scrapy.Request(next_page, callback=self.parse,
                                 cb_kwargs={'base_url': base_url,
                                            'page_number': page_number + 1,
                                            'query': query}
                                )
        except Exception as e:
            raise e
