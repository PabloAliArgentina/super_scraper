import scrapy
from time import time

class Toledo_Spider(scrapy.Spider):
    name = "toledospider"
    base_url = 'https://toledodigital.com.ar'

    def start_requests(self):
        subs = ["/2-Almacén.html",
                "/2-Frescos.html",
                "/2-Bebidas.html",
                "/2-Verdulería.html",
                "/2-Carnes.html",
                "/2-Fiambrería",
                "/2-Congelados",
                "/2-Perfumería",
                "/2-Limpieza",
                "/2-Mascotas",
                "/2-Hogar"]

        for sub in subs:
            url = self.base_url + sub
            yield scrapy.Request(url=url,
                                 callback=self.parse)


    def parse(self, response):
        products = (response.css('ol.product-items')
                            .css('li.product-item')
                    )
        
        if len(products) == 0: return

        for product in products:
            product_link = (product.css('div.product-item-details')
                                   .css('a.product-item-link')
                                   .attrib['href']
                            )
            
            yield scrapy.Request(url=product_link,
                                 callback=self.parse_product,
                                )            
        #Recursively returns next pages results to scrawler
        next_page = (response.css('li.pages-item-next')
                            .css('a.next::attr(href)')
                            .get()
                    )
        if next_page is not None:
            yield scrapy.Request(url=next_page,
                                callback=self.parse)



    def parse_product(self, response):
        response
        result = {}
        result['name'] = (response.css('div.page-title-wrapper')
                                .css('h1.page-title')
                                .css('span::text')
                                .get()
                         )
        result['id'] = (response.xpath('//div[@itemprop="sku"]/text()')
                                .get()
                        )
        result['ean'] = (response.xpath('//td[@data-th="ean"]/text()')
                                  .get()
                        )
        result['brand'] = (response.xpath('//td[@data-th="Marca"]/text()')
                                    .get()
                          )
        result['price'] = (response.xpath('//meta[@itemprop="price"]/@content')
                                    .get()
                          )
        result['price'] = float(result['price']) if result['price'] is not None else None        
        result['date'] = round(time())      
        result['measurement_unit'] = (response.xpath('//td[@data-th="Unidad de medida"]/text()')
                                              .get()
                                     )
        result['unit_multiplier'] = (response.xpath('//td[@data-th="contenido"]/text()')
                                    .get()
                          )
           
        result['url'] = response.url
        result['img_url'] = (response.css('img.gallery-placeholder__image::attr(src)')
                                     .get()
                            )

        yield result