from flask import Flask, request
import redis, uuid

app = Flask(__name__)
r = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True, protocol=2)

def save(sid, page, data):
    r.hset(f"session:{sid}", mapping={**data, "page": page})
    r.rpush(f"log:{sid}", f"Page {page}: {data}")


@app.route("/")
def p1():
    sid = str(uuid.uuid4())
    return f'<form action="/1" method="post"><input type=hidden name=sid value={sid}>Name: <input name=name>Email: <input name=email><button>Next</button></form>'


@app.route("/1", methods=["POST"])
def p1_save():
    sid = request.form["sid"]
    save(sid, 2, {"name": request.form["name"], "email": request.form["email"]})
    return f'<form action="/2" method="post"><input type=hidden name=sid value={sid}>College: <input name=college>Course: <input name=course><button>Next</button></form>'


@app.route("/2", methods=["POST"])
def p2_save():
    sid = request.form["sid"]
    save(sid, 3, {"college": request.form["college"], "course": request.form["course"]})
    return f'<form action="/3" method="post"><input type=hidden name=sid value={sid}>Language: <input name=language>Experience: <input name=exp><button>Submit</button></form>'


@app.route("/3", methods=["POST"])
def p3_save():
    sid = request.form["sid"]
    save(sid, "DONE", {"language": request.form["language"], "experience": request.form["exp"]})
    return f"Completed! Session: {sid}"


app.run(debug=True)