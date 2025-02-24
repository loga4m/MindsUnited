from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash
from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    flash,
    url_for
)
from flask_login import login_user, logout_user
from flaskr.database import db, User
from flaskr.utils import validate_string


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        profession = request.form.get("profession")
        age = request.form.get("age")
        password = request.form.get("password")

        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if user:
            flash("This username is taken. Sorry :(")
            return redirect(url_for("auth.register"))
            
            

        if not (all(map(validate_string, [full_name, username, email, profession, password]))):
            flash("Bad input data. Try again, please.")
            return redirect(url_for("auth.register"))
        print("works")
        try:
            user = User(
                full_name=full_name,
                username=username,
                email=email,
                profession=profession,
                age=age
            )
            user.set_password(password)
            user.insert()
            flash("Successfully registered!")
            return redirect(url_for("auth.login"))

        except SQLAlchemyError:
            flash("Ooops!. Something went wrong.")
            return redirect(url_for("auth.register"))
        finally:
            db.session.close()

    return render_template("auth/register.html") 



@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember_me = True if request.form.get("remember_me") else False

        if not (all(map(validate_string, (username, password)))):
            flash("Ooops! Incorrect data. Can you try again, please?")
            return redirect(url_for("auth.login"))
        
        user: User = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()


        if not (user and check_password_hash(user.password_hash, password)):
            flash("Wrong login credentials. Can you try again, please? :)")
        
        login_user(user, remember=remember_me)

        return redirect(url_for("users.UserProfile", alternative_id=user.alternative_id))        


    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))