# -*- coding: utf-8 -*-
import json
import re

import scrapy
from scrapy import Request
from urllib import parse
import requests
# from scrapy.loader import ItemLoader
from selenium import webdriver

from ArticleSpider.items import ArticleItemLoader
from ArticleSpider.items import JobBoleArticleItem
from ArticleSpider.utils import common

from pydispatch import dispatcher
from scrapy import signals

class CnblogsSpider(scrapy.Spider):
    name = 'cnblogs'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    # def __init__(self):
    #     self.browser = webdriver.Chrome(executable_path="F:\scrapy\ArticleSpider\/tools\chromedriver.exe")
    #     super(CnblogsSpider, self).__init__()
    #     dispatcher.connect(self.spider_closed, signals.spider_closed)
    #
    # def spider_closed(self, spider):
    #     #当爬虫推出的时候关闭Chrome
    #     print("spider closed")
    #     self.browser.quit()

    #收集所有404的url以及404页面数
    handle_httpstatus_list = [404]
    def __init__(self):
        self.fail_urls = []


    def parse(self, response):
        """
        1.获取新闻列表页中的新闻url并交给scrapy进行下载后调用相应的解析方法
        2.获取下一页的url并交给scrapy进行下载，下载完成后交给parse继续跟进
        :param response:
        :return:
        """
        if response.status == 404:
            self.fail_urls.append(response.url)
            self.crawler.stats.inc_value("failed_url")

        post_nodes = response.css('#news_list .news_block')
        for post_node in post_nodes:
            image_url = post_node.css('.entry_summary a img::attr(src)').extract_first("")
            if image_url.startswith("//"):
                image_url = 'https:'+image_url
            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url,post_url),meta={"front_image_url":image_url}, callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载
        next_url = response.xpath("//a[contains(text(), 'Next >')]/@href").extract_first("")
        yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
        '''
        # 用css方法提取
        next_url = response.css('div.pager a:last-child::text').extract_first("")
        if next_url == "Next >":
            next = response.css('div.pager a:last-child::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
        '''

    def parse_detail(self,response):
        match_re = re.match(".*?(\d+)",response.url)
        if match_re:
        #     # article_item = cnblogsArticleItem()
        #     title = response.css('#news_title a::text').extract_first()
        #     create_date = response.css('#news_info span.time::text').extract_first()
        #     # 用正则表达式提取日期的值
        #     match_date = re.match(".*?(\d+.*)", create_date)
        #     if match_date:
        #         create_date = match_date.group(1)
        #     content = response.css("#news_content").extract()[0]
        #     tag_list = response.css(".news_tags a::text").extract()
        #     tags = ",".join(tag_list)
        #
        #     article_item["title"] = title
        #     article_item["create_date"] = create_date
        #     article_item["content"] = content
        #     article_item["tags"] = tags
        #     article_item["url"] = response.url
        #     # article_item["front_image_url"] = [response.meta.get("front_image_url", "")]
        #     #如果front_image_url是空的就传入一个空字典
        #     if response.meta.get("front_image_url",""):
        #         # 下载图片的url链接必须要有":",__int__规定的
        #         if ':' not in response.meta.get("front_image_url",""):
        #             image_url = 'https:' + response.meta.get("front_image_url","")#否则就加上https:,符合规则
        #             article_item["front_image_url"] = [image_url]
        #         else:
        #             article_item["front_image_url"] = [response.meta.get("front_image_url","")]
        #     else:
        #         article_item["front_image_url"] = []

            post_id = match_re.group(1)
            item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
            item_loader.add_css("title", "#news_title a::text")
            item_loader.add_css("create_date", "#news_info .time::text")
            item_loader.add_css("content", "#news_content")
            item_loader.add_css("tags", ".news_tags a::text")
            item_loader.add_value("url", response.url)
            if response.meta.get("front_image_url", []):
                item_loader.add_value("front_image_url", response.meta.get("front_image_url", []))

            # article_item = item_loader.load_item()


            yield Request(url=parse.urljoin(response.url,"/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                          meta={"article_item":item_loader,"url":response.url},callback=self.parse_nums)

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        item_loader = response.meta.get("article_item", "")

        # praise_nums = j_data["DiggCount"]
        # fav_nums = j_data["TotalView"]
        # comment_nums = j_data["CommentCount"]
        #
        # article_item["praise_nums"] = praise_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["comment_nums"] = comment_nums
        # item_loader["url_object_id"] = common.get_md5(article_item["url"])

        item_loader.add_value("praise_nums", j_data["DiggCount"])
        item_loader.add_value("fav_nums", j_data["TotalView"])
        item_loader.add_value("comment_nums", j_data["CommentCount"])
        item_loader.add_value("url_object_id", common.get_md5(response.meta.get("url", "")))

        article_item = item_loader.load_item()

        yield article_item