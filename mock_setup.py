from typing import List
from flaskr import create_app
from flaskr.database import (
    db,
    Board,
    User,
    PostCategory,
    PostType,
    Representative,
    BoardMember
)


app = create_app()


board: Board


users = [
    ("Albert Einstein", "aeinstein", "aeinstein@gmail.com", "physicist", 146),
    ("Max Planck", "mplanck", "mplanck@gmail.com", "scientist", 167),
    ("Neils Bohr", "nbohr", "nbohr@gmail.com", "scientist", 140),
    ("Isaac Newton", "inewton", "inewton@gmail.com", "scientist", 382),
    ("Oyatillo Axadjonov", "oaxadjonov", "oaxadjonov@gmail.com", "student", 18),
    ("Ravshanbek M.", "mravshanbek", "mravshanbek@gmail.com", "student", 18), 
    ("MuhammadSodiq D.", "dmuhammadsodiq", "dmuhammadsodiq@gmail.com", "student", 18),
    ("Timurbek A.", "atimuberk", "atimuberk@gmail.com", "student", 18), 
    ("Akbar Evatov", "aevatov", "aevatov@gmail.com", "student", 18),
]

passwds = [
    "aeins19",
    "maxpl18",
    "nbhr18",
    "isaanew17",
    "onov21",
    "rnov21",
    "dkov21",
    "atim21",
    "atov21"
]


reg_passwds = passwds[:4]
board_passwds = passwds[7:]
repr_passwds = passwds[4:7]
regular_users = users[:4]
board_members = users[7:]
reprs = users[4:7]


post_types = [
    ("Solution Relations"),
    ("Issue Relations"),
    ("Ideas"),
    ("Issues"),
    ("Solutions")
]

categories = [
    "No Poverty",
    "Health",
    "Education",
    "Climate",
    "Affordable & Clean Energy",
    "Responsible consumption",
    "Economy",
    "Peace, Jutice, and Strong Institutions",
    "Zero Hunger",
    "Life Beow Water",
    "Life on Land",
    "Clean Water and Saniation",
]


def setup() -> None:
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create board
        board = Board()
        board.insert()
        
        # Create roles
            
        fields = ["full_name", "username", "email", "profession", "age"]
        
        # Create users and their specialized types
        
        for user_data_index in range(len(regular_users)):
            user_dict = dict(zip(fields, regular_users[user_data_index]))
            user = User(**user_dict)
            user.set_password(reg_passwds[user_data_index])
            user.insert()


        for repr_data_index in range(len(reprs)):
            repr_dict = dict(zip(fields, reprs[repr_data_index]))
            repr = Representative(**repr_dict)
            repr.set_password(repr_passwds[repr_data_index])
            repr.insert()

        
        for bmember_data_index in range(len(board_members)):
            bmember_dict = dict(zip(fields, board_members[bmember_data_index]))
            bmb = BoardMember(**bmember_dict, board=board)
            bmb.set_password(board_passwds[bmember_data_index])
            bmb.insert()
        

        # Create post types
        for post_type in post_types:
            db_ptype = PostType(name=post_type)
            db_ptype.insert()
            
        # Create categories
        for post_category in categories:
            db_ctype = PostCategory(name=post_category)
            db_ctype.insert()


if __name__ == "__main__":
    setup()
    