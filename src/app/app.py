from flask import Flask, render_template
from model import Session, Contest, Result, Task

app = Flask(__name__)


@app.route('/')
def index():
    session = Session()
    contests = sorted(session.query(Contest), key=lambda x: x.date, reverse=True)
    return render_template('index.jinja2', contests=contests)


@app.route('/contests/<string:contest_id>')
def contest(contest_id):
    session = Session()
    contest = session.query(Contest).filter(Contest.contest_id == contest_id).first()
    tasks = session.query(Task).filter(Task.contest_id == contest_id).all()
    results = session.query(Result).filter(Result.contest_id == contest_id).all()
    result_hash = {(r.user_id, r.problem_id): r for r in results}
    user_ids = {r.user_id for r in results}
    return render_template('contest.jinja2', contest=contest, tasks=tasks,
                           result_hash=result_hash, user_ids=user_ids)
