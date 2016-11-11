# coding: utf-8

import unittest
import MySQLdb
import MySQLdb.cursors
from  setup_database import create_tables
from contextlib import closing
from data_structure import *

class TestDataStructure(unittest.TestCase):

	def setUp(self):
		self.db = MySQLdb.connect(host='localhost',
		                          user='test',
		                          db='test',
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

