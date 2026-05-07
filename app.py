from flask import Flask, request, jsonify, render_template_string, session
import json
import uuid
import requests
import os

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

DB_FILE = "keys.json"

WEBHOOK_URL = "https://discord.com/api/webhooks/1501803448100720761/kGMlOO7g9QRmCEulJlbpw6jgpVdNn_NK0a05RpaadlrVDhBHBhxEsqV4OPkZuUBE4A7W"

ADMIN_PASSWORD = "3f2c1b7e-9c6a-4a12-8d3e-2f7a1c9b5d44"

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


def is_admin():
    return session.get("admin") == True


def send_webhook(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except:
        pass

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Panel</title>
</head>
<body style="font-family:Arial;background:#0b1020;color:white;padding:30px">

<h2>Admin Panel</h2>

<div>
    <input id="pass" placeholder="password">
    <button onclick="login()">Login</button>
</div>

<br>

<button onclick="generate()">Generate Key</button>

<div id="keys"></div>

<script>

let loggedIn = false;

async function login(){
    let pass = document.getElementById("pass").value;

    let res = await fetch("/login", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({password:pass})
    });

    let data = await res.json();

    if(data.ok){
        loggedIn = true;
        load();
        alert("login success");
    } else {
        alert("wrong password");
    }
}

async function load(){
    if(!loggedIn) return;

    let res = await fetch("/list");
    if(res.status != 200) return;

    let data = await res.json();

    let html = "";

    for(let k in data){
        html += `
        <div>
            <b>${k}</b>
            <button onclick="del('${k}')">delete</button>
        </div>
        `;
    }

    document.getElementById("keys").innerHTML = html;
}

async function generate(){
    if(!loggedIn) return alert("login first");

    await fetch("/generate", {method:"POST"});
    load();
}

async function del(k){
    await fetch("/revoke", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({key:k})
    });

    load();
}

</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    if data.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return jsonify({"ok": True})

    return jsonify({"ok": False})


@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/list")
def list_keys():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 403

    return jsonify(load_db())


@app.route("/generate", methods=["POST"])
def generate():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 403

    db = load_db()
    key = str(uuid.uuid4())

    db[key] = {"valid": True, "device": None}

    save_db(db)

    # ★ 修正ここ
    send_webhook(f"<@&1501803112586022992> キーをつくったよ!\n`{key}`")

    return jsonify({"key": key})


@app.route("/revoke", methods=["POST"])
def revoke():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 403

    data = request.json
    key = data.get("key")

    db = load_db()

    if key in db:
        del db[key]
        save_db(db)

        send_webhook(f"<@&1501803112586022992> キーを削除したよ!\n`{key}`")

    return jsonify({"ok": True})


@app.route("/check", methods=["POST"])
def check():
    data = request.json
    key = data.get("key")
    device = data.get("device")

    db = load_db()

    if key not in db:
        return jsonify({"valid": False})

    entry = db[key]

    if entry["device"] is None:
        entry["device"] = device
        save_db(db)
        return jsonify({"valid": True})

    return jsonify({"valid": entry["device"] == device})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
