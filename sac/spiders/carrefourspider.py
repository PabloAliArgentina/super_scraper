import json
import re
from time import time
import scrapy


class Carrefourspider(scrapy.Spider):
    name = "carrefourspider"
    base_url = 'http://www.carrefour.com.ar'

    def __init__(self, *args, **kwargs):
        super(Carrefourspider, self).__init__(*args, **kwargs)
        self.market_name = 'carrefour'

    def start_requests(self):
        urls = ["https://www.carrefour.com.ar/Almacen",
                "https://www.carrefour.com.ar/Desayuno-y-merienda",
                "https://www.carrefour.com.ar/Bebidas",
                "https://www.carrefour.com.ar/Lacteos-y-productos-frescos",
                "https://www.carrefour.com.ar/Carnes-y-Pescados",
                "https://www.carrefour.com.ar/Frutas-y-Verduras",
                "https://www.carrefour.com.ar/Panaderia",
                "https://www.carrefour.com.ar/Congelados",
                "https://www.carrefour.com.ar/Limpieza",
                "https://www.carrefour.com.ar/Perfumeria",
                "https://www.carrefour.com.ar/Mundo-Bebe",
                "https://www.carrefour.com.ar/Mascotas"]

        for url in urls:
            params = {'page_number': 0, 'base_url': url}
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=params)

    def parse(self, response, page_number, base_url):

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
        pattern = r'^Product:sp-(\d+)-none$'
        for key, item in data_json.items():
            if bool(re.match(pattern, key)):
                if 'productId' in item:
                    products_ids.append(item['productId'])

        if len(products_ids) == 0: return  # It means there's no more products

        # Now some fields can be reached straighforward
        price = name = url = unit = ean = image_url = None
        for id in products_ids:
            price = (data_json.get(f'$Product:sp-{id}-none.priceRange.sellingPrice', {})
                     .get('lowPrice')
                     )
            name = (data_json.get(f'Product:sp-{id}-none', {})
                    .get('productName')
                    )
            url = (data_json.get(f'Product:sp-{id}-none', {})
                   .get('link')
                   )
            brand = (data_json.get(f'Product:sp-{id}-none', {})
                   .get('brand')
                   )
            pr_id = (data_json.get(f'Product:sp-{id}-none', {})
                   .get('productId')
                   )
            

            # Find deeper fields in properties :
            for key, item in data_json.items():
                pattern = fr'^Product:sp-{id}-none.properties.(\d+)$'
                if bool(re.match(pattern, key)):
                    if 'name' in item:
                        if item['name'].lower() == 'precio x unidad':
                            unit = (item['values']['json'][0])
                        elif item['name'].lower() == 'ean':
                            ean = (item['values']['json'][0])

            # Find image url requires a tricky and even deeper search into specific .items field:
            for key, item in data_json.items():
                pattern = fr'^Product:sp-{id}-none.items'
                if bool(re.match(pattern, key)):
                    if 'images' in item:
                        if type(item['images']) == list:
                            if 'id' in item['images'][0]:
                                image_id = item['images'][0]['id'].replace('image:', '')
                                if image_id in data_json:
                                    image_url = data_json[image_id]['imageUrl']

            yield {'name': name,
                   'ean': ean,
                   'id': pr_id,
                   'brand': brand,
                   'price': price,
                   'date': (round(time())),
                   'unit': unit,
                   'url': self.base_url + url,
                   'image_url': image_url
                   }

        # #Recursively returns next pages results to scrawler
        next_page = f'{base_url}?page={page_number + 1}'
        try:
            yield scrapy.Request(next_page, callback=self.parse,
                                 cb_kwargs={'base_url': base_url, 'page_number': page_number + 1})
        except Exception as e:
            raise e
