# coding: utf-8

from contextlib import closing
import MySQLdb
import MySQLdb.cursors
import json
import os

def get_connection():
	with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as config_file:
		config = json.load(config_file)
	return MySQLdb.connect(host='localhost',
	                       user=config['DB_user'],
	                       passwd=config['DB_pass'],
	                       db='atcoder',
	                       charset='utf8',
	                       cursorclass=MySQLdb.cursors.DictCursor)

def create_tables(db_connection):
	with closing(db_connection.cursor()) as cursor:
		sql = '''CREATE TABLE contests(
		             contest_id VARCHAR(255) PRIMARY KEY,
		             title VARCHAR(255) NOT NULL,
		             date DATETIME NOT NULL,
		             duration_sec INT NOT NULL);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE users(
		             user_id VARCHAR(255) PRIMARY KEY);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE user_countries(
		             user_id VARCHAR(255) PRIMARY KEY REFERENCES users(user_id),
		             country VARCHAR(255) NOT NULL);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE user_affiliations(
		             user_id VARCHAR(255) PRIMARY KEY REFERENCES users(user_id),
		             affiliation VARCHAR(255) NOT NULL);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE user_twitter_ids(
		             user_id VARCHAR(255) PRIMARY KEY REFERENCES users(user_id),
		             twitter_id VARCHAR(255) NOT NULL);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE user_birth_years(
		             user_id VARCHAR(255) PRIMARY KEY REFERENCES users(user_id),
		             birth_year INT NOT NULL);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE problems(
		             problem_id INT PRIMARY KEY,
		             title VARCHAR(255) NOT NULL);'''
		cursor.execute(sql)

		sql = '''CREATE TABLE tasks(
		             contest_id VARCHAR(255) REFERENCES contests(contest_id),
		             problem_id INT REFERENCES problems(problem_id),
		             symbol VARCHAR(255) NOT NULL,
		             path VARCHAR(255) NOT NULL,
		             PRIMARY KEY(contest_id, problem_id));'''
		cursor.execute(sql)

		sql = '''CREATE TABLE task_points(
		             contest_id VARCHAR(255) REFERENCES contests(contest_id),
		             problem_id INT REFERENCES problems(problem_id),
		             point INT NOT NULL,
		             PRIMARY KEY(contest_id, problem_id));'''
		cursor.execute(sql)

		sql = '''CREATE TABLE results(
		             contest_id VARCHAR(255) REFERENCES contests(contest_id),
		             problem_id INT REFERENCES problems(problem_id),
		             user_id VARCHAR(255) REFERENCES users(user_id),
		             score INT NOT NULL,
		             failure INT NOT NULL,
		             elapsed INT NOT NULL,
		             penalty INT NOT NULL,
		             PRIMARY KEY(contest_id, problem_id, user_id),
		             INDEX(user_id));'''
		cursor.execute(sql)


if __name__ == '__main__':
	db = get_connection()
	with closing(db) as con:
		create_tables(con)

