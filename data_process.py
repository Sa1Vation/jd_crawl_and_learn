#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
from multiprocessing.dummy import Pool
import pymongo
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import jieba
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score
from sklearn import metrics
import joblib
import argparse


def get_parser():  # 获取命令行参数
    parser = argparse.ArgumentParser(description='train model')
    parser.add_argument('-d', '--database', type=str, help='数据库的名字')
    parser.add_argument('-a', '--action', type=str, help='输入行为')
    return parser


def chinese_word_cut(mytext):
    return " ".join(jieba.cut(mytext))


def get_custom_stopwords(stop_words_file):
    with open(stop_words_file, encoding='utf-8') as f:
        stopwords = f.read()
    stopwords_list = stopwords.split('\n')
    custom_stopwords_list = [i for i in stopwords_list]
    return custom_stopwords_list


def build_model(dbname):
    mongodb = dbname
    ranktable = mongodb + 'rank'
    client = pymongo.MongoClient('localhost', 27017)
    dataname = client[mongodb]
    global table2
    len_dict = {}
    table2 = dataname[ranktable]
    global df
    df = pd.DataFrame(data=list(table2.find()))
    df = df.drop(columns=['_id', 'date', 'usernick', 'skuId'])
    df = df.loc[lambda df: df["content"] != "此用户未填写评价内容"]
    df = df.loc[lambda df: df["score"] != 3]
    df['sentiment'] = df['score'].apply(lambda x: 1 if x > 3 else 0)
    df_neg = df.loc[lambda df: df["sentiment"] == 0]
    df_pos = df.loc[lambda df: df["sentiment"] == 1]
    sample_size = min(df_neg.shape[0], df_pos.shape[0])
    if sample_size == df_neg.shape[0]:
        df_pos = df_pos.sample(n=sample_size, random_state=None)
    else:
        df_neg = df_neg.sample(n=sample_size, random_state=None)

    print('df_neg', df_neg.shape)
    print('df_pos', df_pos.shape)
    df = pd.concat([df_pos, df_neg])
    X = df[['content']]
    y = df.sentiment
    X['cutted_comment'] = X.content.apply(chinese_word_cut)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)
    # 数据降维
    stop_words_file = "stopwords.txt"
    stopwords = get_custom_stopwords(stop_words_file)
    max_df = 0.8
    min_df = 3
    vect = CountVectorizer(max_df=max_df,
                           min_df=min_df,
                           token_pattern=u'(?u)\\b[^\\d\\W]\\w+\\b',
                           stop_words=frozenset(stopwords))
    term_matrix = pd.DataFrame(vect.fit_transform(X_train.cutted_comment).toarray(), columns=vect.get_feature_names())
    nb = MultinomialNB()
    pipe = make_pipeline(vect, nb)
    cross_score = cross_val_score(pipe, X_train.cutted_comment, y_train, cv=5, scoring='accuracy').mean()
    print(f"====训练交叉预测准确率:{cross_score}====")
    # 模型拟合
    pipe.fit(X_train.cutted_comment, y_train)
    pipe.predict(X_test.cutted_comment)
    y_pred = pipe.predict(X_test.cutted_comment)
    model_acc = metrics.accuracy_score(y_test, y_pred)
    print(f"====模型预测准确率:{model_acc}====")
    confusion_m = metrics.confusion_matrix(y_test, y_pred)
    print("=======混淆矩阵======")
    print(confusion_m)
    print("====================")
    print("正在保存模型......")
    print("====================")
    model_file_name = dbname + '_trained_model.pkl'
    joblib.dump(pipe, model_file_name)
    print("保存成功")


def predict(comment, dbname):
    model_file_name = dbname + '_trained_model.pkl'
    model = joblib.load(model_file_name)
    df2 = pd.DataFrame(data=[{'content': comment}])
    to_pred = df2[['content']]
    to_pred['cutted_comment'] = to_pred.content.apply(chinese_word_cut)
    a_pred = model.predict(to_pred.cutted_comment)
    if a_pred[0] == 0:
        print("这是一条差评")
    elif a_pred[0] == 1:
        print("这是一条好评")


if __name__ == "__main__":
    parser = get_parser()
    args = vars(parser.parse_args())
    if args['database'] and args['action'] == 'build':
        build_model(args['database'])
    elif args['database'] and args['action'] == 'predict':
        comment = input("请输入一段评论文字:")
        predict(comment, args['database'])
