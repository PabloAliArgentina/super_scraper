import scrapy

class CotoSpider(scrapy.Spider):
    name = "CotoSpider"
    base_url = "https://www.cotodigital3.com.ar"

    def start_requests(self):

        urls = ["https://www.cotodigital3.com.ar/sitios/cdigi/browse"] #contains all categories together
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        def clean_text(text: str) -> str:
            text_ = text.replace('\n', '').replace('\t', '').strip()
            text_ = " ".join(text_.split())
            return text_

        products = response.css('ul#products.grid').css('div.leftList')
        for product in products:
            result = {'name': None,
                      'sku': None,
                      'price': None,
                      'unit': None,
                      'url': None,
                      'img_url': None}
            try:
                result['name'] = clean_text(product.css('div.descrip_full::text').get())
                result['sku'] = product.css('div.descrip_full').attrib['id'].replace('descrip_full_sku','')
                result['price'] = clean_text(product.css('span.atg_store_productPrice')
                                           .css('span.atg_store_newPrice::text')
                                           .get()
                                           ),
                result['unit'] = clean_text(product.css('span.unit::text').get())
                result['url'] = self.base_url + product.css('div.product_info_container').css('a::attr(href)').get()
                result['img_url'] = product.css('span.atg_store_productImage').css('img::attr(src)').get()
            except:
                pass

            yield result

        #Recursively returns next pages results to scrawler
        pagination_items = response.css('ul#atg_store_pagination').css('li')
        next_page = None
        for index, item in enumerate(pagination_items):
            # print ('\n' * 10 + item.get())
            if 'class' in item.attrib and 'active' in item.attrib['class']:
                next_page = self.base_url + pagination_items[index + 1].css('a::attr(href)').get()

        if next_page is not None:
            yield scrapy.Request(next_page, callback=self.parse)
