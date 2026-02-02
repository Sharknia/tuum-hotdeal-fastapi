# Host 안전장치 설정 가이드

> 이 가이드는 운영 서버의 journald와 swap 설정을 위한 것입니다.
> 애플리케이션 코드 변경이 없으므로, 서버 관리자가 직접 적용해야 합니다.

## 1) journald 메모리/디스크 제한

### 현재 상태 확인
```bash
# 현재 journald 설정 확인
sudo systemctl show systemd-journald | grep -i "max\|use"

# journald 로그 크기 확인
sudo journalctl --disk-usage
```

### journald.conf 설정
```bash
# 설정 파일 열기
sudo nano /etc/systemd/journald.conf
```

#### 추가/수정할 설정
```ini
# /etc/systemd/journald.conf

# 시스템 전체 로그 최대 크기 (디스크 상한)
SystemMaxUse=500M

# 런타임 중 메모리 상한
RuntimeMaxUse=100M

# 단일 로그 파일 최대 크기
SystemMaxFileSize=50M

# 로그 보관 기간 (선택사항)
MaxRetentionSec=7day
```

### journald 재시작
```bash
# 설정 적용을 위해 journald 재시작
sudo systemctl restart systemd-journald

# 상태 확인
sudo systemctl status systemd-journald
```

### 검증
```bash
# 로그 크기가 제한되었는지 확인
sudo journalctl --disk-usage
```

---

## 2) Swap 추가 (메모리 스파이크 완충)

### 현재 Swap 상태 확인
```bash
# Swap 사용량 확인
free -h

# Swap 파일/파티션 확인
sudo swapon --show
```

**현재 상태:** Swap 없음 (23Gi RAM)

### Swap 추가 방법

#### 방법 A: Swap 파일 생성 (권장)
```bash
# 4GB swap 파일 생성
sudo fallocate -l 4G /swapfile

# 권한 설정 (보안)
sudo chmod 600 /swapfile

# swap 파일로 포맷
sudo mkswap /swapfile

# swap 활성화
sudo swapon /swapfile

# 확인
free -h
sudo swapon --show
```

#### 영구 적용 (재부팅 후에도 유지)
```bash
# /etc/fstab에 swap 파일 추가
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# swappiness 설정 (swap 사용 빈도 조정)
# 값이 낮을수록 swap을 덜 사용함 (0-100, 권장: 10)
sudo sysctl vm.swappiness=10

# 영구 설정
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### 검증
```bash
# Swap 활성화 확인
free -h

# Swap 사용량 모니터링
watch -n 1 'free -h'

# swappiness 값 확인
cat /proc/sys/vm/swappiness
```

---

## 3) 모니터링

### 메모리 사용량 모니터링
```bash
# 실시간 메모리 사용량
watch -n 1 'free -h'

# 프로세스별 메모리 사용량
ps aux --sort=-%mem | head -20

# Docker 컨테이너 메모리 사용량
docker stats
```

### journald 메모리 사용량 확인
```bash
# journald 프로세스 메모리 사용량
ps aux | grep journald

# 로그 크기
sudo journalctl --disk-usage
```

---

## 4) 롤백 방법

### journald 설정 롤백
```bash
# 백업된 설정 파일로 복원
sudo cp /etc/systemd/journald.conf.backup /etc/systemd/journald.conf

# 기본값으로 복원
sudo nano /etc/systemd/journald.conf
# 모든 주석 해제 및 기본값 복원

# 재시작
sudo systemctl restart systemd-journald
```

### Swap 제거
```bash
# swap 비활성화
sudo swapoff /swapfile

# /etc/fstab에서 swap 항목 제거
sudo sed -i '/\/swapfile/d' /etc/fstab

# swap 파일 삭제
sudo rm /swapfile

# swappiness 설정 제거 (선택사항)
sudo sed -i '/vm.swappiness/d' /etc/sysctl.conf
```

---

## 5) 주의사항

1. **Swap 추가 전 반드시 현재 메모리 사용량 확인**
   - 메모리가 부족한 상태에서 swap을 너무 크게 설정하면 성능 저하

2. **journald 설정 변경 시 로그 손실 가능성**
   - SystemMaxUse를 줄이면 이전 로그가 삭제될 수 있음
   - 중요한 로그가 있다면 백업 후 진행

3. **swappiness 값은 서버 상황에 따라 조정**
   - 값이 너무 높으면 성능 저하
   - 값이 너무 낮으면 메모리 부하 시 OOM 발생 가능

4. **모든 변경 사항은 테스트 환경에서 먼저 검증 권장**
