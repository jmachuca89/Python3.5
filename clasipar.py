import scrapy
from Clasipar.items import AnuncioItem
import json
from scrapy.selector import Selector
import re
import datetime


class ClasiparSpider(scrapy.Spider):
    name = "clasifull"

    # allowed_domains = ['https://clasipar.paraguay.com/']
    start_urls = [
        "https://clasipar.paraguay.com/",
    ]

    def parse(self, response):
        categorias = response.css(
            "div.panel-heading h2.panel-title a::attr(href)").extract()
        for categoria in categorias:
            yield scrapy.Request(categoria, callback=self.subcategorias)

    def subcategorias(self, response):
        subcategorias = response.css(
            "div.subcategorias ul li h2 a::attr(href)").extract()
        for subcategoria in subcategorias:
            yield scrapy.Request(subcategoria+"/page-1", callback=self.anuncios)

    def anuncios(self, response):

        # scrapea lista de anuncios y sigue paginacion
        detalles = response.css("article.box-anuncio")  # .extract()
        for anuncio in detalles:
            item = AnuncioItem()
            a = anuncio.css("h6 span strong::text").extract()
            if a:
                item['intencion'] = a[0]
                item['oferente'] = a[1]
            item['nroAnuncio'] = (anuncio.css(
                "a.titAnuncio::attr(href)").extract_first()).split("-")[-1]
            link_anuncio = anuncio.css(
                "a.titAnuncio::attr(href)").extract_first()
            yield scrapy.Request(link_anuncio, callback=self.anuncioDetalle, meta={"item": item})
        next_page = response.css("li.active + li a::text").extract_first()
        if next_page is not None:
            base = re.search("/page-", response.url)
            base = response.url[:base.start()]
            next_page = base + "/page-" + next_page
            # next_page = response.urljoin(("/page-" + next_page))
            yield scrapy.Request(next_page, callback=self.anuncios)

    def anuncioDetalle(self, response):
        item = response.meta['item']
        item['titulo'] = response.css(
            "h1 span[itemprop='name']::text").extract_first()
        item['anunciante'] = response.css(
            '.infoAnunciante__header').css("h5::text").extract_first()
        precio = (response.css(
            '.user-price::text').extract_first()).split(" ")
        if "onsul" not in precio[0]:
            if "Gs." in precio[0]:
                item['precio'] = {"Moneda": precio[0],
                                  "Valor": int(precio[1].replace(".", ""))}
            else:
                item['precio'] = {"Moneda": precio[0],
                                  "Valor": float((precio[1].replace(".", "")).replace(",", "."))}
        else:
            item['precio'] = {"Moneda": "Undefined", "Valor": "Undefined"}
        detalles = response.css('.anuncio-detalles')
        for detalle in detalles.css(".grid__item"):
            if detalle.css('span::text').extract_first() == "Departamento:":
                item['departamento'] = detalle.css('h6::text').extract_first()
            elif detalle.css('span::text').extract_first() == "Nro. de Anuncio:":
                item['nroAnuncio'] = int(
                    detalle.css('h6::text').extract_first())
            elif detalle.css('span::text').extract_first() == "Zona:":
                item['zona'] = detalle.css('h6::text').extract_first()
            elif detalle.css('span::text').extract_first() == "Nro. de Visitas:":
                item['visitas'] = int(detalle.css('h6::text').extract_first())
            elif detalle.css('span::text').extract_first() == "Publicado el:":
                newDate = detalle.css('h6::text').extract_first()
                newDate = newDate.split("/")
                item['fechaPublicacion'] = datetime.datetime(
                    int(newDate[2]), int(newDate[1]), int(newDate[0]), 5, 0)
            elif detalle.css('span::text').extract_first() == "Ciudad:":
                item['ciudad'] = detalle.css(
                    'h6::text').extract_first()
            else:
                pass
        item['descripcion'] = " ".join(response.css(
            '.desc-user::text').extract())
        item['intencion'] = response.css("h6.pull-left::text").extract_first()
        item['url'] = response.url
        bread = (response.url).split("/")
        item['categoria'] = bread[3]
        item['subcategoria'] = bread[4]
        script = re.compile("btn_view_info")
        separacion = re.split(script, response.css("body").extract_first())
        m = re.search(r"var token = \'", separacion[2])
        m2 = re.search(r"\';", separacion[2])
        token = separacion[2][m.end():m2.start()]
        n = re.search(r"var code = \'", separacion[2])
        n2 = re.search(r"\';", (separacion[2][n.end():]))
        code = separacion[2][n.end():(n2.start()+n.end())]
        consulta = "https://clasipar.paraguay.com/src/async/request_ads_data?token=" + \
            token + "&code="+code  # ajax request con token y codigo
        yield scrapy.Request(consulta, callback=self.numeroEmail, meta={"item": item}, method="POST")

    def numeroEmail(self, response):
        # r = json.loads(response.css("p").extract())
        r = response.css("body").extract_first()
        item = response.meta['item']
        m = re.search(r"\"phone_number\"\:\"", r)
        m2 = re.search(r"\",", r[m.end():])
        # phone
        # 1er caso: puede tener varios telefonos separados por espacios
        item['telefono'] = r[m.end():(m.end()+m2.start())]
        n = re.search(r"mailto\:", r)
        n2 = re.search(r"\%5C", r[n.end():])
        item['email'] = r[n.end():(n.end()+n2.start())]

        # item['email'] = j['email']
        # item['phone'] = j['phone']
        return item

        # categorias
        # response.css("div.panel-heading h2.panel-title a::attr(href)").extract()
        # subcategorias
        # response.css("div.subcategorias ul li h2 a::attr(href)").extract()
        # anuncio
        # response.css("article.box-anuncio")
        # intencion y oferente
        # anuncios[0].css("div.box-anuncio__descripcion h6 span strong::text").extract()
        # numero de anuncio
        # numero = response.css("div.subcategorias ul li h2 a::attr(href)").extract()
        # numero.split("-")[-1]
        # token c-FaHrVze9lGDd2B4xO-0tM6KrX8HaifWjRs6YN30DJwS0e_stbVW4d93flygeW4kT8z_C6fhDXUc23qHmJT9g
        # code 1_3ewby1QjvsFQ9fNkCm7mfiXD03nE6Nm_f_eA6axrR5th0DvALfaGsTt3ISb-QmlzIpFHebbUi3om7yC1SxTA

        # https://clasipar.paraguay.com/src/async/request_ads_data?token=c-FaHrVze9lGDd2B4xO-0tM6KrX8HaifWjRs6YN30DJwS0e_stbVW4d93flygeW4kT8z_C6fhDXUc23qHmJT9g&code=1_3ewby1QjvsFQ9fNkCm7mfiXD03nE6Nm_f_eA6axrR5th0DvALfaGsTt3ISb-QmlzIpFHebbUi3om7yC1SxTA
