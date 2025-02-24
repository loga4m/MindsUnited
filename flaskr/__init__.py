from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user


def create_app() -> Flask:
    
    from . import auth, users, posts, requestops
    from .database import db, User

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="WU",
        SQLALCHEMY_DATABASE_URI="sqlite:///project.db"
    )
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    db.init_app(app)

    
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(users.users_bp)
    app.register_blueprint(posts.posts_bp)
    app.register_blueprint(requestops.requests_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.execute(
            db.select(User).filter_by(alternative_id=user_id)
        ).scalars().first()
    

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("users.UserProfile", alternative_id=current_user.alternative_id))
        return render_template("home.html")


    return app