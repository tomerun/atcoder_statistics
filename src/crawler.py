# coding: utf-8
import os
import sys
import json
import re
from datetime import datetime as dt, timedelta
import time
import logging

import requests
import lxml.html
import lxml
import cssselect

import database
from data_structure import *

def str_to_datetime(str):
	match = re.match(r'(\d{4})/(\d{2})/(\d{2})\s*(\d{2}):(\d{2})', str)
	if match:
		return dt(year   = int(match.group(1)),
		          month  = int(match.group(2)),
		          day    = int(match.group(3)),
		          hour   = int(match.group(4)),
		          minute = int(match.group(5)))
	else:
		raise RuntimeError('unknown date')


class Crawler:

	def __init__(self, interval = 0.5):
		self.logger = logging.getLogger('crawler')
		self.interval_secs = interval
		self.prev_request_time = dt.now() - timedelta(seconds = interval * 2)

	def __enter__(self):
		self.session = requests.Session()
		self.session.headers.update({'User-Agent': 'AtCoder Statistics Crawler', 'From': 'tomerunmail@gmail.com'})
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.session:
			self.session.close()

	def get(self, url):
		wait_until = self.prev_request_time + timedelta(seconds = self.interval_secs)
		wait_secs = (wait_until - dt.now()).total_seconds()
		if wait_secs > 0:
			time.sleep(wait_secs)
		self.logger.info("get:%s", url)
		res = self.session.get(url)
		self.prev_request_time = dt.now()
		if res.ok:
			return res.text
		else:
			self.logger.error("get error:%s", url)
			raise RuntimeError(f'error occured in crawling {url}')

	def get_html(self, url):
		text = self.get(url)
		return lxml.html.fromstring(text)


class Scraper:

	def __init__(self, crawler):
		self.crawler = crawler

	def extract_contest_info_from_list(self, row):
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
			print(f'unknown duration:{id} {title}')
			duration_sec = 100000000 # some large value

		return Contest(id, title, start_at, duration_sec)


	def crawl_contests_list_page(self, url):
		root = self.crawler.get_html(f'https://atcoder.jp{url}&lang=ja')
		contest_list = root.cssselect('#main-div div.row > div:nth-of-type(2) table > tbody > tr')
		return [self.extract_contest_info_from_list(contest_row) for contest_row in contest_list]


	def crawl_contests_list(self):
		root = self.crawler.get_html('https://atcoder.jp/contest/archive?lang=ja')
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


	def crawl_contest_info(self, contest_id):
		root = self.crawler.get_html(f'https://{contest_id}.contest.atcoder.jp/?lang=ja')
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


	def crawl_task(self, contest_id, row):
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


	def crawl_tasks(self, contest_id):
		root = self.crawler.get_html(f'https://{contest_id}.contest.atcoder.jp/assignments?lang=ja')
		task_list = root.cssselect('div#outer-inner table tbody tr')
		for task_elem in task_list:
			try:
				self.crawl_task(contest_id, task_elem)
			except Exception as e:
				print(f'crawling tasks failed:{str(e)} : {contest_id}')


	def crawl_all_contest_tasks(self):
		db = database.get_connection()
		with closing(db) as con:
			contests = Contest.loadAll(db)

		for contest in contests:
			time.sleep(1)
			self.crawl_tasks(contest.id)


	def crawl_results(self, contest_id):
		json_str = self.crawler.get(f'https://{contest_id}.contest.atcoder.jp/standings/json')
		data_json = json.loads(json_str)['response']

		db = database.get_connection()
		try:
			for user_data in data_json[1:-1]:
				user_id = user_data['user_screen_name']
				user = User(user_id)
				user.persist(db)
				tasks = user_data['tasks']
				for i in range(len(tasks)):
					task = tasks[i]
					if 'failure' not in task:
						continue
					problem_id = task['task_id']
					score = task['score']
					failure = task['failure']
					penalty = 0#task['penalty']
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


	def crawl_all_contest_results(self):
		db = database.get_connection()
		with closing(db) as con:
			contests = Contest.loadAll(db)

		for contest in contests:
			time.sleep(1)
			print(contest.id)
			try:
				self.crawl_results(contest.id)
			except Exception as e:
				print('crawling tasks failed:' + str(e) + ' : ' + contest.id)


	def crawl_task_point(self, task):
		root = self.crawler.get_html(task.get_url())
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


	def crawl_task_point_of_contest(self, contest_id):
		db = database.get_connection()
		with closing(db) as con:
			tasks = Task.of_contest(contest_id, db)
		for task in tasks:
			self.crawl_task_point(task)


	def crawl_contest_by_id(self, contest_id):
		self.crawl_contest_info(contest_id)
		self.crawl_tasks(contest_id)
		self.crawl_task_point_of_contest(contest_id)
		self.crawl_results(contest_id)



def main():
	logger = logging.getLogger('crawler')
	logger.setLevel(logging.INFO)
	handler = logging.FileHandler('log/crawler.log')
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	contest_list = ['abc001']
	with Crawler() as crawler:
		scraper = Scraper(crawler)
		for contest in contest_list:
			scraper.crawl_results(contest)
			# scraper.crawl_contest_by_id(contest)


if __name__ == '__main__':
	main()

