# coding: utf-8

import unittest
import MySQLdb
import MySQLdb.cursors
from database import create_tables
from contextlib import closing
from data_structure import *

class TestDataStructure(unittest.TestCase):

	def setUp(self):
		self.db = MySQLdb.connect(host='localhost',
		                          user='test',
		                          db='test',
		                          password='test',
		                          charset='utf8',
		                          cursorclass=MySQLdb.cursors.DictCursor)
		create_tables(self.db)

	def tearDown(self):
		try:
			with closing(self.db.cursor()) as cursor:
				cursor.execute('SHOW TABLES;')
				table_names = [row['Tables_in_test'] for row in cursor.fetchall()]
				for table_name in table_names:
					cursor.execute('DROP TABLE %s' % table_name)
		finally:
			self.db.close()

	def test_Contest(self):
		c1 = Contest('icpc2016', 'ICPCアジア地区予選2016', datetime.datetime(2016, 11, 13, 9, 0, 0), 18000)
		c2 = Contest('SRM999', 'Single Round Match 999', datetime.datetime(2018, 2, 10, 21, 0, 0), 75 * 60)
		c1.persist(self.db)
		c2.persist(self.db)

		read = Contest.load('icpc2016', self.db)
		self.assertEqual('icpc2016', read.id)
		self.assertEqual('ICPCアジア地区予選2016', read.title)
		self.assertEqual(datetime.datetime(2016, 11, 13, 9, 0, 0), read.date)
		self.assertEqual(18000, read.duration_sec)

		read = Contest.load('SRM999', self.db)
		self.assertEqual('SRM999', read.id)
		self.assertEqual('Single Round Match 999', read.title)
		self.assertEqual(datetime.datetime(2018, 2, 10, 21, 0, 0), read.date)
		self.assertEqual(75 * 60, read.duration_sec)

		read = Contest.load('GCJ2016', self.db)
		self.assertEqual(None, read)

		contests = Contest.loadAll(self.db)
		self.assertEqual(2, len(contests))
		self.assertEqual({'icpc2016', 'SRM999'}, {contest.id for contest in contests})

	def test_Problem(self):
		p1 = Problem(123, 'くるくるくるりん')
		p2 = Problem(1, 'Data Center on Fire')
		p1.persist(self.db)
		p2.persist(self.db)

		read = Problem.load(123, self.db)
		self.assertEqual(123, read.id)
		self.assertEqual('くるくるくるりん', read.title)

		read = Problem.load(1, self.db)
		self.assertEqual(1, read.id)
		self.assertEqual('Data Center on Fire', read.title)

		read = Problem.load(2, self.db)
		self.assertEqual(None, read)

		problems = Problem.loadAll(self.db)
		self.assertEqual(2, len(problems))
		self.assertEqual({1, 123}, {problem.id for problem in problems})

	def test_Task(self):
		c1 = Contest('cf292', 'codeforces 292', datetime.datetime(2016, 11, 13, 9, 0, 0), 60)
		c2 = Contest('FCH 2015', 'Facebook Hacker Cup 2015', datetime.datetime(2018, 2, 10, 21, 0, 0), 100)
		c1.persist(self.db)
		c2.persist(self.db)

		p1 = Problem(2, 'くるくるくるりん')
		p2 = Problem(5, 'Data Center on Fire')
		p1.persist(self.db)
		p2.persist(self.db)

		t1 = Task(c1.id, p1.id, 'A', 'cf292_a')
		t2 = Task(c2.id, p2.id, 'XXX', 'hogehoge_path')
		t1.persist(self.db)
		t2.persist(self.db)

		read = Task.load('cf292', 2, self.db)
		self.assertEqual('cf292', read.contest_id)
		self.assertEqual(2, read.problem_id)
		self.assertEqual('A', read.symbol)
		self.assertEqual('cf292_a', read.path)

		read = Task.load('FCH 2015', 5, self.db)
		self.assertEqual('FCH 2015', read.contest_id)
		self.assertEqual(5, read.problem_id)
		self.assertEqual('XXX', read.symbol)
		self.assertEqual('hogehoge_path', read.path)

		read = Task.load('cf292', 444, self.db)
		self.assertEqual(None, read)
		read = Task.load('FCH2015', 5, self.db)
		self.assertEqual(None, read)

		tasks = Task.loadAll(self.db)
		self.assertEqual(2, len(tasks))
		self.assertEqual({2, 5}, {task.problem_id for task in tasks})

		task_of_contest = Task.of_contest('cf292', self.db)
		self.assertEqual(1, len(task_of_contest))
		self.assertEqual('cf292', task_of_contest[0].contest_id)
		self.assertEqual(2, task_of_contest[0].problem_id)
		self.assertEqual('A', task_of_contest[0].symbol)
		self.assertEqual('cf292_a', task_of_contest[0].path)

	def test_Task_get_url(self):
		task = Task('agc000', '10000', 'A', 'agc_a')
		self.assertEqual('http://agc000.contest.atcoder.jp/tasks/agc_a', task.get_url())

	def test_TaskPoint(self):
		c1 = Contest('cf292', 'codeforces 292', datetime.datetime(2016, 11, 13, 9, 0, 0), 60)
		c2 = Contest('FCH 2015', 'Facebook Hacker Cup 2015', datetime.datetime(2018, 2, 10, 21, 0, 0), 100)
		c1.persist(self.db)
		c2.persist(self.db)

		p1 = Problem(2, 'くるくるくるりん')
		p2 = Problem(5, 'Data Center on Fire')
		p1.persist(self.db)
		p2.persist(self.db)

		t1 = TaskPoint(c1.id, p1.id, 300)
		t2 = TaskPoint(c2.id, p2.id, 100)
		t1.persist(self.db)
		t2.persist(self.db)

		read = TaskPoint.load('cf292', 2, self.db)
		self.assertEqual('cf292', read.contest_id)
		self.assertEqual(2, read.problem_id)
		self.assertEqual(300, read.point)

		read = TaskPoint.load('FCH 2015', 5, self.db)
		self.assertEqual('FCH 2015', read.contest_id)
		self.assertEqual(5, read.problem_id)
		self.assertEqual(100, read.point)

		read = TaskPoint.load('cf292', 444, self.db)
		self.assertEqual(None, read)
		read = TaskPoint.load('FCH2015', 1, self.db)
		self.assertEqual(None, read)

		points = TaskPoint.loadAll(self.db)
		self.assertEqual(2, len(points))
		self.assertEqual({300, 100}, {point.point for point in points})

	def test_Result(self):
		c1 = Contest('cf292', 'codeforces 292', datetime.datetime(2016, 11, 13, 9, 0, 0), 60)
		c2 = Contest('FCH 2015', 'Facebook Hacker Cup 2015', datetime.datetime(2018, 2, 10, 21, 0, 0), 100)
		c1.persist(self.db)
		c2.persist(self.db)

		p1 = Problem(2, 'くるくるくるりん')
		p2 = Problem(5, 'Data Center on Fire')
		p1.persist(self.db)
		p2.persist(self.db)

		u1 = User('hoge')
		u2 = User('foo')
		u1.persist(self.db)
		u2.persist(self.db)

		r1 = Result(c1.id, p1.id, u1.id, 100, 1, 345, 645)
		r2 = Result(c2.id, p2.id, u2.id, 0, 2, 0, 0)
		r1.persist(self.db)
		r2.persist(self.db)

		read = Result.load('cf292', 2, 'hoge', self.db)
		self.assertEqual('cf292', read.contest_id)
		self.assertEqual(2, read.problem_id)
		self.assertEqual('hoge', read.user_id)
		self.assertEqual(100, read.score)
		self.assertEqual(1, read.failure)
		self.assertEqual(345, read.elapsed)
		self.assertEqual(645, read.penalty)

		read = Result.load('FCH 2015', 5, 'foo', self.db)
		self.assertEqual('FCH 2015', read.contest_id)
		self.assertEqual(5, read.problem_id)
		self.assertEqual('foo', read.user_id)
		self.assertEqual(0, read.score)
		self.assertEqual(2, read.failure)
		self.assertEqual(0, read.elapsed)
		self.assertEqual(0, read.penalty)

		read = Result.load('cf292', 444, 'hoge', self.db)
		self.assertEqual(None, read)
		read = Result.load('cf292', 2, 'piyo', self.db)
		self.assertEqual(None, read)
		read = Result.load('FCH 2015', 2, 'hoge', self.db)
		self.assertEqual(None, read)

		results = Result.loadAll(self.db)
		self.assertEqual(2, len(results))
		self.assertEqual({645, 0}, {result.penalty for result in results})

