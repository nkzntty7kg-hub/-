from flask import Flask, request, jsonify, render_template_string, session
import json
import uuid
import os
import requests

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

def send_webhook(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
    except:
        pass

PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Rainix License Panel</title>
    <style>
        body {
            margin:0;
            font-family: Arial;
            background: radial-gradient(circle at top, #0b1020, #05060a);
            color:#e5e7eb;
        }

        .wrap {
            max-width:800px;
            margin:40px auto;
            padding:20px;
        }

        .card {
            background:#0f172a;
            border:1px solid #1f2a44;
            border-radius:16px;
            padding:20px;
            box-shadow:0 0 20px rgba(59,130,246,0.15);
        }

        h2 { text-align:center; margin-bottom:20px; }

        button {
            padding:10px 14px;
            border:none;
            border-radius:10px;
            cursor:pointer;
            font-weight:bold;
        }

        .gen { background:#2563eb; color:white; }
        .gen:hover { background:#1d4ed8; }

        .danger { background:#ef4444; color:white; }
        .danger:hover { background:#dc2626; }

        .row {
            display:flex;
            gap:10px;
            margin-bottom:15px;
        }

        input {
            flex:1;
            padding:10px;
            border-radius:10px;
            border:1px solid #334155;
            background:#0b1220;
            color:white;
        }

        .keylist {
            margin-top:20px;
        }

        .key {
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:10px;
            margin:8px 0;
            background:#111c33;
            border-radius:10px;
            border:1px solid #1f2a44;
        }

        .status {
            font-size:12px;
            opacity:0.8;
        }

        .btn-small {
            padding:6px 10px;
            font-size:12px;
        }
    </style>
</head>
<body>
<div class="wrap">

<div class="card">
    <h2>Rainix Panel</h2>

    <div class="row">
        <input id="pass" placeholder="password">
        <button class="gen" onclick="login()">Login</button>
    </div>

    <div class="row">
        <button class="gen" onclick="generate()">Generate UUID Key</button>
    </div>

    <div class="row">
        <input id="key" placeholder="Enter key to revoke">
        <button class="danger" onclick="revokeInput()">Revoke</button>
    </div>

    <div class="keylist" id="keys"></div>
</div>

</div>

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
        loadKeys();
        alert("login success");
    } else {
        alert("wrong password");
    }
}

async function loadKeys(){
    if(!loggedIn) return;

    let res = await fetch('/list');
    let data = await res.json();

    let html = "";

    for(let k in data){
        html += `
        <div class='key'>
            <div>
                <div><b>${k}</b></div>
                <div class='status'>valid: ${data[k].valid} | device: ${data[k].device}</div>
            </div>
            <button class='danger btn-small' onclick="revoke('${k}')">Delete</button>
        </div>
        `;
    }

    document.getElementById('keys').innerHTML = html;
}

async function generate(){
    if(!loggedIn) return alert("login first");

    await fetch('/generate');
    loadKeys();
}

async function revoke(key){
    await fetch('/revoke', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({key:key})
    });

    loadKeys();
}

async function revokeInput(){
    let key = document.getElementById('key').value;
    await revoke(key);
}

</script>
</body>
</html>
"""

@app.route("/")
def panel():
    return render_template_string(PAGE)


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    if data.get("password") == ADMIN_PASSWORD:
        session["admin"] = True

        # ★ログイン通知
        send_webhook("@here ｒぐいんしたのだれ？ｗ")

        return jsonify({"ok": True})

    return jsonify({"ok": False})


def is_admin():
    return session.get("admin") == True


@app.route("/list")
def list_keys():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 403
    return jsonify(load_db())


@app.route("/generate")
def generate():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 403

    db = load_db()
    key = str(uuid.uuid4())

    db[key] = {"valid": True, "device": None}
    save_db(db)

    send_webhook(f"<@&1501803112586022992> キーを作ったよ\n`{key}`")

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

        send_webhook(f"<@&1501803112586022992> キーを消したよ\n`{key}`")

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
