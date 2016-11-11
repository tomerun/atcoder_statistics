# coding: utf-8
import os
import sys
import re
import requests
import lxml.html
import lxml
import cssselect

def extract_contest_info(row):
	cells = row.findall('td')
	datetime = cells[0].text_content()
	link = cells[1].find('a')
	url = link.get('href')
	m = re.search('https://([^.]+)\.contest\.atcoder\.jp', url)
	id = m.group(1)
	name = link.text
	duration = cells[2].text_content()
	return (datetime, duration, id, name)

def crawl_page(url):
	page = requests.get('https://atcoder.jp' + url + '&lang=ja')
	root = lxml.html.fromstring(page.text)
	contest_list = root.cssselect('#main-div div.row > div:nth-of-type(2) table > tbody > tr')
	return [extract_contest_info(contest_row) for contest_row in contest_list]

def main():
	top = requests.get('https://atcoder.jp/contest/archive?lang=ja')
	root = lxml.html.fromstring(top.text)
	page_list = root.cssselect('#main-div ul.pagination-sm > li')
	ids = []
	for page in page_list:
		link = page.cssselect('a')[0]
		ids = ids + crawl_page(link.get('href'))
	return ids

if __name__ == '__main__':
	print(main())

