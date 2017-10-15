# coding: utf-8

import os
import os.path
import yaml


class Config:

  @staticmethod
  def load(env=None):
    if not(env):
      env = os.getenv('ENV')
    if not(env):
      env = 'development'
    with open(f'{os.path.dirname(__file__)}/../config/{env}.yml', 'r') as f:
      return yaml.load(f)
