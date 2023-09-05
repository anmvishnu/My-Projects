# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class QuoteItem(scrapy.Item):
    # define the fields for your item here like:
    text = scrapy.Field()
    author = scrapy.Field()
    tags = scrapy.Field()

class AmazonProductItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    stars = scrapy.Field()
    rating_count = scrapy.Field()
    feature_bullets = scrapy.Field()
    images = scrapy.Field()
    variant_data = scrapy.Field()
    Reviews_count = scrapy.Field()
    asin=scrapy.Field()

class AmazonProductReviews(scrapy.Item):
    asin = scrapy.Field()
    text = scrapy.Field()
    title = scrapy.Field()
    rating = scrapy.Field()
    Total_reviews=scrapy.Field()

    
