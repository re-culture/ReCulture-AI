from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import *

# Load environment variables
load_dotenv()

# DB connection settings
db_host = os.getenv("DATABASE_HOST")
db_name = os.getenv("DATABASE_NAME")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")

# Initialize Flask app
app = Flask(__name__)

# Create database engine and session
engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}')
Session = sessionmaker(bind=engine)
session = Session()


# API endpoint to get records
@app.route("/", methods=["GET"])
def handle_test():
    return "Hello Python Server"


@app.route("/rec", methods=["GET"])
def get_rec():
    ret = session.query(CulturePost).all()
    all_data = [{
        'id': row.id,
        'title': row.title,
        'emoji': row.emoji,
        'date': row.date,
        'categoryId': row.categoryId,
        'authorId': row.authorId,
        'review': row.review,
        'disclosure': row.disclosure,
        'detail1': row.detail1,
        'detail2': row.detail2,
        'detail3': row.detail3,
        'detail4': row.detail4,
        'createdAt': row.createdAt,
        'updatedAt': row.updatedAt
    } for row in ret]
    return jsonify(all_data)


# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
