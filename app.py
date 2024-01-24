from flask import (
    Flask,
    render_template,
    request,
    url_for,
    flash,
    redirect,
    session,
)

import flask_socketio

import mysql.connector

from datetime import datetime, timedelta, date

mydb = mysql.connector.connect(
    host="localhost", user="root", passwd="", database="dbhofin"
)
# mydb = mysql.connector.connect(host="www.db4free.net", user="sebastian200x", passwd="jds09122128032", database="dbhofin")

app = Flask(__name__)
app.secret_key = "capstone"

# Database for localhost

# app.config["MYSQL_HOST"] = "localhost"
# app.config["MYSQL_USER"] = "root"
# app.config["MYSQL_PASSWORD"] = ""
# app.config["MYSQL_DB"] = "dbhofin"

# Database for online database

# app.config['MYSQL_HOST'] = 'www.db4free.net'
# app.config['MYSQL_USER'] = 'sebastian200x'
# app.config['MYSQL_PASSWORD'] = 'jds09122128032'
# app.config['MYSQL_DB'] = 'dbhofin'
# app.config['MYSQL_PORT'] = 3306

# mysql = MySQL(app)


# session checker if logged in it will redirect to respective homepage
def userchecker(dir):
    is_admin = session.get("is_admin")
    if is_admin == "yes":
        return redirect(url_for("admin_members_reg"))
    elif is_admin == "no":
        return redirect(url_for("member_payment_reminder"))
    else:
        return render_template(dir)


def adminredirect(dir, **args):
    is_admin = session.get("is_admin")
    if is_admin is not None:
        if is_admin == "no":
            return redirect(url_for("member_payment_reminder"))
        else:
            return render_template(dir, **args)
    else:
        return redirect(url_for("login"))


def memberredirect(dir, **args):
    is_admin = session.get("is_admin")
    if is_admin is not None:
        if is_admin == "yes":
            return redirect(url_for("admin_members_reg"))
        else:
            return render_template(dir, **args)
    else:
        return redirect(url_for("login"))


# username generator
def generate_username(id):
    now = datetime.now()
    year_today = now.strftime("%Y")
    username = year_today + str(id)
    return username


# List of Session
@app.route("/sessions")
def active_sessions():
    session_data = []
    for key, value in session.items():
        session_data.append(f"{key}: {value}")
    return "\n".join(session_data)


@app.route("/")
def index():
    # Temporary admin creator for 1st time opened
    create = mydb.cursor()
    create.execute("SELECT * FROM tbl_useracc WHERE is_admin='yes' AND is_deleted='no'")
    result = create.fetchall()
    if len(result) == 0:
        create.execute(
            "INSERT INTO `tbl_useracc`(`user_id`, `username`, `password`, `is_admin`, `is_deleted`) VALUES ('1','admin','admin','yes','no')"
        )
        create.execute(
            "INSERT INTO `tbl_userinfo`(`userinfo_id`, `user_id`, `given_name`) VALUES ('1','1','Admin')"
        )
        mydb.commit()
        create.close()
    return userchecker("index.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    # LOGIN
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        login = mydb.cursor()
        login.execute(
            "SELECT * FROM tbl_useracc WHERE username=%s AND password=%s",
            (username, password),
        )
        result = login.fetchall()
        if len(result) != 0:
            if result[0][5] == "no":
                login.execute(
                    "SELECT * FROM tbl_useracc, tbl_userinfo WHERE tbl_useracc.username = %s AND tbl_useracc.password = %s AND tbl_useracc.user_id = tbl_userinfo.user_id",
                    (username, password),
                )
                info = login.fetchone()
                if "login_attempts" not in session or session["login_attempts"] != 0:
                    is_admin = info[4]
                    fullname = info[8] + " " + info[10]
                    user_id = info[0]
                    if is_admin == "yes":
                        session.clear()
                        session["is_admin"] = is_admin
                        session["fullname"] = fullname
                        session["user_id"] = user_id
                        session["user_type"] = "ADMIN"
                        return redirect(url_for("admin_members_reg"))
                        # return render_template("home.html")

                    elif is_admin == "no":
                        session.clear()
                        session["is_admin"] = is_admin
                        session["fullname"] = fullname
                        session["user_id"] = user_id
                        session["user_type"] = "USER"
                        return redirect(url_for("member_payment_reminder"))
            else:
                session[
                    "reminder"
                ] = "The user account has been deleted. If you think this is a mistake, please contact the ADMINISTRATOR"

        else:
            # LOGIN ATTEMPT
            login_attempts = session.get("login_attempts", 3)
            session["login_attempts"] = max(0, login_attempts - 1)
            login_attempts = session["login_attempts"]

            # Check if the user has exceeded the maximum login attempts
            if login_attempts == 0:
                current_time = datetime.now()
                new_time = current_time + timedelta(seconds=30)
                if "last_attempt" not in session:
                    session["last_attempt"] = new_time.strftime("%H:%M:%S")

                last_attempt_time = datetime.strptime(
                    session["last_attempt"], "%H:%M:%S"
                ).time()
                current_time = current_time.time()

                if last_attempt_time >= current_time:
                    time_difference = datetime.combine(
                        datetime.min, last_attempt_time
                    ) - datetime.combine(datetime.min, current_time)
                    time_left = str(time_difference)
                    session[
                        "reminder"
                    ] = f"Maximum login attempts exceeded. Please try again after {time_left} seconds."
                else:
                    session.clear()
                    session["reminder"] = f"Wrong Username or Password, 3 tries left"

            elif login_attempts == 2 or login_attempts == 1:
                session[
                    "reminder"
                ] = f"Wrong Username or Password, {login_attempts} {'tries' if login_attempts == 2 else 'try'} left"

    return userchecker("login.html")


@app.route("/admin/members_reg", methods=["POST", "GET"])
def admin_members_reg():
    last = mydb.cursor()
    last.execute("SELECT user_id FROM tbl_useracc ORDER BY user_id DESC LIMIT 1")
    last_row = last.fetchone()
    if last_row:
        next_id = last_row[0] + 1
    else:
        next_id = 1
    last.close()

    username = generate_username(next_id)

    if request.method == "POST":
        given_name = request.form["given_name"]
        middle_name = request.form["middle_name"]
        last_name = request.form["last_name"]
        gender = request.form["gender"]
        password = request.form["password"]
        email = request.form["email"]

        register = mydb.cursor()

        try:
            register.execute(
                "INSERT INTO tbl_useracc(username, password, email, is_admin, is_deleted) VALUES(%s, %s, %s, %s, %s)",
                (username, password, email, "no", "no"),
            )

            id = register.lastrowid

            register.execute(
                "INSERT INTO tbl_userinfo(userinfo_id, user_id, given_name, middle_name, last_name, gender) VALUES( %s, %s, %s, %s, %s, %s)",
                (id, id, given_name, middle_name, last_name, gender),
            )

            register.execute(
                "INSERT INTO tbl_property (property_id, user_id) VALUES (%s, %s)",
                (id, id),
            )

            mydb.commit()
            register.close()
            flash("Registration successful!", "success")

        except Exception as e:
            mydb.rollback()
            register.close()
            flash(
                "Registration failed. Please try again. Error: {}".format(str(e)),
                "error",
            )

    return adminredirect("/admin/members_reg.html", username=username)


@app.route("/admin/members_face_reg")
def members_face_reg():
    return adminredirect("/admin/members_reg_face.html")


@app.route("/admin/members_info", methods=["POST", "GET"])
def admin_members_info():
    # inc.execute(
    #     "SELECT * FROM tbl_property, tbl_useracc, tbl_userinfo WHERE tbl_property.blk_no IS NULL AND tbl_property.lot_no IS NULL AND tbl_property.homelot_area IS NULL AND tbl_property.open_space IS NULL AND tbl_property.sharein_loan IS NULL AND tbl_property.principal_interest IS NULL AND tbl_property.MRI IS NULL AND tbl_property.total IS NULL AND tbl_useracc.is_admin = 'no' AND tbl_useracc.is_deleted = 'no';"
    # )
    inc = mydb.cursor()
    inc.execute(
        """
    SELECT *
    FROM tbl_property
    JOIN tbl_userinfo ON tbl_property.user_id = tbl_userinfo.user_id
    JOIN tbl_useracc ON tbl_property.user_id = tbl_useracc.user_id
    WHERE is_admin = "no" 
        AND is_deleted = "no"
        AND (blk_no IS NULL 
        OR lot_no IS NULL 
        OR homelot_area IS NULL 
        OR open_space IS NULL 
        OR sharein_loan IS NULL 
        OR principal_interest IS NULL 
        OR MRI IS NULL 
        OR total IS NULL)
        """
    )
    inc = inc.fetchall()

    complete = mydb.cursor()
    complete.execute(
        """
    SELECT *
    FROM tbl_property
    JOIN tbl_userinfo 
    JOIN tbl_useracc 
    ON tbl_property.user_id = tbl_userinfo.user_id AND tbl_property.user_id = tbl_useracc.user_id
    WHERE is_admin = "no" 
        AND is_deleted = "no"
        AND blk_no IS NOT NULL
        AND lot_no IS NOT NULL
        AND homelot_area IS NOT NULL
        AND open_space IS NOT NULL
        AND sharein_loan IS NOT NULL
        AND principal_interest IS NOT NULL
        AND MRI IS NOT NULL
        AND total IS NOT NULL
        """
    )
    complete = complete.fetchall()

    return adminredirect("/admin/members_info.html", inc=inc, complete=complete)


@app.route("/admin/edit_info/<int:id>", methods=["POST", "GET"])
def admin_edit_info(id):
    info = mydb.cursor()
    info.execute(
        """
    SELECT * 
    FROM tbl_userinfo 
    JOIN tbl_property
    ON tbl_userinfo.user_id = %s AND tbl_property.user_id = %s
    LIMIT 1""",
        (id, id),
    )

    info = info.fetchone()

    return adminredirect("/admin/edit_info.html", info=info)


@app.route("/admin/delete_info/<int:id>", methods=["POST", "GET"])
def delete_info(id):
    delete = mydb.cursor()
    try:
        delete.execute(
            """
            UPDATE
                `tbl_useracc`
            SET
                `is_deleted` = 'yes'
            WHERE
                `tbl_useracc`.`user_id` = %s;
            """,
            (id,),
        )
        mydb.commit()
        flash("Account deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting account: {str(e)}", "error")

    return redirect(url_for("admin_members_info"))
    # return redirect(url_for("admin_members_info"))


@app.route("/admin/update_info/<int:id>", methods=["POST", "GET"])
def update_info(id):
    given_name = request.form.get("given_name")
    middle_name = request.form.get("middle_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    id_no = request.form.get("id_no")
    blk_no = request.form.get("blk_no")
    lot_no = request.form.get("lot_no")
    homelot_area = request.form.get("homelot_area")
    open_space = request.form.get("open_space")
    sharein_loan = request.form.get("sharein_loan")
    principal_interest = request.form.get("principal_interest")
    MRI = request.form.get("MRI")
    total = request.form.get("total")

    update = mydb.cursor()

    try:
        update.execute(
            """
                UPDATE tbl_userinfo
                SET given_name = %s,
                    middle_name = %s,
                    last_name = %s,
                    gender = %s
                WHERE user_id = %s
                """,
            (
                given_name,
                middle_name,
                last_name,
                gender,
                id,
            ),
        )
        update.execute(
            """
            UPDATE tbl_property
            SET id_no = %s,
                blk_no = %s,
                lot_no = %s,
                homelot_area = %s,
                open_space = %s,
                sharein_loan = %s,
                principal_interest = %s,
                MRI = %s,
                total = %s
            WHERE user_id = %s
            """,
            (
                id_no,
                blk_no,
                lot_no,
                homelot_area,
                open_space,
                sharein_loan,
                principal_interest,
                MRI,
                total,
                id,
            ),
        )
        mydb.commit()
        update.close()
        flash("Account updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating account: {str(e)}", "error")
    return redirect(url_for("admin_members_info"))


@app.route("/admin/payment_history", methods=["POST", "GET"])
def admin_payment_history():
    history = mydb.cursor()
    history.execute(
        """
        SELECT tbl_transaction.*, tbl_userinfo.*
        FROM tbl_transaction
        JOIN tbl_userinfo ON tbl_userinfo.user_id = tbl_transaction.user_id
        WHERE tbl_transaction.transc_type != 'reminder'
        ORDER BY tbl_transaction.date;
        """
    )
    history = history.fetchall()
    return adminredirect("/admin/payment_history.html", history=history)


@app.route("/admin/view_history/<int:id>", methods=["POST", "GET"])
def admin_view_history(id):
    view = mydb.cursor()
    view.execute(
        """
        SELECT *
        FROM tbl_transaction
        JOIN tbl_userinfo ON tbl_transaction.user_id = tbl_userinfo.user_id
        WHERE tbl_transaction.transac_id = %s;
        """,
        (id,),
    )
    view = view.fetchone()
    return adminredirect("/admin/view_history.html", view=view)


@app.route("/admin/payment_reminder", methods=["POST", "GET"])
def admin_payment_reminder():
    new = mydb.cursor()
    new.execute(
        """
        SELECT
            tbl_property.*,
            tbl_userinfo.*
        FROM
            tbl_property
        LEFT JOIN tbl_userinfo ON tbl_property.user_id = tbl_userinfo.user_id
        LEFT JOIN tbl_useracc ON tbl_property.user_id = tbl_useracc.user_id
        WHERE
            tbl_property.user_id NOT IN(
            SELECT
                user_id
            FROM
                tbl_transaction
        ) AND tbl_property.total IS NOT NULL AND tbl_useracc.is_admin = 'no' AND tbl_useracc.is_deleted = 'no'  
        """
    )
    new = new.fetchall()

    return adminredirect("admin/payment_reminder.html", new=new)


@app.route("/admin/payment_remind/<int:id>", methods=["POST", "GET"])
def admin_payment_remind(id):
    reminder = mydb.cursor()
    reminder.execute(
        """
    SELECT tbl_property.total, tbl_userinfo.*
    FROM tbl_property
    JOIN tbl_userinfo ON tbl_userinfo.user_id = %s AND tbl_property.user_id = %s
    LIMIT 1;
        """,
        (
            id,
            id,
        ),
    )
    reminder_data = reminder.fetchone()
    return adminredirect("admin/payment_remind.html", reminder=reminder_data)


# SELECT tbl_transaction.*
# FROM tbl_property
# JOIN tbl_transaction ON tbl_property.user_id = tbl_transaction.user_id
# WHERE tbl_property.total IS NOT NULL


@app.route("/admin/payment_remind/remind/<int:id>", methods=["POST", "GET"])
def admin_payment_remind_remind(id):
    due = request.form.get("due")
    date_conv = datetime.strptime(due, "%Y-%m-%d")
    due_conv = date_conv.strftime("%Y-%m-%d")
    amount = request.form.get("amount")
    reminding = mydb.cursor()
    reminding.execute(
        """
    INSERT INTO `tbl_transaction`(
    `user_id`,
    `transc_type`,
    `amount`,
    `due_date`
    )
    VALUES(
        %s,
        "reminder",
        %s,
        %s
    );
        """,
        (
            id,
            amount,
            due_conv,
        ),
    )
    mydb.commit()
    reminding.close()
    return redirect(url_for("admin_payment_reminder"))


@app.route("/member/payment_reminder", methods=["POST", "GET"])
def member_payment_reminder():
    remind = mydb.cursor()
    user_id = session["user_id"]
    remind.execute(
        """
        SELECT
            *
        FROM
            `tbl_transaction`
        WHERE
            transc_type = "reminder" AND user_id = %s
        ORDER BY 
            due_date;
        """,
        (user_id,),
    )
    remind = remind.fetchall()
    count = len(remind)
    
    # get all rows in sql that doesnt have duplicate in due_date column in the same ID and in the specific id only
    # SELECT * FROM your_table_name WHERE ID = 'your_specific_id' GROUP BY due_date HAVING COUNT(*) = 1;
    # SELECT * FROM tbl_transaction WHERE user_id = '2' GROUP BY user_id, due_date HAVING COUNT(*) = 1;

    return memberredirect("member/payment_reminder.html", remind=remind, count=count)


@app.route("/member/payment/<int:payment_info>", methods=["POST", "GET"])
def member_payment(payment_info):
    return memberredirect("/member/payment.html")


@app.route("/member/payment_history", methods=["POST", "GET"])
def member_payment_history():
    return memberredirect("member/payment_history.html")


@app.route("/member/payment_verification")
def payment_verification():
    return memberredirect("/member/payment_verification.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


#     #pang call nang or view nang mga data
#     quer=mydb.cursor()
# #pang execute nang database
#     quer.execute("SELECT * FROM tbl_userinfo")
#     data=quer.fetchall()
#     quer.close()
# session
# if "fullname" in session:
#     fullname = session["fullname"]
#     return render_template('home.html',users=data,userS=fullname)
# else:
#     return redirect(url_for("login"))


# @app.route("/delete/<string:id_data>", methods=["GET", "POST"])
# def delete(id_data):
#     flash("Record Has Been Deleted Successfully")
#     sql = mydb.cursor()
#     sql.execute("DELETE FROM tbl_userinfo WHERE userinfo_id=%s", (id_data,))
#     mydb.commit()
#     return redirect(url_for("Home"))


# @app.route("/payment/<int:id>", methods=["POST", "GET"])
# def payment(id):
#     if request.method == "POST":
#         amount = request.form.get("amount")
#         userid = id
#         option = request.form.get("option")

#         sql = mydb.cursor()
#         sql.execute("SELECT * FROM tbl_transaction WHERE user_id=%s", [userid])
#         mydb.commit()
#         data = sql.fetchall()
#         for row in data:
#             debt = row[2]
#             totalamt = int(debt) - int(amount)
#             datetimenow = datetime.now()
#             format = datetimenow.strftime("%Y-%m-%d %H:%M:%S")
#             sql.execute(
#                 "UPDATE tbl_transaction SET balance_debt=%s, transac_type=%s ,amount=%s,date=%s WHERE user_id=%s",
#                 (totalamt, option, amount, format, userid),
#             )
#             mydb.commit()
#             sql.execute(
#                 "UPDATE tbl_userinfo SET Total=%s WHERE user_id=%s", (totalamt, userid)
#             )
#             mydb.commit()
#             sql.close()
#             return redirect(url_for("Home2"))
#     else:
#         return render_template("payment.html")

#     # session
#     if "username" in session:
#         username = session["username"]

#         return render_template("payment.html", users=data, userS=username)

#     else:
#         return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port="6969")


# to make it accessible to other device in the same network use this:
# flask run --host=0.0.0.0
