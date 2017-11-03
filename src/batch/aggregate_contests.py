# coding: utf-8
import re

from batch.crawler import Crawler


def main():
  headers = {'Accept-Language': 'ja'}
  with Crawler() as crawler:
    html = crawler.get_html('https://beta.atcoder.jp/contests/archive', headers)
    page_count = len(html.cssselect('ul.pagination li'))
    print(page_count)

    for i in range(page_count):
      html = crawler.get_html(f'https://beta.atcoder.jp/contests/archive?page={i+1}', headers)
      table = html.cssselect('div.table-responsive table')[0]
      contests = table.cssselect('tr td:nth-child(2) a')
      for contest in contests:
        link = contest.get('href')
        match = re.fullmatch('^/contests/(.+)$', link)
        if match:
          print(match[1])


if __name__ == '__main__':
  main()
