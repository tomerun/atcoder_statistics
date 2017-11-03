# coding: utf-8
from datetime import datetime as dt, timedelta
import time
import logging

import requests
import lxml.html
import lxml

logger = logging.getLogger(__name__)


class Crawler:

  def __init__(self, interval=0.5):
    self.interval_secs = interval
    self.prev_request_time = dt.now() - timedelta(seconds=interval * 2)

  def __enter__(self):
    self.http_session = requests.Session()
    self.http_session.headers.update({'User-Agent': 'AtCoder Statistics Crawler',
                                      'From': 'tomerunmail@gmail.com'})
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    if self.http_session:
      self.http_session.close()

  def get(self, url, headers=None):
    wait_until = self.prev_request_time + timedelta(seconds=self.interval_secs)
    wait_secs = (wait_until - dt.now()).total_seconds()
    if wait_secs > 0:
      time.sleep(wait_secs)
    logger.info("get:%s", url)
    res = self.http_session.get(url, headers=headers)
    self.prev_request_time = dt.now()
    if res.ok:
      return res.text
    else:
      logger.error("get error:%s", url)
      raise RuntimeError(f'error occured in crawling {url}')

  def get_html(self, url, headers=None):
    text = self.get(url, headers)
    return lxml.html.fromstring(text)
