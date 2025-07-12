from flask import Flask, render_template
import json
import os

app = Flask(__name__)

@app.route("/")
def status():
    if os.path.exists("signals.json"):
        with open("signals.json", "r") as f:
            signals = json.load(f)
    else:
        signals = {"daily_signals": [], "free_signals": []}

    is_online = os.path.exists("bot_online.txt")

    return render_template("status.html",
        bot_status="🟢 Online" if is_online else "🔴 Offline",
        daily_count=len(signals["daily_signals"]),
        free_count=len(signals["free_signals"]))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=('cert.pem', 'privkey.pem'))

