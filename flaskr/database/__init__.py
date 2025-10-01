from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from flask_sqlalchemy import (
    SQLAlchemy
)
from sqlalchemy import (
    Integer,
    String,
    Table,
    Column,
    ForeignKey,
    DateTime,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    declared_attr
)
import uuid


class Base(DeclarativeBase):

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()


db = SQLAlchemy(model_class=Base)


class Board(db.Model):
    __tablename__ = "board_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    established_at: Mapped[datetime] = mapped_column(
            DateTime, 
            default=lambda: datetime.now(timezone.utc)
    )

    members: Mapped[List[BoardMember]] = relationship(back_populates="board")
    # TODO: 
    incoming_requests: Mapped[List[RepresentativeRequest]] = relationship(
            back_populates="board")



# class Role(db.Model):
#     __tablename__ = "role_table"

#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(20))
#     users: Mapped[List[User]] = relationship(back_populates="role")


#     def __repr__(self):
#         return f"<Role:{self.id}> {self.name}"   

# Comment ^ --> is removed as it is redundant

post_user_association_table = Table(
    "post_user_association_table",
    db.metadata,
    Column("user_id", ForeignKey("user_table.id")),
    Column("post_id", ForeignKey("post_table.id")),
)

# User table is in many-to-one relationship with Role table 
# TODO: deletion requests

post_contributed_authors = Table(
    "post_contributed_authors_table",
    db.metadata,
    Column("user_id", ForeignKey("user_table.id")),
    Column("post_id", ForeignKey("post_table.id")),
)


class User(UserMixin, db.Model):
    __tablename__ = "user_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    alternative_id: Mapped[str] = mapped_column(default=lambda: str(uuid.uuid4()))

    full_name: Mapped[str] = mapped_column(String(40))
    username: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str] = mapped_column(String(50), unique=True)
    profession: Mapped[str] = mapped_column(String(30))
    age: Mapped[Optional[int]]
    password_hash: Mapped[str] = mapped_column(String)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )

    authored_posts: Mapped[List[Post]] = relationship(
        back_populates="original_author"
    )

    contributed_posts: Mapped[List[Post]] = relationship(
        secondary=post_contributed_authors,
        back_populates="contributing_authors"
    )

    post_comments: Mapped[List[PostComment]] = relationship(back_populates="author")
    requests: Mapped[List[UserRequest]] = relationship(back_populates="calling_user")

    type: Mapped[str]


    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": "type",
    }


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self. password_hash, password)

    def get_id(self):
        return self.alternative_id

    def get_public_info(self):
        return {
            "full_name": self.full_name,
            "username": self.username,
            "profession": self.profession,
            "posts": self.posts
        }
    
    def get_short_info(self):
        return {
            "full_name": self.full_name, 
            "username": self.username, 
            "alternative_id": self.alternative_id
        }

    def __repr__(self):
        return f"<User:{self.id}> @{self.username}"


class BoardMember(User):
    __tablename__ = "board_member_table"

    id: Mapped[int] = mapped_column(ForeignKey("user_table.id"), primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("board_table.id"))
    board: Mapped[Board] = relationship(back_populates="members")
    board_comments: Mapped[List[BoardDiscussionComment]] = relationship(back_populates="author")

    __mapper_args__ = {
        "polymorphic_identity": "board_member"
    }



class Representative(User):
    __tablename__ = "representative_table"
    id: Mapped[int] = mapped_column(ForeignKey("user_table.id"), primary_key=True)
    incoming_requests: Mapped[List[UserRequest]] = relationship(back_populates="receiving_representative")
    repr_requests: Mapped[List[RepresentativeRequest]] = relationship(back_populates="representative")

    # TODO: requests relationship: Done
    inserted_insights: Mapped[Insight] = relationship(back_populates="inserting_representative")

    __mapper_args__ = {
        "polymorphic_identity": "representative"
    }



class Request(db.Model):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    confirmed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)



class UserRequest(Request):
    __tablename__ = "user_request_table"

    calling_user_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"))
    calling_user: Mapped[User] = relationship(back_populates="requests")
    receiving_representative_id: Mapped[int] = mapped_column(ForeignKey("representative_table.id"))
    receiving_representative: Mapped[Representative] = relationship(
        back_populates="incoming_requests",
        foreign_keys=[receiving_representative_id]
    )

    request_object: Mapped[Post] = relationship(back_populates="outgoing_request")
    linked_repr_request: Mapped[RepresentativeRequest] = relationship(back_populates="calling_user_request")



class RepresentativeRequest(Request):
    __tablename__ = "representative_request"

    calling_user_request_id: Mapped[int] = mapped_column(ForeignKey("user_request_table.id"))
    calling_user_request: Mapped[UserRequest] = relationship(back_populates="linked_repr_request")
    representative_id: Mapped[int] = mapped_column(ForeignKey("representative_table.id"))
    representative: Mapped[Representative] = relationship(back_populates="repr_requests")
    board_id: Mapped[int] = mapped_column(ForeignKey("board_table.id"))
    board: Mapped[Board] = relationship(back_populates="incoming_requests")

    __table_args__ = (
        UniqueConstraint("calling_user_request_id", "representative_id", name="user_req_repr_id_uniq"),
    )



class PostType(db.Model):
    __tablename__ = "post_type_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    posts: Mapped[List[Post]] = relationship(back_populates="post_type")

    def get_info(self):
        return {
            "id": self.id,
            "name": self.name
        }

post_category_association_table = Table(
    "post_category_association_table",
    db.metadata,
    Column("post_category_id", ForeignKey("post_category_table.id")),
    Column("post_id", ForeignKey("post_table.id")),
)


class PostCategory(db.Model):
    __tablename__ = "post_category_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))    
    posts: Mapped[List[Post]] = relationship(
        secondary=post_category_association_table,
        back_populates="post_categories"
    )


    def get_info(self):
        return {
            "id": self.id,
            "name": self.name,
            "posts": [
                post.get_public_info(short=True)
                for post in self.posts
            ]
        }


post_to_post_association_table = Table(
    "post_to_post_association_table",
    db.metadata,
    Column("post_id", ForeignKey("post_table.id")),
    Column("linked_post_id", ForeignKey("post_table.id"))
)

# Post table is in many-to-one relationship with PostType table



class Post(db.Model):
    __tablename__ = "post_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    alternative_id: Mapped[str] = mapped_column(default=lambda: str(uuid.uuid4()))

    title: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(Text)
    upvotes: Mapped[int] = mapped_column(default=0)
    private: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # BAD:
    confirmed_for_deployment: Mapped[bool] = mapped_column(default=False)
    confirmed_for_insights: Mapped[bool] = mapped_column(default=False)

    original_author_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"))
    original_author: Mapped[User] = relationship(
        back_populates="authored_posts",
        foreign_keys=[original_author_id]
    )

    contributing_authors: Mapped[List[User]] = relationship(
        secondary=post_contributed_authors,
        back_populates="contributed_posts"
    )

    post_type_id: Mapped[int] = mapped_column(ForeignKey("post_type_table.id"))
    post_type: Mapped[PostType] = relationship(back_populates="posts")
    
    post_categories: Mapped[List[PostCategory]] = relationship(
        secondary=post_category_association_table,
        back_populates="posts"
    )

    post_discussion: Mapped[PostDiscussion] = relationship(back_populates="post")

    linked_posts: Mapped[List[Post]] = relationship(
        secondary=post_to_post_association_table,
        primaryjoin=id == post_to_post_association_table.c.post_id,
        secondaryjoin=id == post_to_post_association_table.c.linked_post_id,
        back_populates="linked_to"
    )

    linked_to: Mapped[List[Post]] = relationship(
        secondary=post_to_post_association_table,
        primaryjoin=id == post_to_post_association_table.c.linked_post_id,
        secondaryjoin=id == post_to_post_association_table.c.post_id,
        back_populates="linked_posts"
    )

    insights: Mapped[List[Insight]] = relationship(back_populates="source_post")

    outgoing_requet_id: Mapped[int] = mapped_column(ForeignKey("user_request_table.id"), nullable=True)
    outgoing_request: Mapped[UserRequest] = relationship(back_populates="request_object")



    def get_public_info(self, short=False):

        response = {
            "alternative_id": self.alternative_id,
            "title": self.title,
            "original_author": self.original_author.get_short_info(),
            "post_type": self.post_type.name,
            "confirmed_for_deployment": self.confirmed_for_deployment,
            "confirmed_for_insights": self.confirmed_for_insights,
            "post_categories": [category.name for category in self.post_categories],
            "posted_at": self.created_at
        }

        if short:
            response["body"] = self.body[:50]
        else:
            response["body"] = self.body
            response["upvotes"] = self.upvotes
            response["discussion_comments"] = [comment.get_info() for comment in self.post_discussion.post_comments]
            response["authors"] = [
                author.get_short_info()
                for author in self.contributing_authors
            ],

        return response

class Discussion(db.Model):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class PostDiscussion(Discussion):
    __tablename__ = "discussion_table"

    post_id: Mapped[int] = mapped_column(ForeignKey("post_table.id"))
    post: Mapped[Post] = relationship(back_populates="post_discussion")
    post_comments: Mapped[List[PostComment]] = relationship(back_populates="post_discussion")


class BoardDiscussion(Discussion):
    __tablename__ = "board_discussion_table"

    topic: Mapped[str] = mapped_column(Text)
    board_discussion_comments: Mapped[List[BoardDiscussionComment]] = relationship(back_populates="board_discussion")


class Comment(db.Model):
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)


    @declared_attr
    def author_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("user_table.id"))

    @declared_attr
    def author(cls) -> Mapped[User]:
        return relationship(back_populates="post_comments")
    

    def get_info(self):
        return {
            "id": self.id,
            "text": self.text,
            "upvotes": self.upvotes,
            "author": self.author.get_short_info()
        }


class PostComment(Comment):
    __tablename__ = "post_comment"

    post_discussion_id: Mapped[int] = mapped_column(ForeignKey("discussion_table.id"))
    post_discussion: Mapped[PostDiscussion] = relationship(back_populates="post_comments")


class BoardDiscussionComment(Comment):
    __tablename__ = "board_discussion_comment"


    author: Mapped[BoardMember] = relationship(back_populates="board_comments")

    board_discussion_id: Mapped[int] = mapped_column(ForeignKey("board_discussion_table.id"))
    board_discussion: Mapped[BoardDiscussion] = relationship(back_populates="board_discussion_comments")


class Insight(db.Model):
    __tablename__ = "insights_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ai_tuned_text: Mapped[str] = mapped_column(Text)


    # TODO: representatives can put things into insights, not all people
    inserting_representative_id: Mapped[int] = mapped_column(ForeignKey("representative_table.id"))
    inserting_representative: Mapped[Representative] = relationship(back_populates="inserted_insights")

    source_post_id: Mapped[int] = mapped_column(ForeignKey("post_table.id"))
    source_post: Mapped[Post] = relationship(back_populates="insights")


