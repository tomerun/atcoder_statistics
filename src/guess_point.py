# coding: utf-8

import database
from data_structure import *

new_contest_list = ['agc001','agc002','agc003','agc004','agc005','agc006','agc007',
                    'arc058','arc059','arc060','arc061','arc062','arc063',
                    'abc042','abc043','abc044','abc045','abc046','abc047',
                    'tekna1-2016-quala','tekna1-2016-qualb','tenka1-2016-final-open',
                    'code-festival-2016-quala','code-festival-2016-qualb','code-festival-2016-qualc',
                    'ddcc2016-qual']


def get_user_list():
	sql = "SELECT DISTINCT user_id FROM results WHERE contest_id = '{0}'".format(new_contest_list[0])
	for contest_id in new_contest_list[1:-1]:
		sql += " OR contest_id = '{0}'".format(contest_id)
	sql += 'ORDER BY user_id;'
	db = database.get_connection()
	with closing(db) as con:
		with closing(con.cursor()) as cursor:
			cursor.execute(sql)
			return [e['user_id'] for e in cursor.fetchall()]

def get_task_list(contest_ids):
	sql =  "SELECT tasks.problem_id, symbol, point FROM tasks, task_points"
	sql += "  WHERE tasks.contest_id = task_points.contest_id AND tasks.problem_id = task_points.problem_id"
	sql += "        AND (tasks.contest_id = '{0}'".format(contest_ids[0])
	for contest_id in contest_ids[1:-1]:
		sql += "      OR tasks.contest_id = '{0}'".format(contest_id)
	sql += "  ) ORDER BY tasks.problem_id;"
	db = database.get_connection()
	with closing(db) as con:
		with closing(con.cursor()) as cursor:
			cursor.execute(sql)
			return cursor.fetchall()

def get_result_list(problem_id):
	sql = "SELECT user_id, score, failure FROM results WHERE problem_id = '{0}'".format(problem_id)
	sql += '  ORDER BY user_id;'
	db = database.get_connection()
	with closing(db) as con:
		with closing(con.cursor()) as cursor:
			cursor.execute(sql)
			return cursor.fetchall()

def output_train_csv():
	user_list = get_user_list()
	user_idx = {user_list[i] : i for i in range(len(user_list))}
	print('source', end = '')
	for user in user_list:
		print(',{0}_T,{0}_F'.format(user), end = '')
	print(',point')
	task_list = get_task_list(new_contest_list)
	for task in task_list:
		print(task['problem_id'], end = '')
		binary_list = [False] * (len(user_list) * 2)
		results = get_result_list(task['problem_id'])
		for result in results:
			user_id = result['user_id']
			if user_id in user_idx:
				idx = user_idx[user_id] * 2
				if result['score'] != task['point']:
					idx += 1
				binary_list[idx] = True
		for b in binary_list:
			print(',', 1 if b else 0, sep = '', end = '')
		print(',' + str(task['point']))


def main():
	output_train_csv()

if __name__ == '__main__':
	main()

