# coding: utf-8

import database
from data_structure import *

new_contest_list = ['agc001','agc002','agc003','agc004','agc005','agc006','agc007',
                    'arc058','arc059','arc060','arc061','arc062','arc063',
                    'abc042','abc043','abc044','abc045','abc046','abc047',
                    'tenka1-2016-quala','tenka1-2016-qualb','tenka1-2016-final-open',
                    'code-festival-2016-quala','code-festival-2016-qualb','code-festival-2016-qualc', 'cf16-final', 'cf16-final-open'
                    'ddcc2016-qual']

old_contest_list = ['arc001','arc002','arc003','arc004','arc005','arc006','arc007','arc008','arc009','arc010','arc011','arc012','arc013','arc014','arc015','arc016','arc017','arc018','arc019','arc020','arc021','arc022','arc023','arc024','arc025','arc026','arc027','arc028','arc029','arc030','arc031','arc032','arc033','arc034','arc035','arc036','arc037','arc038','arc039','arc040','arc041','arc042','arc043','arc044','arc045','arc046','arc047','arc048','arc049','arc050','arc051','arc052','arc053','arc054','arc055','arc056','arc057',
                    'abc001','abc002','abc003','abc004','abc005','abc006','abc007','abc008','abc009','abc010','abc011','abc012','abc013','abc014','abc015','abc016','abc017','abc018','abc019','abc020','abc021','abc022','abc023','abc024','abc025','abc026','abc027','abc028','abc029','abc030','abc031','abc032','abc033','abc034','abc035','abc036','abc037','abc038','abc039','abc040','abc041']


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
	sql =  "SELECT problem_id, symbol FROM tasks"
	sql += "  WHERE (contest_id = '{0}'".format(contest_ids[0])
	for contest_id in contest_ids[1:-1]:
		sql += "      OR contest_id = '{0}'".format(contest_id)
	sql += "  ) ORDER BY problem_id;"
	db = database.get_connection()
	with closing(db) as con:
		with closing(con.cursor()) as cursor:
			cursor.execute(sql)
			return cursor.fetchall()

def get_task_point_list(contest_ids):
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

def get_results(contest_ids):
	sql =  "SELECT problem_id, user_id, score FROM results"
	sql += "  WHERE (contest_id = '{0}'".format(contest_ids[0])
	for contest_id in contest_ids[1:-1]:
		sql += "      OR contest_id = '{0}'".format(contest_id)
	sql += "  );"
	db = database.get_connection()
	with closing(db) as con:
		with closing(con.cursor()) as cursor:
			cursor.execute(sql)
			return cursor.fetchall()

def output_csv(train):
	user_list = get_user_list()
	user_idx = {user_list[i] : i for i in range(len(user_list))}
	user_results = {user_id : {} for user_id in user_list}

	if train:
		contest_list = new_contest_list
		task_points = {tp['problem_id'] : tp['point'] for tp in get_task_point_list(contest_list)}
	else:
		contest_list = old_contest_list
		# assuming points of all problems in old contests are 100
		task_points = {task['problem_id'] : 10000 for task in get_task_list(contest_list)}

	for result in get_results(contest_list):
		uid = result['user_id']
		if uid not in user_list:
			continue
		pid = result['problem_id']
		success = result['score'] >= task_points[pid]   # care for  'full score is 101 pts' case
		user_results[uid][pid] = success
	for contest_id in contest_list:
		tasks = sorted(get_task_list([contest_id]), key = lambda x : x['symbol'])
		task_prob_ids = [x['problem_id'] for x in tasks]
		for user_id, results in user_results.items():
			results = user_results[user_id]
			tried = False
			for pid in task_prob_ids:
				if pid in results:
					tried = True
				elif tried:
					results[pid] = False   # tried and no submit

	# print header
	print('source', end = '')
	for user in user_list:
		print(',{0}_T,{0}_F'.format(user), end = '')
	if train:
		print(',point')
	else:
		print()

	# print body
	for pid, point in task_points.items():
		print(pid, end='')
		for uid in user_list:
			results = user_results[uid]
			if pid not in results:
				print(',0,0', end='')
			elif results[pid]:
				print(',1,0', end='')
			else:
				print(',0,1', end='')
		if train:
			print(',' + str(point))
		else:
			print()


def main():
	output_csv(train = False)

if __name__ == '__main__':
	main()

