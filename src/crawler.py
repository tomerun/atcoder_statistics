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


def extract_contest_info(row):
	cells = row.findall('td')
	start_at_str = cells[0].text_content()
	start_at_match = re.match('(\d{4})/(\d{2})/(\d{2})\s*(\d{2}):(\d{2})', start_at_str)
	if start_at_match:
		start_at = datetime.datetime(year   = int(start_at_match.group(1)),
		                             month  = int(start_at_match.group(2)),
		                             day    = int(start_at_match.group(3)),
		                             hour   = int(start_at_match.group(4)),
		                             minute = int(start_at_match.group(5)))
	else:
		raise RuntimeError('unknown start date')

	link = cells[1].find('a')
	url = link.get('href')
	m = re.search('https://([^.]+)\.contest\.atcoder\.jp', url)
	id = m.group(1)
	title = link.text
	duration_str = cells[2].text_content()
	duration_match = re.match('(\d\d):(\d\d)', duration_str)
	if duration_match:
		duration_sec = int(duration_match.group(1)) * 3600 + int(duration_match.group(2)) * 60
	else:
		print('unknown duration:' + id + " " + title)
		duration_sec = 100000000

	return Contest(id, title, start_at, duration_sec)


def crawl_contests_page(url):
	page = requests.get('https://atcoder.jp' + url + '&lang=ja')
	root = lxml.html.fromstring(page.text)
	contest_list = root.cssselect('#main-div div.row > div:nth-of-type(2) table > tbody > tr')
	return [extract_contest_info(contest_row) for contest_row in contest_list]


def crawl_contests():
	top = requests.get('https://atcoder.jp/contest/archive?lang=ja')
	root = lxml.html.fromstring(top.text)
	page_list = root.cssselect('#main-div ul.pagination-sm > li')
	contests = []
	for page in page_list:
		link = page.cssselect('a')[0]
		contests = contests + crawl_contests_page(link.get('href'))

	db = database.get_connection()
	db.autocommit(True)
	with closing(db) as con:
		for contest in contests:
			contest.persist(con)


def crawl_task(contest_id, row):
	cells = row.cssselect('td')
	symbol = cells[0].text_content()
	title = cells[1].text_content()

	link_url = cells[1].find('a').get('href')
	link_match = re.match('/tasks/(.+)$', link_url)
	if link_match:
		path = link_match.group(1)
	else:
		raise RuntimeError('no task link')

	submit_url = cells[4].find('a').get('href')
	submit_match = re.match('/submit\?task_id=(\d+)$', submit_url)
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
	tasks_page = requests.get('https://{0}.contest.atcoder.jp/assignments?lang=ja'.format(contest_id))
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
	contests = contests[133:-1]

	for contest in contests:
		time.sleep(1)
		print(contest.id)
		try:
			crawl_results(contest.id)
		except Exception as e:
			print('crawling tasks failed:' + str(e) + ' : ' + contest.id)


def main():
	crawl_all_contest_results()

if __name__ == '__main__':
	main()

