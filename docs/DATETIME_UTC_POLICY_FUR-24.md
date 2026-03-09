# FUR-24 Datetime UTC 일관성 정비

## 1) 전수 조사 결과 (`datetime.now` 혼재 지점)

기준 커맨드:

```bash
rg -n "datetime\\.now\\(" app/src
rg -n "Column\\(DateTime|sa\\.DateTime\\(\\)" app/src/domain alembic/versions
```

### App 코드 기준

| 도메인 | 파일 | 기존 상태 | 우선순위 | 리스크 |
|---|---|---|---|---|
| worker_logs 모니터링 | `app/src/domain/admin/repositories.py` | `datetime.now()` naive | P0 | 모니터링 윈도우 경계 계산 오해석 |
| worker_logs 저장 | `app/src/domain/admin/models.py` | `DateTime`(naive), `datetime.now` | P0 | 장애 분석 시각 해석 불일치 |
| hotdeal timestamp | `app/src/domain/hotdeal/models.py` | `DateTime`(naive), `datetime.now` | P0 | 수집/알림 기준 시각 혼동 |
| hotdeal worker update | `app/worker_main.py` | `datetime.now()` naive | P0 | 최신 앵커 시각 기준 불일치 |
| user login 기록 | `app/src/domain/user/services.py` | `datetime.now()` naive | P1 | 감사/세션 추적 시각 혼동 |
| auth token 만료 | `app/src/core/dependencies/auth.py`, `app/src/domain/user/repositories.py` | 이미 `datetime.now(UTC)` aware | 유지 | 낮음 |

### DB/마이그레이션 기준

다음 컬럼은 기존에 timezone 정보가 없는 타입으로 생성됨:

- `worker_logs.run_at`
- `hotdeal_keywords.wdate`
- `hotdeal_keyword_sites.wdate`
- `mail_logs.sent_at`

## 2) UTC 정책

- 애플리케이션 내부 datetime 생성 기준은 `UTC aware`로 통일한다.
- DB 저장 타입은 `DateTime(timezone=True)`(PostgreSQL `TIMESTAMPTZ`)를 표준으로 한다.
- API 응답 datetime은 offset이 포함된 ISO-8601 형태(`+00:00` 또는 `Z`)로 노출한다.
- 과거 레거시 데이터/드라이버 반환값이 naive인 경우, 응답 직전에 UTC로 정규화한다.

## 3) 마이그레이션 전략 (롤백 가능)

신규 Alembic 리비전: `5ac426a27c8d`

### Upgrade

- 대상 컬럼을 `TIMESTAMP WITHOUT TIME ZONE` -> `TIMESTAMP WITH TIME ZONE`으로 전환
- 변환 시 기존 naive 값은 UTC 기준으로 해석:
  - `USING <column> AT TIME ZONE 'UTC'`

### Downgrade

- 대상 컬럼을 다시 `TIMESTAMP WITH TIME ZONE` -> `TIMESTAMP WITHOUT TIME ZONE`으로 전환
- UTC 기준 wall-clock 값을 유지:
  - `USING <column> AT TIME ZONE 'UTC'`

## 4) 도메인별 적용 결과

- `worker_logs`
  - 모델/조회/모니터링 시각을 UTC aware로 통일
  - 모니터링 응답(`evaluated_at`, `last_success_at`, `last_mail_sent_at`) UTC 정규화
- `hotdeal`
  - `wdate` 컬럼 타입을 timezone-aware로 전환
  - 키워드 응답 스키마에서 UTC 정규화
  - worker의 앵커 갱신 시각을 UTC로 통일
- `user auth token`
  - 토큰 만료 계산 로직은 기존 UTC 유지
  - `last_login` 기록 시각을 UTC aware로 통일

## 5) 운영 배포 전 검증 체크리스트

- [ ] 마이그레이션 전 백업/스냅샷 확보
- [ ] 스테이징에서 `alembic upgrade head` 수행 후 datetime 컬럼 타입 확인
- [ ] 레거시 레코드 조회 시 API datetime이 UTC offset 포함 형태로 응답되는지 확인
- [ ] `worker_logs` 모니터링 알림 임계 계산(window_minutes)이 기존 기대와 동일한지 확인
- [ ] hotdeal 최신 앵커(`hotdeal_keyword_sites.wdate`) 업데이트/조회가 UTC 기준으로 동작하는지 확인
- [ ] 로그인 후 `users.last_login`이 UTC 기준으로 기록되는지 확인
- [ ] 롤백 리허설: `alembic downgrade -1` 및 재업그레이드 성공 확인
