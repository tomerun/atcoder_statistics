# coding: utf-8

import itertools
from sklearn.linear_model import RidgeCV
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import pandas as pd
import database
from data_structure import *

def normalize(value):
	return np.log(value / 10000.0)

def denormalize(value):
	return np.power(np.e, value) * 10000.0


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

	expect = normalize(train_data['point'])
	train_data = train_data[effective_cols]
	test_data = test_data[effective_cols]

	mask = np.random.rand(len(train_data)) <= 1.0
	train_selected = train_data[mask]
	train_expect = expect[mask]
	verify_selected = train_data[~mask]
	verify_expect = expect[~mask]	

	# regressor = RidgeCV(alphas = (0.1, 0.3, 0.5, 1, 3, 5, 10, 20), cv = 3)
	# regressor.fit(train_selected, train_expect)
	# print(list(regressor.coef_))
	# print(regressor.intercept_)
	# print(regressor.alpha_)

	# regressor = SVR(C=5, epsilon=0.1)
	# regressor.fit(train_selected, train_expect)

	regressor = RandomForestRegressor(n_estimators=1000)
	regressor.fit(train_selected, train_expect)
	print(regressor.estimators_)
	print(regressor.feature_importances_)
	print(regressor.n_features_)
	print(regressor.n_outputs_)

	train_result = regressor.predict(train_selected)
	for e, r in zip(denormalize(train_expect), denormalize(train_result)):
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

	test_result = denormalize(regressor.predict(test_data))
	result = [(pid_to_task[pid].contest_id, pid_to_task[pid].symbol, pid, r) for pid, r in zip(test_pid, test_result)]
	for res in sorted(result):
		print(res[2], res[0], res[1], res[3])

	# for pid, r in zip(test_pid, test_result):
	# 	task = pid_to_task[pid]
	# 	print(pid, task.contest_id, task.symbol, r)
	print()

if __name__ == '__main__':
	main()

