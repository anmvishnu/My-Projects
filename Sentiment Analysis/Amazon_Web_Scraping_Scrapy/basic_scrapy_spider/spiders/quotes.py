import json
import scrapy
from scrapy.loader import ItemLoader
from urllib.parse import urljoin
import re
from ..items import AmazonProductItem,AmazonProductReviews
from scrapy.exporters import CsvItemExporter 
import numpy as np

class AmazonSearchProductSpider(scrapy.Spider):
    name = "amazon_search_product"


    def start_requests(self):
        keyword_list = ['Gaming Laptops']
        self.csv_exporter = CsvItemExporter(
                open('amazon_data2.csv', 'wb')
            )
        self.csv_exporter.start_exporting()
        page_num=np.arange(1,10)
        for page,keyword in zip(page_num,keyword_list):
            amazon_search_url = f'https://www.amazon.in/s?k={keyword}&page={page}'
            yield scrapy.Request(url=amazon_search_url, callback=self.discover_product_urls, meta={'keyword': keyword, 'page': 1})


    def discover_product_urls(self, response):
        page = response.meta['page']
        keyword = response.meta['keyword'] 

        ## Discover Product URLs
        search_products = response.css("div.s-result-item[data-component-type=s-search-result]")
        for product in search_products:
            relative_url = product.css("h2>a::attr(href)").get()
            product_url = urljoin('https://www.amazon.in/', relative_url).split("?")[0]
            yield scrapy.Request(url=product_url, callback=self.parse_product_data, meta={'keyword': keyword, 'page': page})
            
        ## Get All Pages
        if page == 1:
            available_pages = response.xpath(
                '//*[contains(@class, "s-pagination-item")][not(has-class("s-pagination-separator"))]/text()'
            ).getall()

            last_page = available_pages[-1]
            for page_num in range(2, int(last_page)):
                amazon_search_url = f'https://www.amazon.in/s?k={keyword}&page={page_num}'
                yield scrapy.Request(url=amazon_search_url, callback=self.parse_search_results, meta={'keyword': keyword, 'page': page_num})

    def parse_product_data(self, response):
        
        image_data = json.loads(re.findall(r"colorImages':.*'initial':\s*(\[.+?\])},\n", response.text)[0])
        variant_data = re.findall(r'dimensionValuesDisplayData"\s*:\s* ({.+?}),\n', response.text)
        # print(type(variant_data))
        # print(variant_data)
        feature_bullets = [bullet.strip() for bullet in response.css("#feature-bullets li ::text").getall()]
        price = response.css('.a-price span[aria-hidden="true"] ::text').get("")
        if not price:
            price = response.css('.a-price .a-offscreen ::text').get("")

        # Use Item Loader
        loader = ItemLoader(item=AmazonProductItem(), response=response)
        loader.add_css("name", "#productTitle::text")
        loader.add_value("price", price)
        loader.add_css("stars", "i[data-hook=average-star-rating] ::text")
        # loader.add_css("rating_count", "div[data-hook=total-review-count] ::text")
        loader.add_value("variant_data", variant_data)
        yield loader.load_item()
        variant_dict = json.loads(variant_data[0])

        for variant in variant_dict.keys():
            amazon_reviews_url=f'https://www.amazon.in/product-reviews/{variant}/'
            yield scrapy.Request(url=amazon_reviews_url, callback=self.parse_reviews, meta={'asin': variant, 'retry_count': 0,'loader':loader})

            

    def parse_reviews(self, response):
        loader = response.meta['loader']
        asin=response.meta['asin']
        retry_count = response.meta['retry_count']
        next_page_relative_url = response.css(".a-pagination .a-last>a::attr(href)").get()

        
        
        if next_page_relative_url is not None:
            retry_count = 0
            next_page = urljoin('https://www.amazon.in/', next_page_relative_url)
            yield scrapy.Request(url=next_page, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': retry_count,'loader':loader})
        
        elif retry_count < 3:
            retry_count = retry_count+1
            yield scrapy.Request(url=response.url, callback=self.parse_reviews, dont_filter=True, meta={'asin': asin, 'retry_count': retry_count,'loader':loader})

        review_elements = response.css("#cm_cr-review_list div.review")
        
        # review_loader.update(loader)
        for review_element in review_elements:
            review_loader = ItemLoader(item=AmazonProductReviews(), response=response)
            review_loader.add_value("asin", asin)
            review_loader.add_value("text", "".join(review_element.css("span[data-hook=review-body] ::text").getall()).strip())
            review_loader.add_value("title", review_element.css("*[data-hook=review-title] > span::text").get())
            review_loader.add_value("rating", review_element.css("*[data-hook*=review-star-rating] ::text").re(r"(\d+\.*\d*) out")[0])
            review_loader.add_value("Total_reviews",review_element.css('*[data-hook=cr-filter-info-review-rating-count] ::text').get())
            yield review_loader.load_item()
            print("Name of the product",loader.get_output_value('name'))
            combined_data = {
                'name': loader.get_output_value('name'),
                'price': loader.get_output_value('price'),
                'stars': loader.get_output_value('stars'),
                'rating_count': loader.get_output_value('rating_count'),
                'variant_data': loader.get_output_value('variant_data'),
                'asin': asin,
                'review_title': review_loader.get_output_value('title'),
                'review_text': review_loader.get_output_value('text'),
                'review_rating': review_loader.get_output_value('rating'),
                'Total_reviews':review_loader.get_output_value('Total_reviews')
            }
            # encoded_data = {key: value.encode('utf-8').decode('utf-8') if value is not None else '' for key, value in combined_data.items()}
            self.csv_exporter.export_item(combined_data)
        

    def closed(self, reason):
        # Finish exporting when the spider is closed
        if self.csv_exporter:
            self.csv_exporter.finish_exporting()