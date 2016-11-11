# coding: utf-8
import os
import sys
import datetime
from collections import namedtuple
from contextlib import closing

class Contest(namedtuple('Contest', ['id', 'title', 'date', 'duration_sec'])):

	def persist(self, db_connection):
		with closing(db_connection.cursor()) as cursor:
			datetime_str = self.date.strftime('%Y-%m-%d %H:%M:%S')
			cursor.execute('REPLACE INTO contests VALUES(%s, %s, %s, %s);',
			               (self.id, self.title, datetime_str, self.duration_sec))

	@staticmethod
	def loadAll(db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from contests;')
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(Contest.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def load(id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from contests WHERE contest_id = %s;', (id,))
			row = cursor.fetchone()
			if row:
				return Contest.create_from_row(row)
			else:
				return None

	@staticmethod
	def create_from_row(row):
		return Contest(row['contest_id'],
		               row['title'],
		               row['date'],
		               row['duration_sec'])


