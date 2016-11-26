# coding: utf-8
import os
import sys
import json
import re
import datetime
import time

import requests
import lxml.html
import lxml
import cssselect

import database
from data_structure import *

def str_to_datetime(str):
	match = re.match(r'(\d{4})/(\d{2})/(\d{2})\s*(\d{2}):(\d{2})', str)
	if match:
		return datetime.datetime(year   = int(match.group(1)),
		                         month  = int(match.group(2)),
		                         day    = int(match.group(3)),
		                         hour   = int(match.group(4)),
		                         minute = int(match.group(5)))
	else:
		raise RuntimeError('unknown date')


def extract_contest_info_from_list(row):
	cells = row.findall('td')
	start_at = str_to_datetime(cells[0].text_content())

	link = cells[1].find('a')
	url = link.get('href')
	m = re.search(r'https://([^.]+)\.contest\.atcoder\.jp', url)
	id = m.group(1)
	title = link.text
	duration_str = cells[2].text_content()
	duration_match = re.match(r'(\d\d):(\d\d)', duration_str)
	if duration_match:
		duration_sec = int(duration_match.group(1)) * 3600 + int(duration_match.group(2)) * 60
	else:
		print('unknown duration:' + id + " " + title)
		duration_sec = 100000000 # some large value

	return Contest(id, title, start_at, duration_sec)


def crawl_contests_list_page(url):
	page = requests.get('https://atcoder.jp' + url + '&lang=ja')
	root = lxml.html.fromstring(page.text)
	contest_list = root.cssselect('#main-div div.row > div:nth-of-type(2) table > tbody > tr')
	return [extract_contest_info_from_list(contest_row) for contest_row in contest_list]


def crawl_contests_list():
	top = requests.get('https://atcoder.jp/contest/archive?lang=ja')
	root = lxml.html.fromstring(top.text)
	page_list = root.cssselect('#main-div ul.pagination-sm > li')
	contests = []
	for page in page_list:
		link = page.cssselect('a')[0]
		contests = contests + crawl_contests_list_page(link.get('href'))

	db = database.get_connection()
	db.autocommit(True)
	with closing(db) as con:
		for contest in contests:
			contest.persist(con)

def crawl_contest_info(contest_id):
	tasks_page = requests.get(r'https://{0}.contest.atcoder.jp/?lang=ja'.format(contest_id))
	root = lxml.html.fromstring(tasks_page.text)
	title = root.cssselect('div#outer-inner div.insert-participant-box h1')[0].text_content()
	times = root.cssselect('div.navbar-fixed-top a.brand span.bland-small time')
	start_at = str_to_datetime(times[0].text_content())
	end_at = str_to_datetime(times[1].text_content())
	diff = end_at - start_at
	contest = Contest(contest_id, title, start_at, diff.total_seconds())
	print(contest)
	db = database.get_connection()
	db.autocommit(True)
	with closing(db) as con:
		contest.persist(con)


def crawl_task(contest_id, row):
	cells = row.cssselect('td')
	symbol = cells[0].text_content()
	title = cells[1].text_content()

	link_url = cells[1].find('a').get('href')
	link_match = re.match(r'/tasks/(.+)$', link_url)
	if link_match:
		path = link_match.group(1)
	else:
		raise RuntimeError('no task link')

	submit_url = cells[4].find('a').get('href')
	submit_match = re.match(r'/submit\?task_id=(\d+)$', submit_url)
	if submit_match:
		problem_id = int(submit_match.group(1))
	else:
		raise RuntimeError('no submit link')

	problem = Problem(problem_id, title)
	task = Task(contest_id, problem_id, symbol, path)

	print(problem)
	print(task)
	db = database.get_connection()
	db.autocommit(True)
	with closing(db) as con:
		problem.persist(con)
		task.persist(con)


def crawl_tasks(contest_id):
	tasks_page = requests.get(r'https://{0}.contest.atcoder.jp/assignments?lang=ja'.format(contest_id))
	root = lxml.html.fromstring(tasks_page.text)
	task_list = root.cssselect('div#outer-inner table tbody tr')
	for task_elem in task_list:
		try:
			crawl_task(contest_id, task_elem)
		except Exception as e:
			print('crawling tasks failed:' + str(e) + ' : ' + contest_id)


def crawl_all_contest_tasks():
	db = database.get_connection()
	with closing(db) as con:
		contests = Contest.loadAll(db)

	for contest in contests:
		time.sleep(1)
		crawl_tasks(contest.id)


def crawl_results(contest_id):
	stands_page = requests.get('https://{0}.contest.atcoder.jp/standings'.format(contest_id))
	root = lxml.html.fromstring(stands_page.text)
	script = root.cssselect('div#pagination-standings + script')[0]
	data_match = re.search(r'ATCODER\.standings\s*=\s*({.*});\s*$', script.text_content(), re.MULTILINE | re.DOTALL)
	if data_match is None:
		raise RuntimeError('no data:' + contest_id)

	json_str = data_match.group(1)
	for key in ['pagination', 'data', 'hidden_name', 'show_flag']:
		json_str = re.sub(r'^\s*' + key + r':', '"{0}":'.format(key), json_str, flags = re.MULTILINE)
	data_json = json.loads(json_str)['data']

	db = database.get_connection()
	try:
		for user_data in data_json:
			user_id = user_data['user_screen_name']
			user = User(user_id)
			user.persist(db)
			for task in user_data['tasks']:
				if 'failure' not in task:
					continue
				problem_id = task['task_id']
				score = task['score']
				failure = task['failure']
				penalty = task['penalty']
				elapsed = task['elapsed_time']
				result = Result(contest_id, problem_id, user_id, score, failure, elapsed, penalty)
				result.persist(db)
	except Exception as e:
		db.rollback()
		raise e
	else:
		db.commit()
	finally:
		db.close()


def crawl_all_contest_results():
	db = database.get_connection()
	with closing(db) as con:
		contests = Contest.loadAll(db)

	for contest in contests:
		time.sleep(1)
		print(contest.id)
		try:
			crawl_results(contest.id)
		except Exception as e:
			print('crawling tasks failed:' + str(e) + ' : ' + contest.id)


def crawl_task_point(task):
	task_page = requests.get(task.get_url())
	root = lxml.html.fromstring(task_page.text)
	statement = root.cssselect('#task-statement')[0].text_content()
	match = re.search(r'配点\s*:\s*(\d+)', statement)
	if match:
		point = int(match.group(1))
		task_point = TaskPoint(task.contest_id, task.problem_id, point * 100) # normalize point
		db = database.get_connection()
		db.autocommit(True)
		with closing(db) as con:
			task_point.persist(db)
		print(task.contest_id + '-' + str(task.symbol) + ' has ' + str(point) + ' points.')
	else:
		print(task.contest_id + '-' + str(task.symbol) + ' has unknown points.')


def crawl_task_point_of_contest(contest_id):
	db = database.get_connection()
	with closing(db) as con:
		tasks = Task.of_contest(contest_id, db)
	for task in tasks:
		crawl_task_point(task)
		time.sleep(0.5)


def crawl_contest_by_id(contest_id):
	crawl_contest_info(contest_id)
	crawl_tasks(contest_id)
	crawl_task_point_of_contest(contest_id)
	crawl_results(contest_id)


def main():
	contest_list = ['cf16-final','cf16-final-open']
	for contest in contest_list:
		crawl_contest_by_id(contest)


if __name__ == '__main__':
	main()

