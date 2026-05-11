# SoftwareEngineering-Team08-
# 📖 WikiSystem Project

> 어느 한 분야에 대해 설명하는 문서를 다수의 유저가 작성 및 수정의 반복으로 상호 검증을 통해 완성해 나가는 위키 시스템

---

## 🎯 Vision Statement

**개인 또는 조직이 특정 분야의 지식을 함께 작성하고 검증하며 완성해 나갈 수 있는, 누구나 배포 가능한 위키 플랫폼을 만든다.**

---

## 📌 Project Goals & Scope

### Goals
- 개인이 특정 분야나 정보를 위해 **배포 가능한 위키**를 만들 수 있게 하는 시스템 개발

### Scope

#### ✅ 기본 기능
| 기능 | 설명 |
|------|------|
| 회원 가입 / 로그인 / 계정 관리 | 사용자 인증 및 계정 관련 기능 |
| 글 작성 / 조회 / 수정 / 삭제 | 위키 문서 CRUD |
| 페이지별 링크 시스템 | 문서 간 연결 및 참조 |
| 마크다운 기능 | 마크다운 문법을 이용한 문서 작성 |

#### 🔧 심화 기능
| 기능 | 설명 |
|------|------|
| 동시성 문제 해결 | 다수 유저의 동시 수정 시 충돌 방지 |

---

## 👥 Stakeholders & Users

### Stakeholders
- **위키 운영자** — 시스템을 배포하고 관리하는 주체

### Users
| 역할 | 설명 |
|------|------|
| 📖 독자 | 위키 문서를 조회하는 사용자 |
| ✍️ 작성자 | 위키 문서를 작성하고 수정하는 사용자 |

---

## 🗓️ Milestone

| 주차 | 마일스톤 |
|------|----------|
| 1주차 | 기획 및 설계 |
| 2주차 | 핵심 기능 개발 |
| 3주차 | 핵심 기능 개발 |
| 4주차 | 핵심 기능 개발 |
| 5주차 | 핵심 기능 개발 |
| 6주차 | 핵심 기능 개발 |
| 7주차 | 핵심 기능 개발 |
| 8주차 | 부가 기능 개발 |
| 9주차 | 부가 기능 개발 |
| 10주차 | 부가 기능 개발 |
| 11주차 | 배포 및 발표 준비 |
| 12주차 | 배포 및 발표 준비 |

---

## 🛠 기술 스택

| 분류 | 기술 |
|------|------|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (개발) |
| 인증 | JWT (python-jose) |
| 데이터 검증 | Pydantic v2 |
| 서버 | Uvicorn (ASGI) |
| 패키지 관리 | uv |

---

## 🗂 프로젝트 구조

```
SoftEngineering/
├── .env                        # 환경변수 (SECRET_KEY, DB URL 등)
├── .gitignore
├── requirements.txt            # 패키지 목록
├── GUIDE.md                    # 실행 가이드
│
└── app/
    ├── main.py                 # 앱 진입점 — FastAPI 인스턴스 생성, 라우터 등록, DB 초기화
    ├── database.py             # DB 엔진 및 세션 설정
    ├── dependencies.py         # JWT 인증 의존성 (get_current_user)
    │
    ├── core/
    │   ├── config.py           # 환경변수 로드 (pydantic-settings)
    │   └── security.py         # 비밀번호 해싱, JWT 생성/검증
    │
    ├── models/                 # SQLAlchemy ORM 테이블 정의
    │   ├── user.py             # User 테이블
    │   ├── page.py             # Page 테이블
    │   └── archive.py          # Archive 테이블
    │
    ├── schemas/                # Pydantic 요청/응답 스키마
    │   ├── user.py             # UserCreate, UserResponse, Token
    │   ├── page.py             # PageCreate, PageUpdate, PageResponse
    │   └── archive.py          # ArchiveResponse
    │
    ├── crud/                   # 데이터베이스 쿼리 함수
    │   ├── user.py             # 유저 CRUD + 인증
    │   ├── page.py             # 페이지 CRUD (수정 시 아카이브 자동 생성)
    │   └── archive.py          # 아카이브 조회/생성
    │
    └── routers/                # API 엔드포인트
        ├── auth.py             # 회원가입, 로그인
        ├── users.py            # 유저 조회, 수정, 탈퇴
        ├── pages.py            # 페이지 CRUD
        └── archives.py         # 아카이브 조회
```

---

## 🗄 엔티티 설계

### User (유저)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| username | String(50) | 사용자명 (unique) |
| email | String(255) | 이메일 (unique) |
| hashed_password | String | bcrypt 해시 비밀번호 |
| is_active | Boolean | 활성 여부 (탈퇴 시 false) |
| is_admin | Boolean | 관리자 여부 |
| created_at | DateTime | 가입일 |

### Page (위키 페이지)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| title | String(255) | 페이지 제목 (unique) |
| content | Text | 페이지 본문 |
| author_id | FK → User | 최초 작성자 |
| last_editor_id | FK → User | 마지막 수정자 |
| version | Integer | 현재 버전 번호 |
| is_deleted | Boolean | 삭제 여부 (soft delete) |
| created_at | DateTime | 최초 작성일 |
| updated_at | DateTime | 마지막 수정일 |

### Archive (아카이브)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| page_id | FK → Page | 원본 페이지 |
| editor_id | FK → User | 수정한 유저 |
| title | String | 수정 전 제목 |
| content | Text | 수정 전 본문 |
| version | Integer | 해당 버전 번호 |
| archived_at | DateTime | 아카이브 생성일 |

### 엔티티 관계

```
User ──(1:N)──> Page       (한 유저가 여러 페이지 작성)
User ──(1:N)──> Archive    (한 유저가 여러 수정 이력 보유)
Page ──(1:N)──> Archive    (한 페이지가 여러 버전 이력 보유)
```

> **핵심 동작:** `PUT /pages/{id}` 호출 시 수정 전 내용을 Archive에 자동 저장 후 version을 1 증가시킵니다.

---

## 🔌 API 엔드포인트

### Auth
| Method | URL | 설명 | 인증 |
|--------|-----|------|------|
| POST | `/auth/register` | 회원가입 | 불필요 |
| POST | `/auth/login` | 로그인 (JWT 발급) | 불필요 |

### Users
| Method | URL | 설명 | 인증 |
|--------|-----|------|------|
| GET | `/users/me` | 내 정보 조회 | 필요 |
| PUT | `/users/me` | 내 정보 수정 | 필요 |
| GET | `/users/` | 전체 유저 목록 | 관리자 |
| GET | `/users/{id}` | 특정 유저 조회 | 필요 |
| DELETE | `/users/{id}` | 계정 탈퇴 | 본인/관리자 |

### Pages
| Method | URL | 설명 | 인증 |
|--------|-----|------|------|
| GET | `/pages/` | 페이지 목록 조회 | 불필요 |
| POST | `/pages/` | 페이지 작성 | 필요 |
| GET | `/pages/{id}` | 페이지 상세 조회 | 불필요 |
| PUT | `/pages/{id}` | 페이지 수정 + 자동 아카이브 | 필요 |
| DELETE | `/pages/{id}` | 페이지 삭제 (soft delete) | 작성자/관리자 |

### Archives
| Method | URL | 설명 | 인증 |
|--------|-----|------|------|
| GET | `/pages/{id}/archives/` | 페이지 수정 이력 목록 | 필요 |
| GET | `/pages/{id}/archives/{aid}` | 특정 버전 상세 조회 | 필요 |

---

## 🚀 실행 방법

자세한 실행 방법은 [GUIDE.md](./GUIDE.md)를 참고하세요.

```powershell
# 1. 가상환경 생성 (최초 1회)
uv venv --python 3.12 .venv

# 2. 패키지 설치 (최초 1회)
uv pip install --python .venv -r requirements.txt

# 3. 가상환경 활성화
.venv\Scripts\Activate.ps1

# 4. 서버 실행
uvicorn app.main:app --reload
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI로 API를 테스트할 수 있습니다.

---

## 🔗 GitHub

[![GitHub](https://img.shields.io/badge/GitHub-SoftwareEngineering--Team-181717?style=for-the-badge&logo=github)](https://github.com/moon472907/SoftwareEngineering-Team08-)

👉 https://github.com/moon472907/SoftwareEngineering-Team08-
