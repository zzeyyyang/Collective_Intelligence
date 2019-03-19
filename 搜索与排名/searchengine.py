# -*- coding: utf-8 -*- 
import urllib2
from BeautifulSoup import *
from urlparse import urljoin
from sqlite3 import dbapi2 as sqlite

import nn
mynet = nn.searchnet('nn.db')

# 忽略的单词
ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])

class crawler:
	def __init__(self, dbname):
		self.con = sqlite.connect(dbname)

	def __del__(self):
		self.con.close()

	def dbcommit(self):
		self.con.commit()

	# 辅助函数，用于获取条目的id，并且如果条目不存在，就将其加入数据库中
	def getentryid(self, table, field, value, createnew=True):
		cur = self.con.execute(
			"select rowid from %s where %s = '%s'" % (table, field, value))
		res = cur.fetchone()
		# 条目不存在，则在数据库中新建一条记录
		if res == None:
			cur = self.con.execute(
				"insert into %s (%s) values ('%s')" % (table, field, value))
			return cur.lastrowid
		else:
			return res[0]

	# 为每个网页建立索引
	def addtoindex(self, url, soup):
		if self.isindexed(url): return
		print 'Indexing ' + url

		# 获取每个单词
		text = self.gettextonly(soup)
		words = self.seperatewords(text)

		# 得到url的id
		urlid = self.getentryid('urllist', 'url', url)

		# 将每个单词与该url关联
		for i in range(len(words)):
			word = words[i]
			if word in ignorewords: continue
			wordid = self.getentryid('wordlist', 'word', word)
			self.con.execute("insert into wordlocation(urlid, wordid, location) \
				values (%d, %d, %d)" % (urlid, wordid, i))

	# 从一个HTML网页中提取文字（不带标签）
	def gettextonly(self, soup):
		v = soup.string
		if v == None:
			c = soup.contents
			resulttext = ''
			for t in c:
				subtext = self.gettextonly(t)
				resulttext += subtext + '\n'
			return resulttext
		else:
			return v.strip()

	# 根据任何非空白字符进行分词
	def seperatewords(self, text):
		splitter = re.compile('\\W*')
		return [s.lower() for s in splitter.split(text) if s != '']

	# 如果url已经建过索引，则返回true
	def isindexed(self, url):
		u = self.con.execute \
		    ("select rowid from urllist where url = '%s'" % url).fetchone()
		if u != None:
			# 检查它是否已经被检索过了
			v = self.con.execute(
				'select * from wordlocation where urlid = %d' % u[0]).fetchone()
			if v != None: return True		
		return False

	# 添加一个关联两个网页的链接
	def addlinkref(self, urlFrom, urlTo, linkText):
		words = self.seperatewords(linkText)
		fromid = self.getentryid('urllist', 'url', urlFrom)
		toid = self.getentryid('urllist', 'url', urlTo)
		if fromid == toid: return
		cur = self.con.execute("insert into link(fromid, toid) values (%d, %d)" % (fromid, toid))
		linkid = cur.lastrowid
		for word in words:
			if word in ignorewords: continue
			wordid = self.getentryid('wordlist', 'word', word)
			self.con.execute("insert into linkwords(linkid, wordid) values (%d,%d)" % (linkid, wordid))

	# 从一小组网页开始进行广度优先搜索，直至某一给定深度，
	# 期间为网页建立索引
	def crawl(self, pages, depth=2):
		for i in range(depth):
			newpages = set()
			for page in pages:
				try:
					c = urllib2.urlopen(page)
				except:
					print "Could not open %s" % page
					continue
				soup = BeautifulSoup(c.read())
				self.addtoindex(page, soup)

				links = soup('a')
				for link in links:
					if ('href' in dict(link.attrs)):
						url = urljoin(page, link['href'])
						if url.find("'") != -1: continue
						url = url.split('#')[0] # 去掉位置部分
						if url[0:4] == 'http' and not self.isindexed(url):
							newpages.add(url)
						linkText = self.gettextonly(link)
						self.addlinkref(page, url, linkText)

				self.dbcommit()
			pages = newpages

	# 创建数据库表
	def createindextables(self):
		self.con.execute('create table urllist(url)')
		self.con.execute('create table wordlist(word)')
		self.con.execute('create table wordlocation(urlid, wordid, location)')
		self.con.execute('create table link(fromid integer, toid integer)')
		self.con.execute('create table linkwords(wordid, linkid)')
		self.con.execute('create index wordidx on wordlist(word)')
		self.con.execute('create index urlidx on urllist(url)')
		self.con.execute('create index wordurlidx on wordlocation(wordid)')
		self.con.execute('create index urltoidx on link(toid)')
		self.con.execute('create index urlfromid on link(fromid)')
		self.dbcommit()

	# PageRank算法
	def calculatepagerank(self, iterations=20):
		# 清除当前的PageRank表
		self.con.execute('drop table if exists pagerank')
		self.con.execute('create table pagerank(urlid primary key, score)')

		# 初始化每个url，令其PageRank值为1
		self.con.execute('insert into pagerank select rowid, 1.0 from urllist')
		self.dbcommit()

		for i in range(iterations):
			print "iteration %d" % (i)
			for (urlid,) in self.con.execute('select rowid from urllist'):
				pr = 0.15

				# 循环遍历指向当前网页的所有其他网页
				for (linker,) in self.con.execute(
				'select distinct fromid from link where toid = %d' % urlid):
					# 得到链接源对应网页的PageRank值
					linkingpr = self.con.execute(
					'select score from pagerank where urlid = %d' % linker).fetchone()[0]

					# 根据链接源，求得总的链接数
					linkingcount = self.con.execute(
					'select count(*) from link where fromid = %d' % linker).fetchone()[0]
					pr += 0.85 * (linkingpr / linkingcount)
				self.con.execute(
				'update pagerank set score = %f where urlid = %d' % (pr, urlid))
			self.dbcommit()


class searcher:
	def __init__(self, dbname):
		self.con = sqlite.connect(dbname)

	def __del__(self):
		self.con.close()

	def getmatchrows(self, q):
		# 构造查询的字符串
		fieldlist = 'w0.urlid'
		tablelist = ''
		clauselist = ''
		wordids = []

		words = q.split(' ')
		tablenumber = 0

		for word in words:
			# 获取单词的ID
			wordrow = self.con.execute(
				"select rowid from wordlist where word = '%s'" % word).fetchone()
			if wordrow != None:
				wordid = wordrow[0]
				wordids.append(wordid)
				if tablenumber>0:
					tablelist += ','
					clauselist += ' and '
					clauselist += 'w%d.urlid = w%d.urlid and ' % (tablenumber-1, tablenumber)
				fieldlist += ',w%d.location' % tablenumber
				tablelist += 'wordlocation w%d' % tablenumber
				clauselist += 'w%d.wordid = %d' % (tablenumber, wordid)
				tablenumber += 1

		# 根据各个组分，建立查询
		fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
		cur = self.con.execute(fullquery)
		rows = [row for row in cur]

		return rows, wordids

	def getscoredlist(self, rows, wordids):
		totalscores = dict([(row[0], 0) for row in rows])

		# 放置评价函数
		weights = [(1.0, self.locationscore(rows)),
				   (1.0, self.frequencyscore(rows)),
				   (1.0, self.pagerankscore(rows)),
				   (1.0, self.linktextscore(rows, wordids))]

		for (weight, scores) in weights:
			for url in totalscores:
				totalscores[url] += weight*scores[url]

		return totalscores

	def geturlname(self, id):
		return self.con.execute(
			"select url from urllist where rowid = %d" % id).fetchone()[0]

	def query(self, q):
		rows, wordids = self.getmatchrows(q)
		scores = self.getscoredlist(rows, wordids)
		rankedscores = sorted([(score, url) for (url, score) in scores.items()], reverse = 1)
		for (score, urlid) in rankedscores[0:10]:
			print '%f\t%s' % (score, self.geturlname(urlid))
		return wordids, [r[1] for r in rankedscores[0:10]]

	def normalizescores(self, scores, smallIsBetter=0):
		vsmall = 0.00001 # 避免被0整除
		if smallIsBetter:
			minscore = min(scores.values())
			return dict([(u, float(minscore) / max(vsmall, l)) for (u,l) \
				in scores.items()])
		else:
			maxscore = max(scores.values())
			if maxscore == 0: maxscore = vsmall
			return dict([(u, float(c) / maxscore) for (u, c) in scores.items()])

    # 单词频度
	def frequencyscore(self, rows):
		counts = dict([(row[0], 0) for row in rows])
		for row in rows: counts[row[0]] += 1
		return self.normalizescores(counts)

	# 文档位置
	def locationscore(self, rows):
		locations = dict([(row[0], 1000000) for row in rows])
		for row in rows:
			loc = sum(row[1:])
			if loc < locations[row[0]]: locations[row[0]] = loc

		return self.normalizescores(locations, smallIsBetter = 1)

	# 单词距离
	def distancescore(self, rows):
		# 如果仅有一个单词，则得分都一样
		if len(rows[0]) <= 2: return dict([(row[0], 1.0) for row in rows])

		# 初始化字典，并填入一个很大的数
		mindistance = dict([(row[0], 1000000) for row in rows])

		for row in rows:
			dist = sum([abs(row[i] - row[i-1]) for i in range(2, len(row))])
			if dist < mindistance[row[0]]: mindistance[row[0]] = dist

		return self.normalizescores(mindistance, smallIsBetter = 1)

	# 利用外部回指链接简单计数
	def inboundlinkscore(self, rows):
		uniqueurls = set([row[0] for row in rows])
		inboundcount = dict([(u, self.con.execute( \
			'select count(*) from link where toid = %d' % u).fetchone()[0]) \
			for u in uniqueurls])
		return self.normalizescores(inboundcount)
	
	# PageRank值
	def pagerankscore(self, rows):
		pageranks = dict([(row[0], self.con.execute('select score from pagerank where \
			urlid = %d' % row[0]).fetchone()[0]) for row in rows])
		maxrank = max(pageranks.values())
		normalizedscores = dict([(u, float(l) / maxrank) for (u, l) in pageranks.items()])
		return normalizedscores

	# 利用链接文本
	def linktextscore(self, rows, wordids):
		linkscores = dict([(row[0], 0) for row in rows])
		for wordid in wordids:
			cur = self.con.execute('select link.fromid, link.toid from linkwords, link where \
				wordid = %d and linkwords.linkid = link.rowid' % wordid)
			for (fromid, toid) in cur:
				if toid in linkscores:
					pr = self.con.execute('select score from pagerank where urlid = %d' % fromid).fetchone()[0]
					linkscores[toid] += pr
		vsmall = 0.00001 # 避免被0整除
		maxscore = max(linkscores.values())
		if maxscore == 0: maxscore = vsmall
		normalizedscores = dict([(u, float(l) / maxscore) for (u, l) in linkscores.items()])
		return normalizedscores

	# 神经网络
	def nnscore(self, rows, wordids):
		# 获得一个由唯一的URL ID构成的有序列表
		urlids = [urlid for urlid in set([row[0] for row in rows])]
		nnres = mynet.getresult(wordids, urlids)
		scores = dict([(urlids[i], nnres[i]) for i in range(len(urlids))])
		return self.normalizedscores(scores)