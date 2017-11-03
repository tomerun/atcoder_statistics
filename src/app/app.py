from flask import Flask
from model import Session, Contest

app = Flask(__name__)


@app.route('/')
def index():
    session = Session()
    return '\n'.join(map(lambda x: str(x), session.query(Contest.contest_id)))
