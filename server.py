import redis
from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import *
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import torch.nn.functional as F
import numpy as np


# Load environment variables
load_dotenv()

# DB connection settings
db_host = os.getenv("DATABASE_HOST")
db_name = os.getenv("DATABASE_NAME")
db_user = os.getenv("DATABASE_USER")
db_password = os.getenv("DATABASE_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")

# Initialize Flask app
app = Flask(__name__)

# Create database engine and session
engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}')
Session = sessionmaker(bind=engine)
session = Session()

# Connect redis
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
redis_client.set('test_key', 'test_value')
print(redis_client.get('test_key'))

# Fetch data from the CulturePost table with all necessary columns
def fetch_data_from_db():
    cached_data = redis_client.get('culture_posts')
    if cached_data:
        print("loaded data")
        return eval(cached_data)

    query = session.query(CulturePost).all()
    data = [{
        'id': row.id,
        'title': row.title,
        'emoji': row.emoji,
        'categoryId': row.categoryId,
        'authorId': row.authorId,
        'review': row.review,
        'disclosure': row.disclosure,
        'detail1': row.detail1,
        'detail2': row.detail2,
        'detail3': row.detail3,
        'detail4': row.detail4,
    } for row in query]
    redis_client.set('culture_posts', str(data))
    return data


# Fetch all records written by the current user with all necessary columns
def fetch_user_data_from_db(user_id):
    cached_data = redis_client.get(f'user{user_id}_posts')
    if cached_data:
        print("loaded cached data")
        return eval(cached_data)

    query = session.query(CulturePost).filter_by(authorId=user_id).all()
    user_data = [{
        'id': row.id,
        'title': row.title,
        'emoji': row.emoji,
        'categoryId': row.categoryId,
        'authorId': row.authorId,
        'review': row.review,
        'disclosure': row.disclosure,
        'detail1': row.detail1,
        'detail2': row.detail2,
        'detail3': row.detail3,
        'detail4': row.detail4,
    } for row in query]
    redis_client.set(f'user{user_id}_posts', str(user_data))
    return user_data


# GCN 모델 정의
class GCN(torch.nn.Module):
    def __init__(self):
        super(GCN, self).__init__()
        self.conv1 = GCNConv(500, 16)  # TF-IDF의 max_features = 500
        self.conv2 = GCNConv(16, 16)
        self.conv3 = GCNConv(16, 500)  # 차원 다시 확장

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.conv3(x, edge_index)
        return x


# API endpoint to get records
@app.route("/", methods=["GET"])
def handle_test():
    return "Hello Python Server"


@app.route("/rec", methods=["GET"])
def get_rec():
    data = fetch_data_from_db()
    return jsonify(data)


@app.route("/recommend", methods=["GET"])
def get_recommend():
    data_from_db = fetch_data_from_db()
    df = pd.DataFrame(data_from_db)
    category_name = ["", "영화", "뮤지컬", "연극", "스포츠", "공연", "드라마", "책", "전시"]
    df['category_name'] = df['categoryId'].apply(lambda x: category_name[x])
    df['all_text'] = df['category_name'] + ' ' + df['title'] + ' ' + df['review']

    # TF-IDF 벡터화
    tfidf_vectorizer = TfidfVectorizer(max_features=500)
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['all_text'])

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # 유저 벡터와 전체 그래프 노드를 결합하여 학습 데이터 생성
    def create_combined_graph_data(user_vector, data):
        # 유저 벡터의 크기를 맞춰 2차원으로 변환
        user_node = user_vector.squeeze(0)  # 불필요한 차원 제거

        # 유저 노드를 기존 TF-IDF 매트릭스의 한 노드로 추가
        combined_x = torch.cat([data.x, user_node.unsqueeze(0)], dim=0)

        # 엣지 구성 (유저 노드와 기존 노드 간 유사도 기반 엣지 추가)
        user_edges = [[i, len(data.x)] for i in range(len(data.x))]  # 유저 노드를 새로운 노드로 추가
        user_edge_index = torch.tensor(user_edges, dtype=torch.long).t().contiguous()

        combined_edge_index = torch.cat([data.edge_index, user_edge_index], dim=1)

        return Data(x=combined_x, edge_index=combined_edge_index)

    def train_gnn(data):
        model = GCN()  # GCN 모델 생성
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)  # 옵티마이저 설정

        # 모델 학습 함수 정의
        def train():
            model.train()
            optimizer.zero_grad()
            out = model(data)  # GCN을 통해 노드 임베딩 계산
            loss = F.mse_loss(out, data.x)  # 노드 특징 복원을 위한 MSE Loss
            loss.backward()
            optimizer.step()

        # 학습 반복
        for epoch in range(100):  # 100회 반복 학습
            train()

        return model  # 학습 완료된 모델 반환

    def create_user_profile_vector(user_id):
        # 유저가 작성한 모든 기록을 가져옴
        user_posts = fetch_user_data_from_db(user_id)

        # 카테고리, 제목, 내용을 결합하여 하나의 텍스트로 만듦
        combined_text = ' '.join(
            [category_name[post['categoryId']] + ' ' + post['title'] + ' ' + post['review'] for post in user_posts])
        print(combined_text)

        # 결합된 텍스트를 TF-IDF 벡터화
        user_vector = tfidf_vectorizer.transform([combined_text])

        return torch.tensor(user_vector.toarray(), dtype=torch.float)

    # Create graph data
    # TF-IDF 벡터화된 데이터 사용 (이미 있는 tfidf_matrix와 cosine_sim 사용)
    # 엣지(Edge) 생성 (코사인 유사도에 기반)
    edge_index = torch.tensor([
        [i, j] for i in range(len(cosine_sim)) for j in range(len(cosine_sim)) if cosine_sim[i, j] > 0.5
    ], dtype=torch.long).t().contiguous()

    # TF-IDF 벡터를 노드 특징으로 사용
    x = torch.tensor(tfidf_matrix.toarray(), dtype=torch.float)

    # 그래프 데이터 객체 생성
    data = Data(x=x, edge_index=edge_index)

    # GNN 학습
    trained_model = train_gnn(data)

    user_id = request.args.get('user_id')

    # 유저 프로필 벡터 생성
    user_vector = create_user_profile_vector(user_id)

    # 유저 벡터와 전체 노드 결합한 그래프 데이터 생성
    combined_data = create_combined_graph_data(user_vector, data)

    # GNN 모델로 유저 임베딩 추출
    trained_model.eval()  # 모델 평가 모드
    user_embedding = trained_model(combined_data)

    # 유저 임베딩과 모든 노드 간의 유사도 계산
    user_sim = cosine_similarity(user_embedding[-1].detach().numpy().reshape(1, -1), data.x.detach().numpy())

    # 유사한 순으로 정렬하여 추천
    recommended_indices = np.argsort(-user_sim[0])
    recommendations = df.iloc[recommended_indices]

    return jsonify(recommendations.to_dict(orient='records'))


@app.route("/update-cache", methods=["POST"])
def update_cache():
    user_id = request.args.get('user_id')
    redis_client.delete('culture_posts')
    redis_client.delete(f'user{user_id}_posts')
    data_from_db = fetch_data_from_db()
    redis_client.set('culture_posts', str(data_from_db))
    user_data_from_db = fetch_user_data_from_db(user_id)
    redis_client.set(f'user{user_id}_posts', str(user_data_from_db))
    return jsonify({"status": "cache updated"}), 200


# Run Flask app
if __name__ == "__main__":
    app.run(port=5050, host='0.0.0.0')
