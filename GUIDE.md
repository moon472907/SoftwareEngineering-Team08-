# Wiki API 실행 가이드

## 목차
1. [사전 준비](#1-사전-준비)
2. [패키지 설치](#2-패키지-설치)
3. [서버 실행](#3-서버-실행)
4. [API 사용 방법](#4-api-사용-방법)
5. [프로젝트 구조](#5-프로젝트-구조)

---

## 1. 사전 준비

### uv 설치 확인
```powershell
uv --version
```
출력 예시: `uv 0.10.9`

uv가 없다면 공식 사이트(https://docs.astral.sh/uv/)에서 설치하세요.

### 가상환경 생성 (최초 1회)
```powershell
uv venv --python 3.12 .venv
```
- Python 3.12가 없으면 자동으로 다운로드됩니다.
- `.venv` 폴더가 프로젝트 루트에 생성됩니다.

---

## 2. 패키지 설치 (최초 1회)

```powershell
uv pip install --python .venv -r requirements.txt
```

설치되는 주요 패키지:
| 패키지 | 용도 |
|--------|------|
| fastapi | 웹 프레임워크 |
| uvicorn | ASGI 서버 |
| sqlalchemy | ORM (데이터베이스) |
| pydantic | 데이터 검증 |
| python-jose | JWT 토큰 |
| passlib | 비밀번호 해싱 |

---

## 3. 서버 실행

### 방법 A — 가상환경 활성화 후 실행 (권장)

```powershell
# 1. 가상환경 활성화
.venv\Scripts\Activate.ps1

# 2. 서버 실행
uvicorn app.main:app --reload
```

가상환경이 활성화되면 프롬프트 앞에 `(.venv)` 가 붙습니다:
```
(.venv) PS D:\Project\SoftEngineering>
```

### 방법 B — 활성화 없이 바로 실행

```powershell
.venv\Scripts\uvicorn.exe app.main:app --reload
```

### 실행 성공 시 출력 예시

```
INFO:     Will watch for changes in these directories: ['D:\\Project\\SoftEngineering']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 서버 종료
```
Ctrl + C
```

---

## 4. API 사용 방법

서버 실행 후 브라우저에서 아래 주소에 접속하세요.

| 주소 | 설명 |
|------|------|
| http://localhost:8000/docs | Swagger UI — 브라우저에서 직접 API 테스트 가능 |
| http://localhost:8000/redoc | ReDoc — 읽기 편한 API 문서 |
| http://localhost:8000/health | 서버 상태 확인 |

### 기본 사용 흐름

#### 1단계 — 회원가입
```
POST /auth/register
```
```json
{
  "username": "홍길동",
  "email": "hong@example.com",
  "password": "password123"
}
```

#### 2단계 — 로그인 (토큰 발급)
```
POST /auth/login
```
```
username=홍길동
password=password123
```
응답으로 `access_token`을 받습니다.

#### 3단계 — 인증이 필요한 API 호출
Swagger UI에서 우측 상단 **Authorize** 버튼 클릭 후 토큰 입력:
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 4단계 — 위키 페이지 작성
```
POST /pages
```
```json
{
  "title": "파이썬이란",
  "content": "파이썬은 인터프리터 방식의 프로그래밍 언어입니다."
}
```

#### 5단계 — 페이지 수정 (자동으로 아카이브 생성됨)
```
PUT /pages/{page_id}
```
```json
{
  "content": "파이썬은 간결한 문법이 특징인 프로그래밍 언어입니다."
}
```

#### 6단계 — 수정 이력 조회
```
GET /pages/{page_id}/archives
```

---

## 5. 프로젝트 구조

```
SoftEngineering/
├── .env                    # 환경변수 (SECRET_KEY 등)
├── requirements.txt        # 패키지 목록
├── wiki.db                 # SQLite DB (서버 첫 실행 시 자동 생성)
└── app/
    ├── main.py             # 앱 진입점, 라우터 등록
    ├── database.py         # DB 연결 설정
    ├── dependencies.py     # JWT 인증 의존성
    ├── core/
    │   ├── config.py       # 환경변수 로드
    │   └── security.py     # JWT 생성/검증, 비밀번호 해싱
    ├── models/             # SQLAlchemy 테이블 정의
    │   ├── user.py
    │   ├── page.py
    │   └── archive.py
    ├── schemas/            # 요청/응답 데이터 형식 (Pydantic)
    │   ├── user.py
    │   ├── page.py
    │   └── archive.py
    ├── crud/               # 데이터베이스 쿼리 함수
    │   ├── user.py
    │   ├── page.py
    │   └── archive.py
    └── routers/            # API 엔드포인트
        ├── auth.py         # POST /auth/register, POST /auth/login
        ├── users.py        # GET/PUT /users/me, GET /users/{id}
        ├── pages.py        # CRUD /pages
        └── archives.py     # GET /pages/{id}/archives
```

### 엔티티 관계

```
User ──(1:N)──> Page
User ──(1:N)──> Archive
Page ──(1:N)──> Archive

Page 수정 시 → 이전 버전이 Archive에 자동 저장됨
```

---

## 환경변수 설정 (.env)

```env
DATABASE_URL=sqlite:///./wiki.db
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **주의:** 배포 시 `SECRET_KEY`를 반드시 길고 무작위한 값으로 변경하세요.
> 생성 방법: `python -c "import secrets; print(secrets.token_hex(32))"`
