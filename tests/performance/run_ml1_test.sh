#!/bin/bash
# ML1 성능 테스트 실행 스크립트
#
# 사용법:
#   bash tests/performance/run_test.sh 1       # Phase 1: 기준 테스트  (10 VU)
#   bash tests/performance/run_test.sh 2       # Phase 2: 부하 테스트  (50 VU)
#   bash tests/performance/run_test.sh 3       # Phase 3: 스트레스 테스트 (100 VU)
#   bash tests/performance/run_test.sh 4       # Phase 4: 스파이크 테스트 (200 VU)
#
# 결과 파일 (tests/performance/reports/ 디렉토리):
#   ml1_phase1_20260422_130000.html            ← 브라우저로 열 수 있는 종합 리포트
#   ml1_phase1_20260422_130000_stats.csv       ← Avg/Min/Max/퍼센타일
#   ml1_phase1_20260422_130000_stats_history.csv ← 시간별 응답시간 추이
#   ml1_phase1_20260422_130000_failures.csv    ← 실패 요청 상세

set -e

PHASE=${1:-1}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="tests/performance/reports"
PREFIX="${REPORT_DIR}/ml1_phase${PHASE}_${TIMESTAMP}"

mkdir -p "$REPORT_DIR"

echo "========================================"
echo " ML1 Phase ${PHASE} 테스트 시작"
echo " 시각: ${TIMESTAMP}"
echo " 리포트: ${PREFIX}"
echo "========================================"

# 캐시 포화 방지: 3개 필드(weight×systolic_bp×diastolic_bp) 랜덤화로 ~2,067만 가지 조합 생성
# → 운영 서버 Redis를 직접 초기화하지 않아도 테스트 중 포화 불가
echo ""
echo "[1/1] Locust 실행 중..."
echo "      브라우저에서 http://localhost:8089 접속 후 VU 설정"
echo ""
echo "  Phase 1 (기준)    : Number of users=10,  Spawn rate=1"
echo "  Phase 2 (부하)    : Number of users=50,  Spawn rate=5"
echo "  Phase 3 (스트레스): Number of users=100, Spawn rate=10"
echo "  Phase 4 (스파이크): Number of users=200, Spawn rate=50"
# TODO: Celery 증설 이후 테스트 적용 예정
echo "  Phase 5 (스트레스): Number of users=300, Spawn rate=50"
echo "  Phase 6 (스트레스): Number of users=500, Spawn rate=50"
echo ""

uv run locust \
    -f tests/performance/ml1_scenario.py \
    --html "${PREFIX}.html" \
    --csv "${PREFIX}"

echo ""
echo "========================================"
echo " 테스트 완료"
echo " HTML 리포트: ${PREFIX}.html"
echo " CSV 통계   : ${PREFIX}_stats.csv"
echo "========================================"
