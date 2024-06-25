import scrapy
import re
from time import time

class Atomospider(scrapy.Spider):
    name = "atomospider"

    def __init__(self, *args, **kwargs):
        super(Atomospider, self).__init__(*args, **kwargs)
        self.market_name = 'atomo'

    def start_requests(self):
        urls = ["https://atomoconviene.com/atomo-ecommerce/3-almacen",
                "https://atomoconviene.com/atomo-ecommerce/81-bebidas",
                "https://atomoconviene.com/atomo-ecommerce/226-lacteos-fiambres",
                "https://atomoconviene.com/atomo-ecommerce/883-suplementos-y-dietetica",
                "https://atomoconviene.com/atomo-ecommerce/300-carnes-y-congelados",
                "https://atomoconviene.com/aimport retomo-ecommerce/473-sin-tacc",
                "https://atomoconviene.com/atomo-ecommerce/83-perfumeria",
                "https://atomoconviene.com/atomo-ecommerce/85-limpieza",
                "https://atomoconviene.com/atomo-ecommerce/82-mundo-bebe",
                "https://atomoconviene.com/atomo-ecommerce/88-mascotas",
                "https://atomoconviene.com/atomo-ecommerce/306-libreria-jugueteria"
                ]

        for url in urls:
            params = {'page_number': 1, 'base_url': url}
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=params)

    def parse(self, response, page_number, base_url):

        def parse_price(price:str) -> float:
            return float(price.replace('$', '')
                                .replace('.', '')
                                .replace(',', '.')
                            )
        
        products = response.css('article')
        if len(products) == 0: return

        for product in products:
            result = {'ean': None,
                      'name': None,
                      'id': None,
                      'price': None,
                      'date': (round(time())),
                      'stock': None,
                      'url': None,
                      'img_url': None}
            try:
                result['name'] = (product.css('h2.h3.product-title')
                                          .css('a *::text')
                                          .get()
                                )
                result['price'] = parse_price(
                                    product
                                        .css('div.product-price-and-shipping')
                                        .css('span.price::text')
                                        .get()
                                        .replace(u'\xa0', '')
                                  )
                result['stock'] = int(product.css('span#product-availability')
                                      .css('b')
                                      .css('span')[0]
                                      .attrib['data-stock']
                                      )
                result['id'] = product.attrib['data-id-product']
                result['url'] = (product.css('h2.h3.product-title')
                                        .css('a')
                                        [0]
                                        .attrib['href']
                                )
                result['img_url'] = (product
                                      .css('div.card-img-top.product__card-img')
                                      .css('a.thumbnail.product-thumbnail')
                                      .css('img')[0]
                                      .attrib['data-full-size-image-url']
                                    )
                result['ean'] = re.search(r"--(\d+)\.html",
                                          result['url']
                                         ).group(1)
            except Exception:
                pass

            yield result

        #Recursively returns next pages results to scrawler
        next_page = f'{base_url}?page={page_number + 1}'
        try:
            yield scrapy.Request(next_page,
                                 callback=self.parse,
                                 cb_kwargs={'base_url': base_url,
                                            'page_number': page_number + 1})
        except Exception as e:
            raise e