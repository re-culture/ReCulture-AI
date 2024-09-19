# Python 베이스 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일들을 복사
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# 앱 코드 복사
COPY models.py .
COPY server.py .

# Flask 서버 실행
CMD ["python", "server.py"]