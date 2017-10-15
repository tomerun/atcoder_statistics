# coding: utf-8
import json
import re
from datetime import datetime as dt, timedelta
import time
import logging

import lxml.html
import lxml
import cssselect

from crawler import Crawler, logger
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


class Scraper:

	def __init__(self, crawler):
		self.crawler = crawler

	def _extract_contest_info_from_list(self, row):
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
			logger.warn(f'unknown duration:{id} {title}')
			duration_sec = 100000000 # some large value

		return Contest(contest_id=id, title=title, date=start_at, duration_sec=duration_sec)


	def _crawl_contests_list_page(self, url):
		root = self.crawler.get_html(f'https://atcoder.jp{url}&lang=ja')
		contest_list = root.cssselect('#main-div div.row > div:nth-of-type(2) table > tbody > tr')
		return [self._extract_contest_info_from_list(contest_row) for contest_row in contest_list]


	def crawl_contests_list(self, db_session):
		root = self.crawler.get_html('https://atcoder.jp/contest/archive?lang=ja')
		page_list = root.cssselect('#main-div ul.pagination-sm > li')
		contests = []
		for page in page_list:
			link = page.cssselect('a')[0]
			contests = contests + _crawl_contests_list_page(link.get('href'))
		db_session.add_all(contests)


	def crawl_contest_info(self, contest_id, db_session):
		root = self.crawler.get_html(f'https://{contest_id}.contest.atcoder.jp/?lang=ja')
		title = root.cssselect('div#outer-inner div.insert-participant-box h1')[0].text_content()
		times = root.cssselect('div.navbar-fixed-top a.brand span.bland-small time')
		start_at = str_to_datetime(times[0].text_content())
		end_at = str_to_datetime(times[1].text_content())
		diff = end_at - start_at
		contest = Contest(contest_id=contest_id, title=title, date=start_at, duration_sec=diff.total_seconds())
		logger.info(contest)
		db_session.add(contest)


	def _crawl_task(self, contest_id, row, db_session):
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

		problem = Problem(problem_id=problem_id, title=title)
		task = Task(contest_id=contest_id, problem_id=problem_id, symbol=symbol, path=path)
		logger.info(problem)
		logger.info(task)
		db_session.add(problem)
		db_session.add(task)


	def crawl_tasks(self, contest_id, db_session):
		root = self.crawler.get_html(f'https://{contest_id}.contest.atcoder.jp/assignments?lang=ja')
		task_list = root.cssselect('div#outer-inner table tbody tr')
		for task_elem in task_list:
			try:
				self._crawl_task(contest_id, task_elem, db_session)
			except Exception as e:
				logger.error(f'crawling tasks failed:{str(e)} : {contest_id}')


	def crawl_all_contest_tasks(self, db_session):
		for contest in db_session.query(Contest).all():
			self.crawl_tasks(contest.contest_id, db_session)


	def crawl_task_point(self, task, db_session):
		root = self.crawler.get_html(task.get_url())
		statement = root.cssselect('#task-statement')[0].text_content()
		match = re.search(r'配点\s*:\s*(\d+)', statement)
		if match:
			point = int(match.group(1))
			task_point = TaskPoint(contest_id=task.contest_id, problem_id=task.problem_id, point=point * 100) # normalize point
			db_session.add(task_point)
			logger.info(task.contest_id + '-' + str(task.symbol) + ' has ' + str(point) + ' points.')
		else:
			logger.warn(task.contest_id + '-' + str(task.symbol) + ' has unknown points.')


	def crawl_task_point_of_contest(self, contest_id, db_session):
		tasks = db_session.query(Task).filter(Task.contest_id == contest_id)
		for task in tasks:
			self.crawl_task_point(task, db_session)


	def crawl_results(self, contest_id, db_session):
		json_str = self.crawler.get(f'https://beta.atcoder.jp/contests/{contest_id}/standings/json')
		users = json.loads(json_str)['StandingsData']
		tasks = {t.path: t.problem_id for t in db_session.query(Task).filter(Task.contest_id == contest_id)}
		for user_data in users:
			results = user_data["TaskResults"]
			if not results:
				continue
			user_id = user_data['UserScreenName']
			user = User(user_id=user_id)
			db_session.add(user)
			for task_name in results:
				result = results[task_name];
				problem_id = tasks[task_name]
				score = result['Score']
				failure = result['Penalty']
				elapsed = result['Elapsed'] // 1000000000
				result = Result(contest_id=contest_id, problem_id=problem_id, user_id=user_id,
				                score=score, failure=failure, elapsed=elapsed)
				db_session.add(result)


	def crawl_all_contest_results(self, db_session):
		for contest in db_session.query(Contest).all():
			logger.info(contest.id)
			try:
				self.crawl_results(contest.id, db_session)
			except Exception as e:
				logger.error('crawling tasks failed:' + str(e) + ' : ' + contest.id)


	def crawl_contest_by_id(self, contest_id, db_session):
		self.crawl_contest_info(contest_id, db_session)
		self.crawl_tasks(contest_id, db_session)
		self.crawl_task_point_of_contest(contest_id, db_session)
		self.crawl_results(contest_id, db_session)


def main():
	logger.setLevel(logging.INFO)
	handler = logging.FileHandler('log/crawler.log')
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	contest_list = ['abc001']
	with Crawler() as crawler:
		scraper = Scraper(crawler)
		for contest in contest_list:
			db_session = Session()
			try:
				# scraper.crawl_results(contest, db_session)
				scraper.crawl_contest_by_id(contest, db_session)
			except Exception as e:
				db_session.rollback()
				raise e
			finally:
				db_session.commit()
				db_session.close()

if __name__ == '__main__':
	main()

