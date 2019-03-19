# -*- coding: utf-8 -*- 
from BeautifulSoup import BeautifulSoup
import urllib2
import re

chare = re.compile(r'[!-\.&]')
itemowners = {}
# 要去除的单词
dropwords = ['a','new','some','more','my','own','the','many','other','another']

currentuser = 0
for i in range(1,51):

	c = urllib2.urlopen('http://member.zebo.com/Main?event_key=USERSEARCH&wiowiw=wiw&keyword=car&page=%d'
		% (i))
	soup = BeautifulSoup(c.read())
	for td in soup('td'):
		if('class' in dict(td.attrs) and td['class'] == 'bgverdanasmall'):
			items = [re.sub(chare, '', a.contents[0].lower()).strip() for a in td('a')]
			for item in items:
				# 去除多余的单词
				txt = ' '.join([t for t in item.split(' ') if t not in dropwords])
				if len(txt)<2: continue
				itemowners.setdefault(txt, {})
				itemowners[txt][currentuser] = 1
			currentuser += 1

# 构造一个以匿名用户为列、以物品为行的矩阵，希望拥有某件物品标记为1，否则标记为0
out = file('zebo.txt', 'w')
out.write('Item')
for user in range(0, currentuser): out.write('\tU%d' % user)
out.write('\n')
for item, owners in itemowners.items():
	if len(owners) > 10:
		out.write(item)
		for user in range(0, currentuser):
			if user in owners: out.write('\t1')
			else: out.write('\t0')
		out.write('\n')