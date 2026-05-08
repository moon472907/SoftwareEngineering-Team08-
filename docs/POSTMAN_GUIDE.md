# Postman 사용 가이드

## 컬렉션 Import 방법

1. Postman 실행
2. 좌측 상단 **Import** 클릭
3. `docs/wiki-api.postman_collection.json` 파일 선택
4. Import 완료 → 좌측 Collections에 **Wiki API** 생성 확인

---

## 기본 사용 흐름

### 1단계 — 회원가입

`Auth > 회원가입` 선택 후 **Send**

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

응답 예시:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-05-04T12:00:00Z"
}
```

---

### 2단계 — 로그인 (토큰 자동 저장)

`Auth > 로그인` 선택 후 **Send**

> 로그인 성공 시 `access_token`이 컬렉션 변수에 **자동 저장**됩니다.  
> 이후 모든 요청에 토큰이 자동으로 포함됩니다.

응답 예시:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 3단계 — 위키 페이지 작성

`Pages > 페이지 작성` 선택 후 **Send**

```json
{
  "title": "파이썬이란",
  "content": "파이썬은 인터프리터 방식의 프로그래밍 언어입니다."
}
```

---

### 4단계 — 페이지 수정 (자동 아카이브)

`Pages > 페이지 수정` 에서 URL의 `1`을 실제 page_id로 변경 후 **Send**

```json
{
  "content": "파이썬은 간결한 문법이 특징인 프로그래밍 언어입니다."
}
```

> 수정 시 이전 내용이 Archive에 자동 저장되고 `version`이 증가합니다.

---

### 5단계 — 수정 이력 확인

`Archives > 페이지 수정 이력 목록` 에서 URL의 `1`을 page_id로 변경 후 **Send**

---

## API 목록

### Auth
| 이름 | Method | URL | 인증 |
|------|--------|-----|------|
| 회원가입 | POST | `/auth/register` | 불필요 |
| 로그인 | POST | `/auth/login` | 불필요 |

### Users
| 이름 | Method | URL | 인증 |
|------|--------|-----|------|
| 내 정보 조회 | GET | `/users/me` | 필요 |
| 내 정보 수정 | PUT | `/users/me` | 필요 |
| 특정 유저 조회 | GET | `/users/{id}` | 필요 |
| 전체 유저 목록 | GET | `/users/` | 관리자 |
| 계정 탈퇴 | DELETE | `/users/{id}` | 본인/관리자 |

### Pages
| 이름 | Method | URL | 인증 |
|------|--------|-----|------|
| 페이지 목록 조회 | GET | `/pages/` | 불필요 |
| 페이지 작성 | POST | `/pages/` | 필요 |
| 페이지 상세 조회 | GET | `/pages/{id}` | 불필요 |
| 페이지 수정 | PUT | `/pages/{id}` | 필요 |
| 페이지 삭제 | DELETE | `/pages/{id}` | 작성자/관리자 |

### Archives
| 이름 | Method | URL | 인증 |
|------|--------|-----|------|
| 수정 이력 목록 | GET | `/pages/{id}/archives/` | 필요 |
| 특정 버전 조회 | GET | `/pages/{id}/archives/{aid}` | 필요 |

---

## URL 변수 설정

컬렉션 변수는 Postman에서 직접 수정할 수 있습니다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `base_url` | `http://localhost:8000` | 서버 주소 |
| `access_token` | (로그인 시 자동 저장) | JWT 토큰 |

변경 방법: 컬렉션 우클릭 → **Edit** → **Variables** 탭

---

## 인증 오류 해결

| 오류 | 원인 | 해결 |
|------|------|------|
| `401 Unauthorized` | 토큰 없음 또는 만료 | `Auth > 로그인` 재실행 |
| `403 Forbidden` | 권한 부족 | 본인 리소스인지 확인 |
| `404 Not Found` | 잘못된 ID | URL의 id 값 확인 |
| `400 Bad Request` | 중복 데이터 | 다른 username/title 사용 |
