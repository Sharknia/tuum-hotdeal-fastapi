# Frontend Improvement Options

> tuum.day 프론트엔드 개선 방안 분석 문서

## 현재 상태 분석

### 구조
```
static/
├── index.html          # 리다이렉트 전용 (login/home으로)
├── login.html          # 로그인 페이지
├── signup.html         # 회원가입 페이지
├── home.html           # 메인 홈 페이지
├── hotdeal.html        # 핫딜 키워드 관리 페이지
├── style.css           # 전역 CSS (797 lines)
├── script.js           # 메인 JS (WebSocket, 채팅 UI)
├── login.js            # 로그인 로직
├── signup.js           # 회원가입 로직
├── favicon.ico
├── vercel.json         # (미사용)
└── js/
    ├── auth.js         # 인증 유틸리티 (API URL 결정, 토큰 관리)
    └── keyword_manager.js  # 키워드 CRUD
```

### 기술 스택
| 항목 | 현재 상태 |
|------|----------|
| **HTML** | Vanilla HTML5 |
| **CSS** | Vanilla CSS with CSS Variables (디자인 토큰 정의됨) |
| **JavaScript** | Vanilla ES6+ (ES Modules 사용) |
| **빌드 도구** | 없음 |
| **패키지 매니저** | 없음 (package.json 없음) |
| **번들러** | 없음 |
| **타입 체크** | 없음 |
| **린터/포매터** | 없음 |

### 긍정적 요소
- CSS Variables로 디자인 토큰 정의됨 (colors, spacing, typography)
- ES Modules 사용 (`import/export`)
- 코드량이 적음 (~1,500 lines total)
- 인증 로직 분리됨 (`auth.js`)

### 개선이 필요한 부분
| 문제 | 영향도 | 설명 |
|------|--------|------|
| **빌드 프로세스 없음** | 높음 | 번들링, 미니파이, 트리쉐이킹 불가 |
| **타입 안전성 없음** | 중간 | 런타임 에러 발생 가능성 |
| **중복 코드** | 중간 | 각 HTML 파일에서 공통 레이아웃 반복 |
| **캐시 버스팅 수동** | 낮음 | `?v=1.0.0` 수동 관리 |
| **HMR 없음** | 낮음 | 개발 시 수동 새로고침 필요 |
| **환경 변수 관리** | 중간 | JS에서 환경 분기 하드코딩 |

---

## 개선 옵션

### Option A: 현재 구조 유지 + 점진적 개선

**개요**: 기존 Vanilla 구조를 유지하면서 도구만 추가

**변경 사항**:
1. `package.json` 추가 (개발 도구용)
2. ESLint + Prettier 설정
3. JSDoc으로 타입 힌팅
4. esbuild로 간단한 번들링 (선택)

**디렉토리 구조**:
```
static/
├── src/              # 소스 파일
│   ├── js/
│   └── css/
├── dist/             # 빌드 결과물 (nginx가 서빙)
├── package.json
├── eslint.config.js
└── build.js          # 간단한 빌드 스크립트
```

**장점**:
- 학습 곡선 거의 없음
- 기존 코드 변경 최소화
- 빠른 적용 가능 (1-2시간)

**단점**:
- 컴포넌트 재사용 여전히 불편
- SPA 라우팅 없음
- 상태 관리 복잡

| 추천도 | 노력 | 리스크 | 유지보수성 |
|--------|------|--------|------------|
| ⭐⭐⭐ (3/5) | 낮음 | 낮음 | 중간 |

---

### Option B: Vite + Vanilla JS/TS (같은 레포)

**개요**: Vite를 빌드 도구로 도입, 기존 JS를 TypeScript로 점진적 마이그레이션

**변경 사항**:
1. `frontend/` 디렉토리 생성
2. Vite 설정 (`vite.config.ts`)
3. TypeScript 도입 (점진적)
4. 기존 CSS 유지, CSS Modules 선택적 사용

**디렉토리 구조**:
```
tuum-hotdeal-fastapi/
├── app/              # FastAPI 백엔드 (기존)
├── frontend/         # 프론트엔드 (신규)
│   ├── src/
│   │   ├── main.ts
│   │   ├── pages/
│   │   │   ├── login.ts
│   │   │   ├── home.ts
│   │   │   └── hotdeal.ts
│   │   ├── components/   # 재사용 컴포넌트
│   │   ├── utils/
│   │   └── styles/
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── static/           # 기존 (deprecate 예정)
└── ...
```

**장점**:
- HMR으로 개발 경험 대폭 개선
- TypeScript로 타입 안전성
- 번들링/미니파이/트리쉐이킹 자동
- 환경 변수 관리 (`import.meta.env`)
- 프레임워크 없이 가볍게 유지

**단점**:
- Vanilla JS/TS는 컴포넌트 재사용이 불편
- SPA 라우팅 직접 구현 필요
- 상태 관리 라이브러리 없음

| 추천도 | 노력 | 리스크 | 유지보수성 |
|--------|------|--------|------------|
| ⭐⭐⭐⭐ (4/5) | 중간 | 낮음 | 높음 |

**예상 소요 시간**: 4-8시간 (마이그레이션)

---

### Option C: Vite + React/Preact (같은 레포)

**개요**: React 또는 Preact를 도입하여 컴포넌트 기반 개발

**변경 사항**:
1. `frontend/` 디렉토리에 React 앱 생성
2. 기존 UI를 컴포넌트로 분리
3. React Router로 SPA 라우팅

**디렉토리 구조**:
```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── HomePage.tsx
│   │   └── HotdealPage.tsx
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── AuthForm.tsx
│   │   └── KeywordList.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useKeywords.ts
│   ├── services/
│   │   └── api.ts
│   └── styles/
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**Preact vs React**:
| 항목 | React | Preact |
|------|-------|--------|
| 번들 크기 | ~40KB | ~3KB |
| API 호환성 | - | React와 거의 동일 |
| 생태계 | 풍부 | React 호환 |
| 추천 | 확장 계획 있으면 | 현재 규모에 적합 |

**장점**:
- 컴포넌트 재사용 용이
- 풍부한 생태계 (UI 라이브러리, 훅 등)
- 상태 관리 쉬움 (useState, useContext, Zustand 등)
- 많은 레퍼런스와 커뮤니티

**단점**:
- 학습 곡선 있음 (React 처음이면)
- 오버엔지니어링 우려 (현재 규모 대비)
- 빌드 시간 증가

| 추천도 | 노력 | 리스크 | 유지보수성 |
|--------|------|--------|------------|
| ⭐⭐⭐⭐ (4/5) | 중간-높음 | 중간 | 높음 |

**예상 소요 시간**: 8-16시간 (완전 재작성)

---

### Option D: Next.js (별도 레포 또는 Monorepo)

**개요**: Next.js로 완전히 분리된 프론트엔드 앱 구축

**변경 사항**:
1. 별도 `tuum-hotdeal-frontend` 레포 생성 (또는 turborepo monorepo)
2. Next.js App Router 사용
3. API Routes로 BFF 패턴 (선택)

**디렉토리 구조 (별도 레포)**:
```
tuum-hotdeal-frontend/
├── app/
│   ├── page.tsx
│   ├── login/
│   │   └── page.tsx
│   ├── hotdeal/
│   │   └── page.tsx
│   └── layout.tsx
├── components/
├── lib/
├── public/
├── package.json
├── next.config.js
└── tailwind.config.js (optional)
```

**장점**:
- SSR/SSG로 SEO 및 초기 로딩 최적화
- 파일 기반 라우팅
- API Routes로 BFF 가능
- 최신 React 기능 (Server Components)
- Vercel 배포 쉬움

**단점**:
- 현재 프로젝트 규모에 비해 과도함
- 별도 배포 파이프라인 필요
- 학습 곡선 높음
- CORS 설정 다시 필요 (별도 도메인 시)

| 추천도 | 노력 | 리스크 | 유지보수성 |
|--------|------|--------|------------|
| ⭐⭐ (2/5) | 높음 | 중간 | 높음 |

**예상 소요 시간**: 16-24시간 (완전 재구축 + 인프라)

---

### Option E: HTMX + Jinja2 (서버 렌더링)

**개요**: FastAPI에서 Jinja2 템플릿 + HTMX로 서버 렌더링

**변경 사항**:
1. FastAPI에 Jinja2 템플릿 추가
2. `templates/` 디렉토리 생성
3. HTMX로 인터랙션 처리

**디렉토리 구조**:
```
app/
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── home.html
│   └── hotdeal.html
├── static/
│   └── styles.css
└── src/
    └── domain/
        └── views/     # HTML 반환 라우터
```

**장점**:
- 번들러/빌드 도구 불필요
- Python 개발자에게 친숙
- SEO 자동 최적화
- 매우 가벼움

**단점**:
- 복잡한 UI 인터랙션에 한계
- 프론트엔드 개발자에게 익숙하지 않음
- React/Vue 대비 생태계 작음

| 추천도 | 노력 | 리스크 | 유지보수성 |
|--------|------|--------|------------|
| ⭐⭐⭐ (3/5) | 낮음 | 낮음 | 중간 |

**예상 소요 시간**: 4-6시간

---

## 최종 권장안

### 프로젝트 목적에 따른 추천

| 목적 | 추천 옵션 | 이유 |
|------|----------|------|
| **학습 목적 유지** | **Option B** (Vite + Vanilla TS) | 프레임워크 없이 모던 도구 체험 |
| **실제 서비스화** | **Option C** (Vite + Preact) | 가벼우면서도 확장 가능 |
| **최소 변경** | **Option A** | 리스크 최소화 |
| **Python 중심** | **Option E** (HTMX) | 백엔드와 통합 |

### 종합 추천: **Option B (Vite + Vanilla TS)**

**이유**:
1. **학습 프로젝트 취지에 부합**: 프레임워크 없이 모던 도구 학습
2. **적절한 노력 대비 효과**: 4-8시간 투자로 개발 경험 대폭 개선
3. **점진적 도입 가능**: TypeScript를 점진적으로 도입
4. **같은 레포 유지**: 배포 파이프라인 변경 최소화
5. **확장성**: 필요 시 React/Preact로 쉽게 전환

---

## 마이그레이션 로드맵 (Option B 선택 시)

### Phase 1: 기반 구축 (2시간)
- [ ] `frontend/` 디렉토리 생성
- [ ] Vite 초기화 (`npm create vite@latest`)
- [ ] TypeScript 설정
- [ ] ESLint + Prettier 설정
- [ ] 기존 CSS 복사

### Phase 2: 코드 마이그레이션 (4시간)
- [ ] `auth.js` → `auth.ts` 변환
- [ ] 각 페이지 JS → TS 변환
- [ ] 환경 변수 정리 (`import.meta.env`)

### Phase 3: 빌드/배포 통합 (2시간)
- [ ] `vite build` → `frontend/dist` 출력
- [ ] nginx 설정 업데이트 (`/var/www/hotdeal` → `frontend/dist`)
- [ ] GitHub Actions 워크플로우 업데이트
- [ ] 기존 `static/` deprecate

### Phase 4: 품질 개선 (선택)
- [ ] 공통 컴포넌트 추출 (Navbar, Footer)
- [ ] API 클라이언트 추상화
- [ ] 에러 핸들링 개선

---

## 참고 자료

- [Vite 공식 문서](https://vitejs.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [Preact 공식 문서](https://preactjs.com/)
- [HTMX 공식 문서](https://htmx.org/)
