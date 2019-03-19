# -*- coding: utf-8 -*-
from random import random, randint
import math


def wineprice(rating, age):
    peak_age = rating - 50

    price = rating / 2
    if age > peak_age:
        price *= (5 - (age-peak_age))
    else:
        price *= (5 * ((age+1)/peak_age))
    if price < 0:
        price = 0
    return price


def wineset1():
    rows = []
    for i in range(300):
        rating = random.random()*50 + 50
        age = random.random()*50

        price = wineprice(rating, age)

        # 增加噪声
        price *= (random.random()*0.4 + 0.8)

        rows.append({'input': (rating, age), 'result': price})

    return rows


def wineset2():
    rows = []
    for i in range(300):
        rating = random.random()*50 + 50
        age = random.random()*50

        aisle = float(randint(1, 20))
        bottlesize = [375.0, 750.0, 1500.0, 3000.0][randint(0, 3)]
        price = wineprice(rating, age)
        price *= (bottlesize/750)
        price *= (random.random()*0.9 + 0.2)

        rows.append({'input': (rating, age, aisle, bottlesize), 'result': price})
    return rows


def wineset3():
    rows = wineset1()
    for row in rows:
        if random.random() < 0.5:
            row['result'] = 0.5
    return rows


# k-NN

# 定义相似度(欧几里得距离)
def euclidean(v1, v2):
    d = 0.0
    for i in range(len(v1)):
        d += (v1[i]-v2[i])**2
    return math.sqrt(d)


def getdistances(data, vec1):
    distancelist = []
    for i in range(len(data)):
        vec2 = data[i]['input']
        distancelist.append((euclidean(vec1, vec2), i))
    distancelist.sort()
    return distancelist


def knnestimate(data, vec1, k=5):
    dlist = getdistances(data, vec1)
    avg = 0.0

    for i in range(k):
        idx = dlist[i][1]
        avg += data[idx]['result']
    avg /= k

    return avg


# 为近邻分配权重
# 反函数
def inverseweight(dist, num=1.0, const=0.1):
    return num / (dist + const)


# 减法函数
def subtractweight(dist, const=1.0):
    if dist > const:
        return 0
    else:
        return const-dist


# 高斯函数
def gaussian(dist, sigma=10.0):
    return math.e**(-dist**2/(2*sigma**2))


# 加权k-NN
def weightedknn(data, vec1, k=5, weightf=gaussian):
    dlist = getdistances(data, vec1)
    avg = 0.0
    totalweight = 0.0

    for i in range(k):
        dist = dlist[i][0]
        idx = dlist[i][1]
        weight = weightf(dist)
        avg += weight*data[idx]['result']
        totalweight += weight
    avg /= totalweight
    return avg


# Cross Validation
def dividedata(data, test=0.05):
    trainset = []
    testset = []
    for row in data:
        if random.random() < test:
            testset.append(row)
        else:
            trainset.append(row)
    return trainset, testset


def testalgorithm(algf, trainset, testset):
    error = 0.0
    for row in testset:
        guess = algf(trainset, row['input'])
        error += (row['result']-guess)**2
    return error/len(testset)


def crossvalidate(algf, data, trials=100, test=0.05):
    error = 0.0
    for i in range(trials):
        trainset, testset = dividedata(data, test)
        error += testalgorithm(algf, trainset, testset)
    return error/trials


# 对各个维度按比例缩放
def rescale(data, scale):
    scaleddata = []
    for row in data:
        scaled = [scale[i]*row['input'][i] for i in range(len(scale))]
        scaleddata.append({'input': scaled, 'result': row['result']})
    return scaleddata


# 优化缩放结果(寻找最优scale)
def createcostfunction(algf, data):
    def costf(scale):
        sdata = rescale(data, scale)
        return crossvalidate(algf, sdata, trials=10)
    return costf


weightdomain = [(0, 20)] * 4  # 利用优化算法(如退火)进行搜索


# 计算价格在[low, high]区间内的概率
def probguess(data, vec1, low, high, k=5, weightf=gaussian):
    dlist = getdistances(data, vec1)
    nweight = 0.0
    tweight = 0.0

    for i in range(k):
        dist = dlist[i][0]
        idx = dlist[i][1]
        weight = weightf(dist)
        v = data[idx]['result']

        if low <= v <= high:
            nweight += weight
        tweight += weight
    if tweight == 0:
        return 0

    return nweight/tweight


from pylab import *


# 绘制概率分布
def cumulativegraph(data, vec1, high, k=5, weightf=gaussian):
    t1 = arange(0.0, high, 0.1)
    cprob = array([probguess(data, vec1, 0, v, k, weightf) for v in t1])
    plot(t1, cprob)
    show()


def probabilitygraph(data, vec1, high, k=5, weightf=gaussian, ss=5.0):
    t1 = arange(0.0, high, 0.1)
    probs = [probguess(data, vec1, v, v+0.1, k, weightf) for v in range(t1)]

    # 平滑处理
    smoothed = []
    for i in range(len(probs)):
        sv = 0.0
        for j in range(len(probs)):
            dist = abs(i-j) * 0.1
            weight = gaussian(dist, sigma=ss)
            sv += weight*probs[j]
        smoothed.append(sv)
    smoothed = array(smoothed)

    plot(t1, smoothed)
    show()


if __name__ == '__main__':
    data = wineset3()
    cumulativegraph(data, (1, 1), 120)
