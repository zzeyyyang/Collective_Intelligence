# -*- coding: utf-8 -*-
import feedparser
import re
import docclass


def read(feed, classifier):
    f = feedparser.parse(feed)
    for entry in f['entries']:
        print
        print '-----'
        print 'Title:     ' + entry['title'].encode('utf-8')
        print 'Publisher: ' + entry['publisher'].encode('utf-8')
        print
        print entry['summary'].encode('utf-8')

        # fulltext = '%s\n%s\n%s' % (entry['title'], entry['publisher'], entry['summary'])

        print 'Guess: ' + str(classifier.classify(entry))

        cl = raw_input('Enter category: ')
        classifier.train(entry, cl)


def entryfeatures(entry):
    splitter = re.compile('\\W*')
    f = {}

    titlewords = [s.lower() for s in splitter.split(entry['title']) if 2 < len(s) < 20]
    for w in titlewords:
        f['Title:'+w] = 1

    summarywords = [s.lower() for s in splitter.split(entry['summary']) if 2 < len(s) < 20]

    # 统计大写单词
    uc = 0
    for i in range(len(summarywords)):
        w = summarywords[i]
        f[w] = 1
        if w.isupper():
            uc += 1

        # 将从摘要中获得的词组作为特征
        if i < len(summarywords)-1:
            towords = ' '.join(summarywords[i:i+1])
            f[towords] = 1

        f['Publisher:'+entry['publisher']] = 1

        # 用以指示是否存在过多的大写内容
        if float(uc) / len(summarywords) > 0.3:
            f['UPPERCASE'] = 1

        return f


if __name__ == '__main__':
    # cl = docclass.fisherclassifier(docclass.getwords)
    cl = docclass.fisherclassifier(entryfeatures)
    cl.setdb('python_feed.db')
    read('python_search.xml', cl)
