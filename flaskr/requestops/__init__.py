from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    abort
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from flask_login import login_required, current_user
from flaskr.database import (
    db,
    Post,
    User,
    UserRequest,
    Representative,
    RepresentativeRequest,
    Board
)

requests_bp = Blueprint("requests", __name__, url_prefix="/requests")


@requests_bp.route("/")
@login_required
def GetRequests():
    return render_template("requests_tmps/main.html")



@requests_bp.get("/create/<string:req_type>")
@login_required
def CreateRequest(req_type):
    request_caller_type = current_user.type

    print(req_type)

    if req_type == "user_req":
        # if request_caller_type == "representative":
        #     flash("The request cannot be proceeded. Do not try again.")
        #     return redirect(url_for("requests.GetRequests"))       
            
        source_object_id = request.args.get("source_id")
        source_object: Post = db.one_or_404(
            select(Post).filter_by(alternative_id=source_object_id)
        )
        print(source_object)


        all_reprs = db.session.execute(
            select(Representative)
        ).scalars().all()

        incoming_reqs_count = [len(repr.incoming_requests) for repr in all_reprs]
        min_count = min(incoming_reqs_count)

        target_repr: Representative = None
        targets= [
            repr for repr in all_reprs if len(repr.incoming_requests) == min_count
        ]
        for t in targets:
            if t.alternative_id != current_user.alternative_id:
                target_repr = t
                break

        if not target_repr:
            flash("The request cannot be proceeded.")
            return redirect(url_for("posts.ViewPost", post_id=source_object_id))

        try:
            user_request: UserRequest = UserRequest()
            user_request.calling_user = current_user
            user_request.receiving_representative = target_repr
            user_request.request_object = source_object
            user_request.insert()
            return redirect(url_for("requests.GetRequests"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong with request creation.")
            return redirect(url_for("posts.ViewPost", post_id=source_object_id))
        finally:
            db.session.commit()

    elif req_type == "repr_req":
        user_request_id = request.args.get("user_req_id")
        if user_request_id is None or not user_request_id.isdigit():
            abort(404)

        user_request_id = int(user_request_id)
        print(user_request_id)

        user_request = db.one_or_404(
            select(UserRequest).filter(UserRequest.id == user_request_id)
        )

        existing_repr_req = db.session.scalar(
            select(RepresentativeRequest)
            .filter(RepresentativeRequest.calling_user_request_id == user_request.id)
            .limit(1)
        )

        if existing_repr_req:
            flash("The request already exists.")
            return redirect(url_for("requests.GetRequests"))

        all_boards = db.session.execute(select(Board)).scalars().all()
        incoming_reqs_count = [len(board.incoming_requests) for board in all_boards]
        min_count = min(incoming_reqs_count)

        target_board: Board | None = None

        for board in all_boards:
            if len(board.incoming_requests) == min_count:
                target_board = board
                break

        if not target_board:
            flash("The request cannot be proceeded.")
            return redirect(url_for("requests.GetRequests"))

        try:
            representative_request = RepresentativeRequest()
            representative_request.calling_user_request_id = user_request.id  # This sets the ID automatically
            representative_request.representative = user_request.receiving_representative
            representative_request.board = target_board
            user_request.confirmed = True
            db.session.add(representative_request)
            db.session.commit()
            return redirect(url_for("requests.GetRequests"))

        except SQLAlchemyError:
            flash("Something went wrong with representative reqesut creation.")
            return redirect(url_for("requests.GetRequests"))
            db.session.rollback()
        finally:
            db.session.commit()

    else:
        abort(404)
        



@requests_bp.get("/<string:req_type>/<int:req_id>/delete")
def DeleteRequest(req_type, req_id):
    # 
    if req_type == "user_req":
        request_: UserRequest = db.one_or_404(
            db.select(UserRequest).filter_by(id=req_id)
        )
        try:
            db.session.delete(request_)
            db.session.commit()

            flash("Successfully deleted the request")
            return redirect(url_for("requests.GetRequests"))
        
        except SQLAlchemyError:
            flash("something went wrong with deletion.")
            return redirect(url_for("requests.GetRequests"))
        
        finally:
            db.session.close() 

    elif req_type == "repr_req":
        request_: RepresentativeRequest = db.one_or_404(
            select(RepresentativeRequest)
            .filter(RepresentativeRequest.id == req_id)
        )
        user_request: UserRequest = request_.calling_user_request
        try:
            db.session.delete(request_)
            db.session.delete(user_request)
            db.session.commit()
            return redirect(url_for("requests.GetRequests"))
        except SQLAlchemyError:
            flash("Something went wrong with deletion.")
            db.session.rollback()
            return redirect(url_for("requests.GetRequests"))
        finally:
            db.session.close()

    else:
        abort(404)
