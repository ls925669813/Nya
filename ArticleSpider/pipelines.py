# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import MySQLdb
import MySQLdb.cursors
from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline
import codecs
from twisted.enterprise import adbapi
from w3lib.html import remove_tags
from models.es_types import ArticleType

class ArticlespiderPipeline:
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipleline(object):
    #调用scrapy提供的json export导出json文件
    def __init__(self):
        self.file = codecs.open('article.json', 'wb',encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item),ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_close(self,spider):
        self.file.close()

class JsonExporterPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'wb',encoding='utf-8')
        self.exporter = JsonItemExporter(self.file,encoding='utf-8',ensure_ascii=False)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def spider_close(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect("localhost", "root", "123123", "article_spider", charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self,item,spider):
        insert_sql = '''
            insert into cnblog_article(title,url,url_object_id,front_image_path,front_image_url,parise_nums,comment_nums,fav_nums,tags,content,create_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        '''
        params = list()
        params.append(item.get("title",""))
        params.append(item.get("url",""))
        params.append(item.get("url_object_id",""))
        front_image = "".join(item.get("front_image_url",[]))
        params.append(front_image)
        params.append(item.get("front_image_path",""))
        params.append(item.get("praise_nums",0))
        params.append(item.get("comment_nums",0))
        params.append(item.get("fav_nums",0))
        params.append(item.get("tags",""))
        params.append(item.get("content",""))
        params.append(item.get("create_date","2020-8-1"))
        self.cursor.execute(insert_sql,tuple(params))
        self.conn.commit()

        return item

class MysqlTwistedPipeline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host = settings["MYSQL_HOST"],
            db = settings["MYSQL_DBNAME"],
            user = settings["MYSQL_USER"],
            passwd = settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常
        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        # 根据不同的item 构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if "front_image_url" in item:
            image_file_path = ""
            for ok,value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path

        return item

class ElasticsearchPipline(object):
    #讲数据写入到es中

    def process_item(self, item, spider):
        #将item转换为es的数据
        item.save_to_es()

        return item
