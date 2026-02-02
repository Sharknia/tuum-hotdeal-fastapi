# Tuum Hotdeal Service 메모리 안정화 작업 계획 (상세)

> 목적: **메모리 급증으로 인한 서버 다운/재부팅 방지**  
> 원칙: **낮은~중간 복잡도만**, 즉시 효과가 있는 항목 우선
> 기준: **운영 서버 4코어/23Gi RAM/Swap 없음 환경**

---

## 1) 문제 요약
- Playwright 기반 크롤링으로 **피크 메모리 스파이크** 발생
- 로그 폭주로 `journald` 메모리 압박 가능성
- 결과적으로 시스템 불안정 및 재부팅 반복

---

## 2) 목표 (필수)
- **서버 다운/재부팅 0회 유지**
- **Worker 피크 메모리 사용량 안정화**
- **크롤링 성공률 유지**
- **실패 원인/메일 수신자 로그는 유지**

---

## 3) 최소 적용 범위

### 애플리케이션
- `docker-compose.prod.yml` (메모리 제한 실제 적용)
- `app/worker_main.py` (동시성 낮춤)
- `app/src/core/logger.py` 및 관련 로그 호출 (로그량 감소)

### 운영(Host)
- `journald.conf` 설정 (로그 메모리/용량 제한)
- 필요 시 swap 추가 (메모리 스파이크 완충)

---

## 4) 단계별 실행 계획 (필수 최소)

### Phase 0 — **Compose 메모리 제한 적용 (최우선, 저복잡)**
#### 현황
- 현재 `docker-compose.prod.yml`의 `deploy.resources.limits.memory`는 일반 compose에서 무시됨

#### 변경 목표
- **compose 지원 옵션**으로 메모리 제한을 실제 적용
- 워커 컨테이너가 시스템 전체를 잠식하지 못하도록 차단

#### 적용값(서버 4코어/23Gi 기준)
- `worker`
  - `mem_limit: 4g`
  - `mem_reservation: 2g`
- `web`
  - `mem_limit: 1g`
  - `mem_reservation: 256m`

#### 변경 항목
- `docker-compose.prod.yml`
  - `worker` 서비스에 `mem_limit`, `mem_reservation` 추가
  - `web` 서비스에도 제한 추가(트래픽 거의 없음 가정)
  - 기존 `deploy.resources.limits`는 제거 또는 유지 여부 명시

#### 체크포인트
- 컨테이너 재기동 후 `docker stats`로 제한 적용 여부 확인
- 워커 피크 메모리가 제한 내에서 유지되는지 확인

### Phase 1 — **Worker 동시성 즉시 하향 (저복잡)**
#### 현황
- `worker_main.py`에서 세마포어 하드코딩
  - 사이트 세마포어: `asyncio.Semaphore(2)`
  - 키워드 세마포어: `asyncio.Semaphore(5)`

#### 변경 목표
- 피크 메모리/CPU 부하 즉시 감소
- 실패율 급증 없이 안정성 우선

#### 적용값(서버 4코어/23Gi 기준)
- 사이트 동시성: **2 → 1**
- 키워드 동시성: **5 → 2**

#### 변경 항목
- `app/worker_main.py`
  - `site_semaphores = {site: asyncio.Semaphore(1) ...}`
  - `keyword_semaphore = asyncio.Semaphore(2)`

#### 체크포인트
- 워커 1~2회 실행 시 피크 메모리 감소 확인
- 크롤링 성공률이 유지되는지 확인

### Phase 2 — **로그량 감소 (저복잡)**
#### 원칙
- **실패 원인/예외 로그는 유지**
- **메일 수신자 관련 로그는 유지**
- **요청/성공/재시도 등 반복 INFO는 DEBUG로 하향**

#### 하향 대상(예시)
- `BrowserFetcher` 요청/성공/챌린지 재시도
- `BaseCrawler` 요청/성공/브라우저 요청
- `worker_main.py` 키워드 처리 진행/성공 로그

#### 유지 대상(예시)
- 크롤링 실패/예외/차단 관련 ERROR/WARNING
- 메일 발송 대상/완료/실패 로그
- 워커 시작/종료 로그

#### 변경 항목
- `app/src/Infrastructure/crawling/*.py`의 INFO 로그 다수 → DEBUG
- `app/worker_main.py`의 진행 로그 일부 → DEBUG

#### 체크포인트
- 실패 원인 파악 가능 여부 유지
- 메일 수신자 로그가 남는지 확인
- `journald` 메모리 사용량 완화 확인

### Phase 3 — **Host 안전장치 (중복잡이지만 필요)**
#### journald 설정
- `/etc/systemd/journald.conf`에 제한값 지정
  - `SystemMaxUse=` (디스크 상한)
  - `RuntimeMaxUse=` (메모리 상한)
  - `SystemMaxFileSize=` (로그 파일 크기 제한)
  - 적용 후 `systemctl restart systemd-journald`

#### swap 추가(필요 시)
- swap 2~4GiB 추가로 순간 메모리 스파이크 완충
- 커널 `vm.swappiness` 값 조정(낮게 유지)

#### 체크포인트
- journald 메모리 폭주 재발 여부 확인
- swap 사용이 과도하지 않은지 확인

---

## 5) 검증 (필수)
1. `poetry run pytest`
2. `poetry run ruff check .`
3. Worker 1~2회 실행 후:
   - 피크 메모리 확인
   - 크롤링 성공률 확인
   - 시스템 로그에서 watchdog timeout 재발 여부 확인
4. `docker stats`로 컨테이너 제한 적용 확인

---

## 6) 롤백 전략
1. Compose 변경 전 파일 백업
2. 문제 발생 시:
   - 이전 이미지 태그로 롤백
   - Compose 설정 원복
   - 동시성 값 임시로 더 낮춤
   - 로그 레벨 원복

---

## 7) 성공 기준
- 재부팅/응답 불가 **0회 유지**
- Worker 실행 시 피크 메모리 안정화
- watchdog timeout 미발생
- 크롤링 성공률 유지
- 실패 원인 파악 가능 수준의 로그 유지
