from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    flash,
    url_for,
    abort
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from flaskr.database import (
        db, User, Post, 
        PostDiscussion, 
        PostComment, 
        PostCategory, PostType
)


posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


@posts_bp.get("/")
@login_required
def ViewPosts():
    author_id = request.args.get("author_id", None)
    post_type_name = request.args.get("post_type", None)
    print(post_type_name)
    post_category_name = request.args.get("post_category", None)
    post_types = []


    if post_type_name:
        post_types = db.session.execute(
            select(PostType).filter_by(name=post_type_name)
        ).scalars().all()

    if post_category_name:
        post_categories = db.session.execute(
            select(PostCategory).filter_by(name=post_category_name)
            .join(Post.post_categories).distinct()
        ).scalars().all()


    base_query = select(Post).distinct()

    if post_type_name:
        base_query = base_query.join(PostType).filter(PostType.name == post_type_name)
    
    if post_category_name:
        base_query = (
            base_query
            .join(Post.post_categories)
            .filter(PostCategory.name == post_category_name)
        )
    
    if author_id and current_user.alternative_id == author_id:
        base_query = base_query.join(Post.original_author).filter(User.alternative_id == current_user.alternative_id)
    elif author_id:
        base_query = base_query.join(Post.original_author).filter(User.alternative_id == author_id).filter(Post.private == False)
    else:
        base_query = base_query.filter(
            (Post.private == False) | (Post.original_author == current_user)
        )

    all_posts = [post.get_public_info(short=True) for post in db.session.execute(base_query).scalars().all()]

    return render_template(
        "post_tmps/posts.html",
        post_type_name=post_type_name,
        post_category_name=post_category_name,
        author=db.session.execute(
            select(User).filter_by(alternative_id=author_id)
        ).scalars().first(),
        all_posts=all_posts
    )



@posts_bp.route("/add-post", methods=("GET", "POST"))
@login_required
def AddPost():
    post_types = [
        p_type.get_info()
        for p_type in db.session.execute(
                            select(PostType)
                    ).scalars().all()
    ]
    post_categories = [
        p_cat.get_info()
        for p_cat in 
        db.session.execute(
            select(PostCategory)
        ).scalars().all()
    ]

    if request.method == "POST":
        title = request.form.get("title", "")
        body = request.form.get("body", "")
        private = request.form.get("private", False)
        if private:
            private = True
        p_type = request.form.get("post_type", None)
        categories = request.form.getlist("post_categories")
        print(p_type)
        print(categories)

        if len(title) < 10 or len(body) < 50:
            flash("Invalid data in either title or body fields. Please keep title length over 6 chars and body length over 50 chars.")
            return redirect(url_for("posts.AddPost"))

        if not p_type or not categories:
            flash("Please select a post type and at least one category.")
            return redirect(url_for("posts.AddPost"))
        
        try:
            post = Post(
                title=title,
                body=body,
                private=private
            )
            post.original_author = current_user


            post_type = db.session.execute(
                select(PostType).filter_by(id=int(p_type))
            ).scalars().first()

            print(post_type)
            post.post_type = post_type


            for category_id in categories:
                category_id = int(category_id)
                post.post_categories.append(
                    db.session.execute(
                        select(PostCategory).filter_by(id=category_id)
                    ).scalars().first()
                )

            post_discussion = PostDiscussion()
            post_discussion.post = post

            db.session.add_all([post, post_discussion])


            db.session.commit()

            flash("Successfully published!")

            return redirect(url_for("posts.ViewPost", post_id=post.alternative_id))

        except SQLAlchemyError:
            flash("Sorry something went wrong. Please, try again.")
            redirect(url_for("posts.AddPost"))

        finally:
            db.session.close()


    return render_template(
        "post_tmps/add_post.html",
        post_types=post_types,
        post_categories=post_categories
    )


@posts_bp.get("/<string:post_id>")
@login_required
def ViewPost(post_id: str):
    post: Post = db.one_or_404(
        db.select(Post).filter_by(alternative_id=post_id)
    )
    
    is_author_viewing = False

    if current_user == post.original_author:
        is_author_viewing = True
    elif post.private:
            abort(404)
    
    comments = [comment.get_info() for comment in post.post_discussion.post_comments]
    


    return render_template(
        "post_tmps/post_detail.html",
        post=post,
        comments=comments,
        is_author_viewing=is_author_viewing
    )


@posts_bp.post("/<string:post_id>/add-comment")
@login_required
def AddComment(post_id: str):
    post: Post = db.one_or_404(
        select(Post).filter_by(alternative_id=post_id)
    )

    body = request.form.get("text", "")
    if len(body) < 30:
        flash("To make discussions meaningful, the minimum character number is 30. Pleasy, try again.")
        return redirect(url_for("posts.ViewPost", post_id=post_id))
    
    try:
        comment = PostComment(text=body)
        comment.post_discussion = post.post_discussion
        comment.author = current_user
        comment.insert()

        return redirect(url_for("posts.ViewPost", post_id=post_id) + f"#comment-{comment.id}")

    except SQLAlchemyError:
        flash("Something went wrong. Please, try again.")
    finally:
        db.session.close()


@posts_bp.get("/<string:post_id>/comments/<int:comment_id>/delete")
@login_required
def DeleteComment(post_id: str, comment_id: int):
    comment: PostComment = db.one_or_404(
        select(PostComment).filter_by(id=comment_id)
    )

    try:
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for("posts.ViewPost", post_id=post_id) + "#text")
    
    except SQLAlchemyError:
        flash("Something went wrong. Try again.")
    finally:
        db.session.close()
