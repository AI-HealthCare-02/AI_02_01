#!/bin/bash
# ML2 Vision 성능 테스트 실행 스크립트
#
# 사용법:
#   export ML2_TEST_TOKEN="eyJ..."          # JWT 토큰 설정 (필수)
#   bash tests/performance/run_ml2_test.sh 1  # Phase 1: 기준  (5 VU)
#   bash tests/performance/run_ml2_test.sh 2  # Phase 2: 부하  (20 VU)
#   bash tests/performance/run_ml2_test.sh 3  # Phase 3: 스트레스 (50 VU)
#   bash tests/performance/run_ml2_test.sh 4  # Phase 4: 스파이크 (100 VU)
#
# ML1과의 차이:
#   - ML2는 JWT 토큰 필수 (ML2_TEST_TOKEN 환경변수)
#   - ML2는 Redis 캐시 없음 → 동일 이미지라도 매번 ChatGPT Vision API 호출
#   - ML2는 처리 시간이 길어 (10~25초) ML1보다 낮은 VU로 시작
#
# 결과 파일 (tests/performance/reports/ 디렉토리):
#   ml2_phase1_20260422_130000.html            ← 브라우저로 열 수 있는 종합 리포트
#   ml2_phase1_20260422_130000_stats.csv       ← Avg/Min/Max/퍼센타일

set -e

PHASE=${1:-1}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="tests/performance/reports"
PREFIX="${REPORT_DIR}/ml2_phase${PHASE}_${TIMESTAMP}"

mkdir -p "$REPORT_DIR"

echo "========================================"
echo " ML2 Vision Phase ${PHASE} 테스트 시작"
echo " 시각: ${TIMESTAMP}"
echo " 리포트: ${PREFIX}"
echo "========================================"

# JWT 토큰 확인
echo ""
if [ -z "$ML2_TEST_TOKEN" ]; then
    echo "[경고] ML2_TEST_TOKEN 미설정"
    echo "       모든 태스크가 스킵되어 의미 있는 테스트가 불가능합니다."
    echo ""
    echo "  토큰 발급 방법:"
    echo "    uv run python scripts/gen_token.py --user-id 1"
    echo "    export ML2_TEST_TOKEN='eyJ...'"
    echo ""
    read -p "  그래도 계속하시겠습니까? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "테스트를 중단합니다."
        exit 1
    fi
else
    echo "[확인] ML2_TEST_TOKEN 설정됨 → 모든 태스크 활성화"
fi

# ML2는 Redis 캐시 없음 → 별도 캐시 초기화 불필요
echo ""
echo "[안내] ML2는 Redis 캐시 없음 → 캐시 초기화 불필요"
echo "       동일 이미지 반복 전송 시에도 매번 새 ChatGPT Vision API 호출 발생"
echo ""
echo "[Locust 실행 중]"
echo "  브라우저에서 http://localhost:8089 접속 후 VU 설정"
echo ""
echo "  Phase 1 (기준)    : Number of users=5,   Spawn rate=1"
echo "  Phase 2 (부하)    : Number of users=20,  Spawn rate=2"
echo "  Phase 3 (스트레스): Number of users=50,  Spawn rate=5"
echo "  Phase 4 (스파이크): Number of users=100, Spawn rate=10"
echo ""

uv run locust \
    -f tests/performance/ml2_scenario.py \
    --html "${PREFIX}.html" \
    --csv "${PREFIX}"

echo ""
echo "========================================"
echo " 테스트 완료"
echo " HTML 리포트: ${PREFIX}.html"
echo " CSV 통계   : ${PREFIX}_stats.csv"
echo "========================================"
