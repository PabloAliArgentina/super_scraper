import json
from base64 import b64encode
import scrapy


class jumbospider(scrapy.Spider):
    name = "jumbospider"
    base_url = 'https://www.jumbo.com.ar'
    page_size = 100

    #Returns a request to specific category and range of indexes
    def generate_request(self, category: str, _from: int, _to: int):
        variables = f'{{"hideUnavailableItems":true,"skusFilter":"FIRST_AVAILABLE","simulationBehavior":"default","installmentCriteria":"MAX_WITHOUT_INTEREST","productOriginVtex":false,"map":"c","query":"{category}","orderBy":"OrderByScoreDESC","from":{_from},"to":{_to},"selectedFacets":[{{"key":"c","value":"{category}"}}],"operator":"and","fuzzy":"0","searchState":null,"facetsBehavior":"Static","categoryTreeBehavior":"default","withFacets":false}}'
        variables = b64encode(variables.encode('utf-8')).decode('utf-8')
        return f'{self.base_url}/_v/segment/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-AR&__bindingId=4780db52-b885-45f0-bbcc-8bf212bb8427&operationName=productSearchV3&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2240b843ca1f7934d20d05d334916220a0c2cae3833d9f17bcb79cdd2185adceac%22%2C%22sender%22%3A%22vtex.store-resources%400.x%22%2C%22provider%22%3A%22vtex.search-graphql%400.x%22%7D%2C%22variables%22%3A%22{variables}%3D%3D%22%7D'

    def start_requests(self):

        categories = ["almacen",
                      "bebidas",
                      "bebes_y_ninos",
                      "frutas-y-verduras",
                      "carnes",
                      "pescados-y-mariscos",
                      "quesos-y-fiambres,"
                      "lacteos",
                      "congelados",
                      "perfumeria",
                      "limpieza",
                      "mascotas"]

        for category in categories:
            print(f"scraping category:{category}")
            url = self.generate_request(category=category, _from=0, _to=self.page_size - 1)
            params = {'category': category, 'product_index': 0}
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs=params)

    def parse(self, response, category, product_index):

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
            result['brand'] = product.get('brand')
            result['price'] = (product.get('items', [{}])[0]
                               .get('sellers', [{}])[0]
                               .get('commertialOffer', {})
                               .get('Price')
                               )
            result['measurement_unit'] = json.loads(product.get('properties', [{}])[0]
                                                           .get('values', ['{}'])[0]
                                                    ).get('measurement_unit_un')
            result['unit_multiplier'] = json.loads(product.get('properties', [{}])[0]
                                                           .get('values', ['{}'])[0]
                                                    ).get('unit_multiplier_un')
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
        next_page = self.generate_request(category=category, _from=product_index,
                                          _to=product_index + self.page_size - 1)
        try:
            yield scrapy.Request(next_page, callback=self.parse,
                                 cb_kwargs={'category': category, 'product_index': product_index})
        except Exception as e:
            raise e