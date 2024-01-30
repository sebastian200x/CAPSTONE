from flask import Flask, render_template, request, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "your_secret_key"

login_attempts = {}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        client_ip = request.remote_addr
        if client_ip in login_attempts and login_attempts[client_ip]["attempts"] >= 3:
            cooldown_time = login_attempts[client_ip]["cooldown_time"]
            if time.time() < cooldown_time:
                cooldown_remaining = int(cooldown_time - time.time())
                return render_template(
                    "cooldown.html", cooldown_remaining=cooldown_remaining
                )
            else:
                login_attempts[client_ip] = {"attempts": 0, "cooldown_time": 0}
                return attempts

        username = request.form["username"]
        password = request.form["password"]

        # Check login credentials (replace with your authentication logic)
        if username == "a" and password == "a":
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            if client_ip in login_attempts:
                login_attempts[client_ip]["attempts"] += 1
            else:
                login_attempts[client_ip] = {"attempts": 1, "cooldown_time": 0}
            if login_attempts[client_ip]["attempts"] >= 3:
                login_attempts[client_ip]["cooldown_time"] = (
                    time.time() + 300
                )  # 5 minutes cooldown
            return "Incorrect username or password. Please try again."
    return render_template("login2.html")


@app.route("/home")
def home():
    return "Welcome!"


if __name__ == "__main__":
    app.run(debug=True, port="5000")
