from flask import Flask, render_template, request, redirect, url_for, session
import redis
import uuid
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "my-secret-key"


r = redis.Redis(
    host="localhost",
    port=6379,
    db=1,
    decode_responses=True,
    protocol=2
)

SESSION_TIMEOUT = 300



def create_session():
    sid = str(uuid.uuid4())
    session["session_id"] = sid

    key = f"form_session:{sid}"

    r.hset(key, mapping={
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page": "1"
    })

    r.expire(key, SESSION_TIMEOUT)

    log_activity("SESSION_CREATED", 1)

    print("SESSION CREATED:", sid)

    return sid



def get_session_data():
    sid = session.get("session_id")

    if not sid:
        return None

    data = r.hgetall(f"form_session:{sid}")

    return data if data else None


# LOG ACTIVITY
def log_activity(action, page):
    sid = session.get("session_id")

    if not sid:
        return

    key = f"session_logs:{sid}"

    log = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "page": page
    }

    r.rpush(key, json.dumps(log))

    r.expire(key, SESSION_TIMEOUT)



def update_session(data):
    sid = session.get("session_id")

    if not sid:
        return False

    key = f"form_session:{sid}"

    if not r.exists(key):
        return False

    r.hset(key, mapping=data)

    return True



@app.route("/", methods=["GET", "POST"])
def page1():

    if "session_id" not in session:
        create_session()

    if not get_session_data():
        session.clear()
        return redirect(url_for("expired"))

    if request.method == "POST":

        update_session({
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "page": "1"
        })

        log_activity("PAGE_1_SUBMITTED", 1)

        return redirect(url_for("page2"))

    sid = session["session_id"]

    ttl = r.ttl(f"form_session:{sid}")

    return render_template("page1.html", ttl=ttl, page=1)



@app.route("/page2", methods=["GET", "POST"])
def page2():

    if not get_session_data():
        session.clear()
        return redirect(url_for("expired"))

    if request.method == "POST":

        update_session({
            "college": request.form.get("college"),
            "course": request.form.get("course"),
            "year": request.form.get("year"),
            "page": "2"
        })

        log_activity("PAGE_2_SUBMITTED", 2)

        return redirect(url_for("page3"))

    sid = session["session_id"]

    ttl = r.ttl(f"form_session:{sid}")

    return render_template("page2.html", ttl=ttl, page=2)



@app.route("/page3", methods=["GET", "POST"])
def page3():

    if not get_session_data():
        session.clear()
        return redirect(url_for("expired"))

    if request.method == "POST":

        update_session({
            "interest": request.form.get("interest"),
            "experience": request.form.get("experience"),
            "message": request.form.get("message"),
            "page": "3"
        })

        log_activity("PAGE_3_SUBMITTED", 3)

        return redirect(url_for("success"))

    sid = session["session_id"]

    ttl = r.ttl(f"form_session:{sid}")

    return render_template("page3.html", ttl=ttl, page=3)



@app.route("/success")
def success():

    data = get_session_data()

    if not data:
        session.clear()
        return redirect(url_for("expired"))

    sid = session["session_id"]

    log_activity("FORM_COMPLETED", 3)

    logs = r.lrange(f"session_logs:{sid}", 0, -1)

    logs = [json.loads(x) for x in logs]

    return render_template(
        "success.html",
        data=data,
        logs=logs,
        session_id=sid
    )



@app.route("/expired")
def expired():
    return render_template("expired.html")


if __name__ == "__main__":

    print("===================================")
    print(" Redis 3-Page Form")
    print("===================================")
    print("Redis DB     : 1")
    print("Session TTL  : 5 minutes")
    print("URL          : http://127.0.0.1:5000")
    print("===================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )