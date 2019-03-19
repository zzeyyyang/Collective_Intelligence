import time
import random
import math

people = [('Seymour', 'BOS'),
          ('Franny', 'DAL'),
          ('Zooey', 'CAK'),
          ('Walt', 'MIA'),
          ('Buddy', 'ORD'),
          ('Les', 'OMA')]

destination = 'LGA'

flights = {}

for line in open('schedule.txt'):
    origin, dest, depart, arrive, price = line.strip().split(',')
    flights.setdefault((origin, dest), [])

    # 将航班详情添加到航班列表中
    flights[(origin, dest)].append((depart, arrive, int(price)))


# 计算某个给定时间在一天中的分钟数
def getminutes(t):
    x = time.strptime(t, '%H:%M')  # x = [year, month, day, hour, min, sec, ...]
    return x[3]*60 + x[4]


# 数字序列表示航班次（从0开始） 列表长度是人数的两倍（每个人都需要往返两个航班）
def printschedule(r):
    for d in range(int(len(r)/2)):
        name = people[d][0]
        origin = people[d][1]
        out = flights[(origin, destination)][int(r[2*d])]
        ret = flights[(destination, origin)][int(r[2*d+1])]
        print('%10s%10s %5s-%5s $%3s %5s-%5s $%3s' % (name, origin,
                                                     out[0], out[1], out[2],
                                                     ret[0], ret[1], ret[2])) # 人名和起点、出发时间、到达时间、往返航班票价


# 成本函数
def schedulecost(sol):
    totalprice = 0
    latestarrival = 0
    ealiestdep = 24*60

    for d in range(int(len(sol)/2)):
        # 得到往程航班和返程航班
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[2*d])]
        returnf = flights[(destination, origin)][int(sol[2*d+1])]

        # 总价格等于所有往程航班和返程航班价格之和
        totalprice += outbound[2]
        totalprice += returnf[2]

        # 记录最晚到达时间和最早离开时间
        if latestarrival < getminutes(outbound[1]): latestarrival = getminutes(outbound[1])
        if ealiestdep > getminutes(returnf[0]): ealiestdep = getminutes(returnf[0])

    # 每个人必须在机场等待直到最后一个人到达为止
    # 他们也必须在相同时间到达，并等候他们的返程航班
    totalwait = 0
    for d in range(int(len(sol)/2)):
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[2*d])]
        returnf = flights[(destination, origin)][int(sol[2*d+1])]
        totalwait += latestarrival - getminutes(outbound[1])
        totalwait += getminutes(returnf[0]) - ealiestdep

    # 判断是否多付一天租车费用
    if latestarrival < ealiestdep: totalprice += 50

    return totalprice + totalwait


# 随机搜索
def randomoptimize(domain, costf):
    best = 999999999
    bestr = None
    for i in range(1000):
        # 创建一个随机解
        r = [random.randint(domain[i][0], domain[i][1])
             for i in range(len(domain))]

        cost = costf(r)

        if cost < best:
            best = cost
            bestr = r

        return r


# 爬山法
# 从一个随机解开始，在临近的解集中寻找更好的解
def hillclimb(domain, costf):
    sol = [random.randint(domain[i][0], domain[i][1])
         for i in range(len(domain))]
    print(sol)
    print(domain)

    while 1:
        # 创建相邻解的列表
        neighbors = []
        for j in range(len(domain)):
            # 在每个方向上相对于原值偏离一点
            if sol[j] > domain[j][0]:
                neighbors.append(sol[0:j] + [sol[j] - 1] + sol[j+1:])
            if sol[j] < domain[j][1]:
                neighbors.append(sol[0:j] + [sol[j] + 1] + sol[j+1:])
        print(neighbors)

        # 在相邻解中寻找最优解
        current = costf(sol)
        best = current
        for j in range(len(neighbors)):
            cost = costf(neighbors[j])
            if cost < best:
                best = cost
                sol = neighbors[j]
        if best == current:
            break

    return sol


# 模拟退火算法
def annealingoptimize(domain, costf, T=10000.0, cool=0.95, step=1):
    vec = [float(random.randint(domain[i][0], domain[i][1]))
           for i in range(len(domain))]

    while T > 0.1:
        # 选择一个索引值
        i = random.randint(0, len(domain) - 1)
        # 选择一个改变索引值的方向
        dir = random.randint(-step, step)

        # 创建一个代表题解的新列表，改变其中一个值
        vecb = vec[:]
        vecb[i] += dir
        # 防止越界
        if vecb[i] < domain[i][0]: vecb[i] = domain[i][0]
        elif vecb[i] > domain[i][1]: vecb[i] = domain[i][1]

        ea = costf(vec)
        eb = costf(vecb)

        # 随着温度的递减，高成本值和低成本值差异越来越重要，差异越大，接受的概率就越低
        # 因此该算法只倾向于稍差的解而不会是非常差的解
        p = pow(math.e, -(eb-ea) / T)
        if (eb < ea or random.random() < p):
            vec = vecb

        T = T*cool
    return vec


# 遗传算法
# 排序选择原种群最优题解，新种群的余下部分是由修改最优解后形成的全新解组成
def geneticoptimize(domain, costf, popsize=50, step=1,
                    mutprob=0.2, elite=0.2, maxiter=100):
    # 变异操作
    def mutate(vec):
        i = random.randint(0, len(domain) - 1)
        if random.random() < 0.5 and vec[i] > domain[i][0]: # 0.5为发生哪一种变异的概率
            return vec[0:i] + [vec[i] - step] + vec[i+1:]
        elif vec[i] < domain[i][1]:
            return vec[0:i] + [vec[i] + step] + vec[i+1:]

    # 交叉操作
    def crossover(r1, r2):
        i = random.randint(1, len(domain) - 2) # 范围限定了一定发生交叉
        return r1[0:i] + r2[i:]

    # 构造初始种群
    pop = []
    for i in range(popsize):
        vec = [random.randint(domain[i][0], domain[i][1])
               for i in range(len(domain))]
        pop.append(vec)

    # 每一代胜出者数目
    topelite = int(elite*popsize)

    for i in range(maxiter):
        scores = [(costf(v), v) for v in pop]
        scores.sort()
        ranked = [v for (s, v) in scores]

        # 加入纯粹的胜出者
        pop = ranked[0:topelite]

        # 添加变异和交叉后的胜出者
        while len(pop) < popsize:
            if random.random() < mutprob: # mutprob为变异概率
                # 变异
                c = random.randint(0, topelite)
                pop.append(mutate(ranked[c]))
            else:
                # 交叉
                c1 = random.randint(0, topelite)
                c2 = random.randint(0, topelite)
                pop.append(crossover(ranked[c1], ranked[c2]))
        # 打印当前最优值
        print(scores[0][0])

    return scores[0][1]
