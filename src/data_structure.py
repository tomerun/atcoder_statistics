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

class User(namedtuple('User', ['id'])):

	def persist(self, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('REPLACE INTO users VALUES(%s);', (self.id,))

	@staticmethod
	def loadAll(db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from users;')
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(User.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def load(id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from users WHERE user_id = %s;', (id,))
			row = cursor.fetchone()
			if row:
				return Contest.create_from_row(row)
			else:
				return None

	@staticmethod
	def create_from_row(row):
		return User(row['user_id'])


class Problem(namedtuple('Problem', ['id', 'title'])):

	def persist(self, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('REPLACE INTO problems VALUES(%s, %s);',
			               (self.id, self.title))

	@staticmethod
	def loadAll(db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from problems;')
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(Problem.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def load(id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from problems WHERE problem_id = %s;', (id,))
			row = cursor.fetchone()
			if row:
				return Problem.create_from_row(row)
			else:
				return None

	@staticmethod
	def create_from_row(row):
		return Problem(row['problem_id'], row['title'])

class Task(namedtuple('Task', ['contest_id', 'problem_id', 'symbol', 'path'])):

	def persist(self, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('REPLACE INTO tasks VALUES(%s, %s, %s, %s);',
			               (self.contest_id, self.problem_id, self.symbol, self.path))

	def get_url(self):
		return 'http://{0}.contest.atcoder.jp/tasks/{1}'.format(self.contest_id, self.path)

	@staticmethod
	def loadAll(db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from tasks;')
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(Task.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def load(contest_id, problem_id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from tasks WHERE contest_id = %s AND problem_id = %s;',
			               (contest_id, problem_id))
			row = cursor.fetchone()
			if row:
				return Task.create_from_row(row)
			else:
				return None

	@staticmethod
	def of_contest(contest_id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from tasks WHERE contest_id = %s;',
			               (contest_id,))
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(Task.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def create_from_row(row):
		return Task(row['contest_id'], row['problem_id'], row['symbol'], row['path'])

class TaskPoint(namedtuple('TaskPoint', ['contest_id', 'problem_id', 'point'])):

	def persist(self, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('REPLACE INTO task_points VALUES(%s, %s, %s);',
			               (self.contest_id, self.problem_id, self.point))

	@staticmethod
	def loadAll(db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from task_points;')
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(TaskPoint.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def load(contest_id, problem_id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from task_points WHERE contest_id = %s AND problem_id = %s;',
			               (contest_id, problem_id))
			row = cursor.fetchone()
			if row:
				return TaskPoint.create_from_row(row)
			else:
				return None

	@staticmethod
	def create_from_row(row):
		return TaskPoint(row['contest_id'], row['problem_id'], row['point'])


class Result(namedtuple('Result', ['contest_id', 'problem_id', 'user_id', 'score', 'failure', 'elapsed', 'penalty'])):

	def persist(self, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('REPLACE INTO results VALUES(%s, %s, %s, %s, %s, %s, %s);',
			               (self.contest_id, self.problem_id, self.user_id, self.score, self.failure, self.elapsed, self.penalty))

	@staticmethod
	def loadAll(db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from results;')
			ret = []
			row = cursor.fetchone()
			while row:
				ret.append(Result.create_from_row(row))
				row = cursor.fetchone()
			return ret

	@staticmethod
	def load(contest_id, problem_id, user_id, db_connection):
		with closing(db_connection.cursor()) as cursor:
			cursor.execute('SELECT * from results WHERE contest_id = %s AND problem_id = %s AND user_id = %s;',
			               (contest_id, problem_id, user_id))
			row = cursor.fetchone()
			if row:
				return Result.create_from_row(row)
			else:
				return None

	@staticmethod
	def create_from_row(row):
		return Result(row['contest_id'], row['problem_id'], row['user_id'],
		              row['score'], row['failure'], row['elapsed'], row['penalty'])


