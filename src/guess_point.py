# coding: utf-8

import itertools
from sklearn.linear_model import RidgeCV
import numpy as np
import pandas as pd
import database
from data_structure import *


def main():
	train_data = pd.read_csv('train.csv').drop('source', 1)
	test_data = pd.read_csv('test.csv')
	test_pid = test_data['source']
	test_data = test_data.drop('source', 1)

	# extract users having many features in test_data
	col_sum = test_data.sum(0)
	user_count = col_sum.rolling(2).sum()[1:-1:2].astype(int)
	effective_users = [l[0:-2] for l, v in user_count.iteritems() if v >= 20]
	effective_cols = [name for user in effective_users for name in [user + '_T', user + '_F']]
	print('test_user_count', len(effective_users))

	expect = train_data['point']
	train_data = train_data[effective_cols]
	test_data = test_data[effective_cols]

	mask = np.random.rand(len(train_data)) <= 1.0
	train_selected = train_data[mask]
	train_expect = expect[mask]
	verify_selected = train_data[~mask]
	verify_expect = expect[~mask]	

	regressor = RidgeCV(alphas = (1, 3, 5, 10, 20, 30, 50, 100), cv = 3)
	regressor.fit(train_selected, train_expect)
	# print(regressor.cv_values_)
	print(list(regressor.coef_))
	print(regressor.intercept_)
	print(regressor.alpha_)

	train_result = regressor.predict(train_selected)
	for e, r in zip(train_expect, train_result):
		print(e, r)
	print()

	# verify_result = regressor.predict(verify_selected)
	# for e, r in zip(verify_expect, verify_result):
	# 	print(e, r)
	# print()


	db = database.get_connection()
	with closing(db) as con:
		tasks = Task.loadAll(con)
	pid_to_task = {task.problem_id : task for task in tasks}

	test_result = regressor.predict(test_data)
	for pid, r in zip(test_pid, test_result):
		task = pid_to_task[pid]
		print(pid, task.contest_id, task.symbol, r)
	print()

if __name__ == '__main__':
	main()

