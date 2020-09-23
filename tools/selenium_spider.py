from selenium import webdriver


brower = webdriver.Chrome(executable_path="F:\scrapy\ArticleSpider\/tools\chromedriver.exe")
brower.get('https://detail.tmall.com/item.htm?spm=a230r.1.14.3.yYBVG6&id=538286972599&cm_id=140105335569ed55e27b&abbucket=15&sku_properties=10004:709990523;5919063:6536025')
print(brower.page_source)