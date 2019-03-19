import random
import math
import optimization


# 代表宿舍，每个宿舍有两个可用的隔间
dorms = ['Zeus', 'Athena', 'Hercules', 'Bacchus', 'Pluto']

# 代表学生及其首选和次选
prefs = [('Toby', ('Bacchus', 'Hercules')),
         ('Steve', ('Zeus', 'Pluto')),
         ('Andrea', ('Athena', 'Zeus')),
         ('Sarah', ('Zeus', 'Pluto')),
         ('Dave', ('Athena', 'Bacchus')),
         ('Jeff', ('Hercules', 'Pluto')),
         ('Fred', ('Pluto', 'Athena')),
         ('Suzie', ('Bacchus', 'Hercules')),
         ('Laura', ('Bacchus', 'Hercules')),
         ('Neil', ('Hercules', 'Athena'))]

# 构造10个槽用以将学生依次安置于空槽内
domain = [(0, (len(dorms)*2) - i - 1) for i in range(0, len(dorms)*2)]


def printsolution(vec):
    slots = []
    # 为每个宿舍建两个槽
    for i in range(len(dorms)): slots += [i, i]
    # 遍历每一名学生的安置情况
    for i in range(len(vec)):
        x = int(vec[i])
        # 从剩余槽中选择
        dorm = dorms[slots[x]]
        print(prefs[i][0], dorm)
        # 删除该槽
        del slots[x]


# 成本函数
def dormcost(vec):
    cost = 0
    slots = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]

    for i in range(len(vec)):
        x = int(vec[i])
        dorm = dorms[slots[x]]
        pref = prefs[i][1]
        # 首选成本为0，次选成本为1，不在选择之列成本为3
        if pref[0] == dorm: cost+= 0
        elif pref[1] == dorm: cost += 1
        else: cost += 3

        del slots[x]
    return cost


if __name__ == '__main__':
    printsolution([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    # 执行优化函数
    s = optimization.randomoptimize(domain, dormcost)
    print(dormcost(s))
    optimization.geneticoptimize(domain, dormcost)
    printsolution(s)


