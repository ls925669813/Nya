# -*- coding: utf-8 -*-
import datetime
import json
import re
import time
import pickle
import scrapy
from urllib import parse

from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuAnswerItem

from selenium import webdriver
from mouse import move
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit={1}&offset={2}'

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhizhu.com",
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0"
    }

    def parse(self, response):
        '''
        提取出html页面中的所有url, 并跟踪这些url进行下一步爬取
        如果提取的url中格式为/question/xxx 就进行下载之后直接进入解析函数
        '''
        all_urls = response.css('div:nth-child(2) meta:nth-child(1)::attr(content)').extract()
        for url in all_urls:
            yield scrapy.Request(url=url,headers=self.headers,callback=self.parse_question)
            # break

    def parse_question(self, response):
        #处理question页面, 从页面中提取出具体的question item

        match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
        question_id = int(match_obj.group(2))
        #
        # item_loader = ItemLoader(item=ZhihuAnswerItem(), response=response)
        # # item_loader.add_css('title','.PageHeader .QuestionHeader-title::text')
        # item_loader.add_css("content", ".QuestionHeader-detail")
        # item_loader.add_value("url", response.url)
        # item_loader.add_value("zhihu_id", question_id)
        # item_loader.add_css("answer_num", ".List-headerText span::text")
        # item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
        # item_loader.add_css("watch_user_num", ".NumberBoard-itemValue::text")
        # item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
        #
        # question_item = item_loader.load_item()
        yield scrapy.Request(self.start_answer_url.format(question_id,20,0),headers=self.headers,
                             callback=self.parse_answer)


    def parse_answer(self, response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    # def start_requests(self):
    #     return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers, callback=self.login)]

    # def start_requests(self):
    #     # 手动启动chromedriver 有一些js变量
    #     # 1.启动chrome(启动前确保所有的chrome实例已经关闭)
    #     #
    #     # 用存储的cookies直接登陆
    #     cookies = pickle.load(open("F:/scrapy/ArticleSpider/cookies/zhihu.cookie", "rb"))
    #     cookie_dict = {}
    #     for cookie in cookies:
    #         cookie_dict[cookie["name"]] = cookie["value"]
    #     try:
    #         return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]
    #     except:
    #         selenium_login()
    #         return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]
    #


# 用登陆好的界面存储cookies
def selenium_login():
    chrome_option = Options()
    chrome_option.add_argument("--disable extensions")
    chrome_option.add_experimental_option("debuggerAddress","127.0.0.1:9222")

    brower = webdriver.Chrome(executable_path="F:\scrapy\ArticleSpider\/tools\chromedriver.exe",
                              chrome_options=chrome_option
                              )
    # brower.get('https://www.zhihu.com/signin')
    # brower.find_element_by_css_selector(".SignFlow-tabs > div:nth-child(2)").click()
    # brower.find_element_by_css_selector(".SignFlow-account input").send_keys(Keys.CONTROL+"a")
    # brower.find_element_by_css_selector(".SignFlow-account input").send_keys("13326798065")
    # brower.find_element_by_css_selector(".SignFlow-password input").send_keys(Keys.CONTROL+"a")
    # time.sleep(3)
    # brower.find_element_by_css_selector(".SignFlow-password input").send_keys("zq126958")
    # # move()
    # brower.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
    brower.get("http://www.zhihu.com/")
    cookies = brower.get_cookies()

    pickle.dump(cookies, open("F:/scrapy/ArticleSpider/cookies/zhihu.cookie","wb"))
    cookie_dict = {}
    for cookie in cookies:
        cookie_dict[cookie["name"]] = cookie["value"]

    # return [scrapy.Request(url=self.start_urls[0],dont_filter=True,cookies=cookie_dict)]
