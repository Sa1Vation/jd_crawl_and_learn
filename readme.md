# 电商评论爬虫，朴素贝叶斯模型预测
## 要求：
### mongodb, chromeDriver

## 爬取商品数据
### python crawl_taobao.py -k 关键词 -d 数据库名
## 爬取评论数据
### python crawl_taobao.py -d 数据库名 -r 任意字符
## 建立模型
### python data_process.py -d 数据库名 -a build
## 爬取数据
### python data_process.py -d 数据库名 -a predict