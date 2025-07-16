# 가상환경 생성

python@3.13 -m venv venv

# 가상환경 활성화(윈도우)

source venv/Scripts/activate

# 가상환경 활성화(맥)

source venv/bin/activate

# 패키지 설치

pip install -r requirements.txt

# FastAPI 실행

uvicorn app.main:app --reload

````

### FastAPI 접속
``` bash
# 기본 주소
http://127.0.0.1:8000

# Swagger 주소 (자동 생성)
http://127.0.0.1:8000/docs
````

### 추가 명령어

```bash
# requirements.txt 업데이트
pip freeze > requirements.txt
```

### 추가 사항

- 공동 작업을 위해 임의로 생성한 파일 구조입니다. 편하게 추가/수정/삭제 해주세요!
