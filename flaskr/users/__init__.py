from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user
from sqlalchemy import select
from flaskr.database import db, User, Post, PostType


users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/<string:alternative_id>")
@login_required
def UserProfile(alternative_id: str):
    user: User = db.one_or_404(
        db.select(User).filter_by(alternative_id=alternative_id)
    )

    user_short_data = user.get_short_info()

    post_types = [
        post_type.name 
        for post_type in db.session.execute(
            db.select(PostType)
        ).scalars().all()
    ]

    confirmed_for_deployment_count = len([True for post in user.authored_posts if post.confirmed_for_deployment])
    confirmed_for_insights_count = len([1 for post in user.authored_posts if post.confirmed_for_insights])

    authored_posts_count = len(user.authored_posts) if current_user == user else len(db.session.execute(select(Post).filter_by(private=False)).scalars().all())
    statistics = {
        "publications": authored_posts_count,
        "confirmed_for_deployment": confirmed_for_deployment_count,
        "confirmed_for_insights": confirmed_for_insights_count
    }
    is_this_current_user = current_user.alternative_id == alternative_id
    return render_template(
        "profile.html", 
        user_short_data=user_short_data, 
        post_types=post_types, 
        statistics=statistics,
        is_this_current_user=is_this_current_user
    )
