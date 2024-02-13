import scrapy


class Anonimaspider(scrapy.Spider):
    name = "anonimaspider"
    base_url = 'https://supermercado.laanonimaonline.com'

    def start_requests(self):
        urls = ["https://supermercado.laanonimaonline.com/almacen/n1_1/",
                "https://supermercado.laanonimaonline.com/bebidas/n1_2/",
                "https://supermercado.laanonimaonline.com/frescos/n1_6/",
                "https://supermercado.laanonimaonline.com/congelados/n1_296/",
                "https://supermercado.laanonimaonline.com/frutas-y-verduras/n1_7/",
                "https://supermercado.laanonimaonline.com/carniceria/n1_8/",
                "https://supermercado.laanonimaonline.com/perfumeria/n1_359/",
                "https://supermercado.laanonimaonline.com/limpieza/n1_4/",
                "https://supermercado.laanonimaonline.com/mundo-bebe/n1_5/",
                "https://supermercado.laanonimaonline.com/mascotas/n1_10/",
                "https://supermercado.laanonimaonline.com/hogar/n1_9/"]
        for url in urls:
            params = {'page_number': 0, 'base_url': url}
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 cb_kwargs=params)

    def parse(self, response, page_number, base_url):
        products = response.css('div.producto')
        if len(products) == 0: return

        for product in products:
            result = {'name': None,
                      'sku': None,
                      'brand': None,
                      'price': None,
                      'discount_price': None,
                      'previous_price': None,
                      'url': None,
                      'img_url': None
                      }

            for _input in product.css('input'):
                if 'name' in _input.attrib and 'value' in _input.attrib:
                    field = _input.attrib['name']
                    value = _input.attrib['value']
                    if 'sku_item_imetrics' in field:
                        result['sku'] = value
                    elif 'name_item_imetrics' in field:
                        result['name'] = value
                    elif 'precio_item_imetrics' in field:
                        result['price'] = value
                    elif 'precio_oferta_item_imetrics' in field:
                        result['discount_price'] = value
                    elif 'precio_anterior_item_imetrics' in field:
                        result['previous_price'] = value
                    elif 'brand_item_imetrics' in field:
                        result['brand'] = value

            for a in product.css('a'):
                if 'id' in a.attrib:
                    if 'btn_nombre_imetrics' in a.attrib['id']:
                        result['url'] = self.base_url + a.attrib['href']

            for div in product.css('div'):
                if 'id' in div.attrib:
                    if 'btn_img_imetrics' in div.attrib['id']:
                        src = div.css('img')
                        if len(src) > 0:
                            if 'data-src' in src[0].attrib:
                                result['img_url'] = src[0].attrib['data-src']

            yield result

        # #Recursively returns next pages results to scrawler
        next_page = f'{base_url}pag/{page_number + 1}/'
        try:
            yield scrapy.Request(next_page,
                                 callback=self.parse,
                                 cb_kwargs={'base_url': base_url,
                                            'page_number': page_number + 1}
                                )
        except Exception as e:
            raise e
