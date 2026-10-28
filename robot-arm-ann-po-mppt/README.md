# 로봇팔 기반 ANN–P&O MPPT 



## 프로젝트 소개

캡스톤디자인/졸업논문: **「로봇팔 기반 동적 음영 환경에서 ANN-P&O 하이브리드 MPPT 제어 시스템 구현 및 성능 분석」** (충북대학교 전기공학부, 2026).

고정 광원과 태양광 패널 사이에서 **로봇팔 차광판**을 20°~70° 범위로 이동시키고, MOSFET PWM 전자부하로 패널의 동작점을 조절합니다. 다음 세 가지 방식의 MPPT 제어 성능을 비교하는 실험용 플랫폼입니다.

- **Basic P&O**: 추정전력이 증가하면 PWM 제어 방향을 유지, 감소하면 반전
- **Adaptive P&O**: 추정전력 변화량에 따라 PWM step 크기 조정
- **ANN-P&O**: ANN이 로봇팔 각도와 패널 전압으로 PWM을 예측, P&O가 미세 보정

### 시스템 개요

```text
[고정 광원] → [로봇팔 차광판] → [태양광 패널]
                                  |           ┌→ [전압센서]
                                  └→ [ACS712] → [40Ω] → [IRLZ44N] → 패널(-)
                                                      ↑
                                            Arduino UNO (D9 PWM)
                                                      ↕ USB Serial
                                             Raspberry Pi / Python
                                         CSV 저장·ANN 예측·그래프 분석
```

- 로봇팔 서보: PCA9685 PWM 드라이버
- Arduino UNO: 센서 계측, 서보 각도, MOSFET 제어
- Raspberry Pi: 시리얼 수집, ANN 모델 학습/예측, 분석 및 시각화
- 간이 추정전력 지표: `P_est = (PWM/255) × V² / R` (`R = 40Ω`)

이 지표는 **단순화된 실험용 추정치**로, 실제 패널 출력전력 `V×I`나 DC-DC 변환 효율과 동일하지 않습니다. 실험 범위 밖으로 일반화할 수 없습니다.

## 파일 안내

| 위치 | 역할 |
|---|---|
| `firmware/mppt_reference.ino` | Arduino 참고 펌웨어, 간이 전자부하, 로봇팔 및 3가지 MPPT 모드 |
| `mppt_reference/core.py` | 추정전력 계산, P&O 동작, CSV 메시지 파싱 |
| `scripts/mppt_monitor.py` | Arduino 연결 및 CSV 로깅 |
| `scripts/collect_static_data.py` | 정적 실험 원자료 저장 및 sweep별 Best PWM 추출 |
| `scripts/train_ann_pwm.py` | 정적 실험 Best PWM으로 ANN 모델 학습 |
| `scripts/predict_pwm_test.py` | 저장한 ANN 모델로 추천 PWM 확인 |
| `scripts/dynamic_monitor.py` | 세 제어 모드의 동적 실험 기록, ANN 추천 PWM 전송 |
| `scripts/analyze_dynamic.py` | 평균/최대 추정전력, 진동폭, 평균 PWM 집계 |
| `scripts/visualize_dynamic.py` | 알고리즘별 결과 막대그래프 생성 |
| `data/paper_reported_summary.csv` | **논문 표 5에 기재된 요약값** (원시 측정 데이터 아님) |

## 설치

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

아두이노 쪽은 Arduino IDE에서 `firmware/mppt_reference.ino`를 열고, `Adafruit PWM Servo Driver Library`와 `Adafruit BusIO`를 설치해야 합니다. 전압분압비·전류센서 감도·서보 동작 범위·핀 연결은 **실제 장치에 맞게 검토/보정**하세요.

## 실행 예시

아래는 연결 포트가 `COM3`인 Windows PC 예시입니다. Raspberry Pi에서는 `/dev/ttyACM0` 등의 포트를 사용합니다.

```bash
# 1. Arduino/Pi 시리얼 통신 확인 및 CSV 저장
python scripts/mppt_monitor.py --port COM3 --seconds 15

# 2. 정적 실험: PWM sweep을 수집하고 sweep별 Best PWM 기록
python scripts/collect_static_data.py --port COM3 --seconds 180

# 3. ANN 학습 (수집된 CSV가 있을 때만)
python scripts/train_ann_pwm.py --input data/ann_train_data.csv

# 4. ANN PWM 예측
python scripts/predict_pwm_test.py --angle 50 --voltage 8.6

# 5. 동적 음영 조건에서 알고리즘별 기록
python scripts/dynamic_monitor.py --port COM3 --mode basic --seconds 180
python scripts/dynamic_monitor.py --port COM3 --mode adaptive --seconds 180
python scripts/dynamic_monitor.py --port COM3 --mode ann --seconds 180

# 6. 실험 데이터 분석 및 그림 생성
python scripts/analyze_dynamic.py
python scripts/visualize_dynamic.py

# 논문에 보고된 결과 표로 그림만 그리기 (재현 실험 아님)
python scripts/visualize_dynamic.py --paper-summary
```

**실제 3개 실험은 가능한 동일한 음영·광원·배선 조건에서 수행**해야 비교할 수 있습니다. 안내 코드의 시리얼 메시지 형식, 설정, ANN 예측 적용 주기는 논문에서 완전히 명시되어 있지 않아 참고 구현에서 추가로 정한 것이므로 실제 원본 코드와 다를 수 있습니다.

## 논문에 보고된 성능 결과 (측정값 재생산 아님)

| 방법 | 평균 추정전력(W) | 최대 추정전력(W) | 전력 진동폭(W) | 평균 PWM |
|---|---:|---:|---:|---:|
| Basic P&O | 0.46984 | 0.94187 | 0.80924 | 123.44 |
| Adaptive P&O | 0.50948 | 0.97581 | 0.85007 | 78.80 |
| ANN-P&O | **0.54170** | 0.96210 | **0.76007** | 81.90 |

논문 기준 ANN-P&O 평균 추정전력은 Basic P&O 대비 약 15.3%, Adaptive P&O 대비 약 6.3% 높았습니다. 이 수치는 **실내 제한된 실험 조건에서의 추정전력 비교**이며, 상용 MPPT 변환효율이 15.3% 상승했다는 뜻이 아닙니다.

