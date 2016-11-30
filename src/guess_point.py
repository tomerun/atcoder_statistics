# coding: utf-8

import itertools
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR
import numpy as np
import pandas as pd
import database
from data_structure import *

def normalize(value):
	# return value / 10000.0
	return np.log(value / 10000.0)

def denormalize(value):
	# return value * 10000.0
	return np.power(np.e, value) * 10000.0


def guess(train_data, test_data):
	# extract users having many features in test_data
	col_sum = test_data.sum(0)
	user_count = col_sum.rolling(2).sum()[1:-1:2].astype(int)
	effective_users = [l[0:-2] for l, v in user_count.iteritems() if v >= 100]
	effective_cols = [name for user in effective_users for name in [user + '_T', user + '_F']]
	print('test_user_count', len(effective_users))

	expect = normalize(train_data['point'])
	train_data = train_data[effective_cols]
	test_data = test_data[effective_cols]

	mask = np.random.rand(len(train_data)) >= 1.0
	train_selected = train_data[~mask]
	train_expect = expect[~mask]
	verify_selected = train_data[mask]
	verify_expect = expect[mask]

	# tuned_parameters = [{'alphas': [[0.1], [0.3], [1], [3], [10], [30], [100], [300]],
	#                      },
	#                     ]
	# regressor = GridSearchCV(RidgeCV(), tuned_parameters, cv=4)

	tuned_parameters = [{'kernel': ['rbf'],
	                     'gamma': [1e-2, 3e-2, 1e-3, 3e-3, 1e-4],
	                     'C': [1, 3, 10, 30, 100, 300],
	                     'epsilon': [0, 0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03, 0.1],
	                     },
	                    ]
	regressor = GridSearchCV(SVR(), tuned_parameters, cv=4)

	# tuned_parameters = [{'n_estimators': [27, 81, 243],
	#                      'max_features': ['auto', 'sqrt', 'log2'],
	#                      'min_samples_split': [2, 3, 4],
	#                      # 'max_leaf_nodes': [None, 2, 4, 8, 16, 32],
	#                      },
	#                     ]
	# regressor = GridSearchCV(RandomForestRegressor(), tuned_parameters, cv=4)

	regressor.fit(train_selected, train_expect)
	print(regressor.best_params_)
	print(regressor.best_score_)

	# train_result = regressor.predict(train_selected)
	# for e, r in zip(denormalize(train_expect), denormalize(train_result)):
	# 	print(int(round(e / 100)), int(round(r / 100)))
	# print()
	# 
	# verify_result = regressor.predict(verify_selected)
	# for e, r in zip(denormalize(verify_expect), denormalize(verify_result)):
	# 	print(int(round(e / 100)), int(round(r / 100)))
	# print()

	return denormalize(regressor.predict(test_data))


def main():
	train_data = pd.read_csv('train.csv')
	train_pid = train_data['source']
	train_data = train_data.drop('source', 1)

	test_data = pd.read_csv('test.csv')
	test_pid = test_data['source']
	test_data = test_data.drop('source', 1)

	test_result = guess(train_data, test_data)

	db = database.get_connection()
	with closing(db) as con:
		tasks = Task.loadAll(con)
	pid_to_task = {task.problem_id : task for task in tasks if task.contest_id.startswith('arc') or task.contest_id.startswith('abc')}

	result = [(pid_to_task[pid].contest_id, pid_to_task[pid].symbol, pid, r) for pid, r in zip(test_pid, test_result)]
	for res in sorted(result):
		print(res[2], res[0], res[1], int(round(res[3] / 100)))
	print()



if __name__ == '__main__':
	main()

