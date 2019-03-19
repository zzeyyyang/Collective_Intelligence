import math
import optimization
from PIL import Image, ImageDraw

people = ['Charlie', 'Augustus', 'Veruca', 'Violet', 'Mike', 'Joe', 'Willy', 'Miranda']

links = [('Augustus', 'Willy'),
         ('Mike', 'Joe'),
         ('Miranda', 'Mike'),
         ('Violet', 'Augustus'),
         ('Miranda', 'Willy'),
         ('Charlie', 'Mike'),
         ('Veruca', 'Joe'),
         ('Miranda', 'Augustus'),
         ('Willy', 'Augustus'),
         ('Joe', 'Charlie'),
         ('Veruca', 'Augustus'),
         ('Miranda', 'Joe')]

# 计算交叉线作为成本函数
def crosscount(v):
    # 将数字序列转换成一个person:(x, y)的字典
    loc = dict([(people[i], (v[i*2], v[i*2+1])) for i in range(0, len(people))])
    total = 0

    # 遍历每一对连线
    for i in range(len(links)):
        for j in range(i+1, len(links)):

            # 获取坐标位置
            (x1, y1), (x2, y2) = loc[links[i][0]], loc[links[i][1]]
            (x3, y3), (x4, y4) = loc[links[j][0]], loc[links[j][1]]

            den = (y4 - y3)*(x2 - x1) - (x4 - x3)*(y2 - y1)

            # 若两直线平行，则den为0
            if den == 0: continue

            # 否则， ua与ub就是两条交叉线的分数值
            ua = ((x4 - x3)*(y1 - y3) - (y4 - y3)*(x1 - x3)) / den
            ub = ((x2 - x1)*(y1 - y3) - (y2 - y1)*(x1 - x3)) / den

            if ua > 0 and ua < 1 and ub > 0 and ub < 1:
                total += 1

    # 对两个节点放置太近的题解进行惩罚
    for i in range(len(people)):
        for j in range(i+1, len(people)):
            (x1, y1), (x2, y2) = loc[people[i]], loc[people[j]]

            dist = math.sqrt(math.pow(x1-x2, 2) + math.pow(y1-y2, 2))

            # 对间距小于50个像素的节点判罚
            if dist < 50:
                total += (1.0 - (dist/50.0))

    return total


# 坐标值范围
domain = [(10, 370)] * (len(people) * 2)


def drawnetwork(sol):
    img = Image.new('RGB', (400, 400), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    pos = dict([(people[i], (sol[i*2], sol[i*2+1])) for i in range(0, len(people))])

    for (a, b) in links:
        draw.line((pos[a], pos[b]), fill=(255, 0, 0))

    for n, p in pos.items():
        draw.text(p, n, (0, 0, 0))

    img.show()


if __name__ == '__main__':
    sol = optimization.randomoptimize(domain, crosscount)
    print(crosscount(sol))

    sol = optimization.annealingoptimize(domain, crosscount, step=50, cool=0.99)
    print(crosscount(sol))

    print(sol)

    drawnetwork(sol)
