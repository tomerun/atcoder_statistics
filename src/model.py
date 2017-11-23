# coding: utf-8
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from datetime import timedelta

from config import Config

config = Config.load()['db']
engine = create_engine(f'mysql://{config["user"]}:{config["pass"]}@{config["host"]}/{config["name"]}', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Contest(Base):
  __tablename__ = 'contests'

  contest_id = Column(String, primary_key=True)
  title = Column(String)
  date = Column(DateTime)
  duration_sec = Column(Integer)

  @property
  def end_date(self):
    return self.date + timedelta(seconds=self.duration_sec)


class User(Base):
  __tablename__ = 'users'

  user_id = Column(String, primary_key=True)


class Problem(Base):
  __tablename__ = 'problems'

  problem_id = Column(Integer, primary_key=True)
  title = Column(String)


class Task(Base):
  __tablename__ = 'tasks'

  contest_id = Column(String, ForeignKey('contests.contest_id'), primary_key=True)
  problem_id = Column(Integer, ForeignKey('problems.problem_id'), primary_key=True)
  symbol = Column(String)
  path = Column(String)

  contest = relationship('Contest', backref='tasks')
  problem = relationship('Problem')

  def get_url(self):
    return f'http://{self.contest_id}.contest.atcoder.jp/tasks/{self.path}'


class TaskPoint(Base):
  __tablename__ = 'task_points'

  contest_id = Column(String, primary_key=True)
  problem_id = Column(Integer, primary_key=True)
  point = Column(Integer)

  __table_args__ = (ForeignKeyConstraint(['contest_id', 'problem_id'], ['tasks.contest_id', 'tasks.problem_id']), {})

  task = relationship('Task', backref='task_point')


class Result(Base):
  __tablename__ = 'results'

  contest_id = Column(String, ForeignKey('contests.contest_id'), primary_key=True)
  problem_id = Column(Integer, ForeignKey('problems.problem_id'), primary_key=True)
  user_id = Column(String, ForeignKey('users.user_id'), primary_key=True)
  score = Column(Integer)  # x100 from the "real" score
  failure = Column(Integer)
  elapsed = Column(Integer)  # in seconds

  contest = relationship('Contest', backref='results')
  problem = relationship('Problem', backref='results')
  user = relationship('User', backref='results')

  def formatted_elapsed(self):
    return "{:d}:{:02d}:{:02d}".format(self.elapsed // 3600, self.elapsed // 60 % 60, self.elapsed % 60)
