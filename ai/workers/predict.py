"""
심혈관 위험도 예측 모듈
ML1: XGBoost + SHAP
"""

import logging
import os

import joblib
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv('ML1_MODEL_PATH', 'ai/models/xgboost_model.pkl')
SCALER_PATH = os.getenv('ML1_SCALER_PATH', 'ai/models/scaler.pkl')

logger.info("모델 로딩 시작 - path: %s", MODEL_PATH)
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
logger.info("모델 로딩 완료")

logger.info("SHAP TreeExplainer 초기화 시작")
explainer = shap.TreeExplainer(model)
logger.info("SHAP TreeExplainer 초기화 완료")

# ── 상수 정의

# 정규화 대상 피처
SCALE_COLS = ['age', 'height', 'weight', 'ap_hi', 'ap_lo', 'bmi']

# 위험 요인 한글 매핑
FACTOR_MAP = {
    'ap_hi': '고혈압',
    'ap_lo': '고혈압',
    'hypertension': '고혈압',        
    'high_cholesterol': '고콜레스테롤', 
    'obesity': '비만',              
    'age_bmi': '고령·과체중',         
    'cholesterol': '고콜레스테롤',
    'gluc': '고혈당',
    'bmi': '과체중',
    'smoke': '흡연',
    'alco': '음주',
    'active': '운동부족',
    'age': '고령',
    'gender': '성별',
    'pulse_pressure': '고혈압',
    'risk_class': '복합위험군',
    'bp_ratio': '고혈압',           # 추가
    'age_hypertension': '고령+고혈압',  # 추가
    'age_cholesterol': '고령+고콜레스테롤',  # 추가
    'age_ap_hi': '고혈압',          # 추가
    'smoke_alco': '흡연+음주',      # 추가
    'age_active': '운동부족',       # 추가
    'bp_bmi': '비만+고혈압',        # 추가
}

# 챌린지 달성 시 보정값 (의학 문헌 기반)
CORRECTION_VALUES = {
    'smoke_7days': {            # 금연 7일 (AHA 2019)
        'ap_hi': -3,
        'ap_lo': -2,
    },
    'alco_7days': {             # 금주 7일 (대한고혈압학회 2021)
        'ap_hi': -2,
        'ap_lo': -1,
    },
    'active_7days': {           # 운동 7일 (한국고혈압학회 2022)
        'ap_hi': -4,
        'ap_lo': -3,
        'bmi': -0.1,
    },
    'diet_7days': {             # 저염식사 7일 (WHO 나트륨 가이드라인)
        'ap_hi': -3,
        'ap_lo': -2,
    }
}


def preprocess(user_data: dict) -> pd.DataFrame:
    df = pd.DataFrame([user_data])

    # BMI 계산
    df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)

    # 맥압 계산
    df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']

    # 나이 × BMI 상호작용
    df['age_bmi'] = df['age'] * df['bmi']

    # 복합 위험군 클래스 생성
    df['hypertension'] = (df['ap_hi'] >= 140).astype(int)
    df['high_cholesterol'] = (df['cholesterol'] >= 2).astype(int)
    df['risk_class'] = (
        df['hypertension'] +
        df['high_cholesterol'] +
        (df['bmi'] >= 30).astype(int) +
        df['smoke'] +
        df['alco']
    )

    # 추가 파생변수
    df['bp_ratio']         = df['ap_hi'] / df['ap_lo']
    df['age_hypertension'] = df['age'] * df['hypertension']
    df['age_cholesterol']  = df['age'] * df['cholesterol']
    df['age_ap_hi']        = df['age'] * df['ap_hi']
    df['smoke_alco']       = df['smoke'] * df['alco']
    df['age_active']       = df['age'] * (1 - df['active'])
    df['bp_bmi']           = df['ap_hi'] * df['bmi']

    # 모델 학습 피처 순서에 맞게 정렬 (18개)
    feature_cols = [
        'age', 'gender', 'height', 'weight',
        'ap_hi', 'ap_lo', 'cholesterol', 'gluc',
        'smoke', 'alco', 'active', 'bmi',
        'hypertension', 'high_cholesterol', 'risk_class',
        'pulse_pressure', 'smoke_alco', 'age_active', 'bp_bmi',
        'bp_ratio', 'age_hypertension', 'age_cholesterol',
        'age_ap_hi', 'age_bmi'
    ]
    df = df[feature_cols]

    # 정규화
    df[SCALE_COLS] = scaler.transform(df[SCALE_COLS])

    return df


def get_risk_grade(risk_percent: float) -> str:
    """위험 등급 반환"""
    if risk_percent <= 10:
        return "낮음"
    elif risk_percent <= 20:
        return "보통"
    elif risk_percent <= 30:
        return "중간"
    elif risk_percent <= 40:
        return "높음"
    else:
        return "매우높음"


def get_character_stage(risk_percent: float) -> int:
    """캐릭터 단계 반환 (1~5)"""
    if risk_percent <= 20:
        return 1   # 건강함
    elif risk_percent <= 40:
        return 2
    elif risk_percent <= 60:
        return 3
    elif risk_percent <= 80:
        return 4
    else:
        return 5   # 위험


def calculate_heart_age(actual_age: int,
                        risk_percent: float) -> int:
    """심혈관 나이 계산"""
    if risk_percent <= 20:
        return actual_age - 3
    elif risk_percent <= 40:
        return actual_age
    elif risk_percent <= 60:
        return actual_age + 3
    elif risk_percent <= 80:
        return actual_age + 7
    else:
        return actual_age + 10


def get_top_risk_factors(df_input: pd.DataFrame,
                         n: int = 3) -> list:
    shap_values = explainer.shap_values(df_input)

    shap_df = pd.DataFrame({
        'feature': df_input.columns.tolist(),
        'shap_value': abs(shap_values[0])
    }).sort_values('shap_value', ascending=False)

    result = []
    seen = set()

    # 전체 피처 돌면서 중복 제거 후 n개 채우기
    for _, row in shap_df.iterrows():
        label = FACTOR_MAP.get(row['feature'], row['feature'])
        if label not in seen:
            seen.add(label)
            result.append(label)
        if len(result) == n:
            break

    return result


def predict(user_data: dict) -> dict:
    """
    심혈관 위험도 예측 메인 함수

    Args:
        user_data: {
            'age': int,
            'gender': int,      # 1=여성, 2=남성
            'height': float,
            'weight': float,
            'ap_hi': int,       # 수축기 혈압
            'ap_lo': int,       # 이완기 혈압
            'cholesterol': int, # 1/2/3
            'gluc': int,        # 1/2/3
            'smoke': int,       # 0/1
            'alco': int,        # 0/1
            'active': int       # 0/1
        }

    Returns:
        {
            'risk_percent': float,
            'heart_age': int,
            'risk_grade': str,
            'character_stage': int,
            'top_risk_factors': list
        }
    """
    # 전처리
    logger.info("전처리 시작")
    df_input = preprocess(user_data)
    logger.info("전처리 완료")

    # 예측 (OMP_NUM_THREADS=1 설정으로 Celery fork 환경 교착 방지)
    logger.info("XGBoost 예측 시작")
    risk_percent = float(
        model.predict_proba(df_input)[0][1] * 100
    )
    logger.info("XGBoost 예측 완료 - risk_percent: %.1f", risk_percent)

    # 결과 조합
    return {
        "risk_percent": round(risk_percent, 1),
        "heart_age": calculate_heart_age(
            user_data['age'], risk_percent
        ),
        "risk_grade": get_risk_grade(risk_percent),
        "character_stage": get_character_stage(risk_percent),
        "top_risk_factors": get_top_risk_factors(df_input)
    }


def recalculate_risk(user_data: dict,
                     completed_challenges: list) -> dict:
    """
    챌린지 달성 후 재예측

    Args:
        user_data: 사용자 건강 데이터
        completed_challenges: ['smoke_7days', 'active_7days']
    """
    adjusted_data = user_data.copy()

    # 보정값 적용
    for challenge in completed_challenges:
        if challenge in CORRECTION_VALUES:
            for feature, delta in CORRECTION_VALUES[challenge].items():
                if feature in adjusted_data:
                    adjusted_data[feature] = max(
                        adjusted_data[feature] + delta, 0
                    )

    # 재예측
    result = predict(adjusted_data)
    result['applied_corrections'] = completed_challenges

    return result


# ── 테스트
if __name__ == '__main__':
    sample = {
        'age': 45,
        'gender': 1,
        'height': 165,
        'weight': 70,
        'ap_hi': 140,
        'ap_lo': 90,
        'cholesterol': 2,
        'gluc': 1,
        'smoke': 1,
        'alco': 0,
        'active': 0
    }

    print("=== 예측 결과 ===")
    result = predict(sample)
    for k, v in result.items():
        print(f"{k}: {v}")

    print("\n=== 금연 7일 달성 후 재예측 ===")
    result2 = recalculate_risk(sample, ['smoke_7days'])
    for k, v in result2.items():
        print(f"{k}: {v}")

    print(f"\n위험도 변화: {result['risk_percent']} → {result2['risk_percent']}%")

    # ── 챌린지 맞춤 추천 함수
RISK_FACTOR_MAP = {
    '고혈압': '고혈압',
    '고령+고혈압': '고혈압',
    '고콜레스테롤': '고콜레스테롤',
    '고령+고콜레스테롤': '고콜레스테롤',
    '고혈당': '고혈당',
    '비만+고혈압': '과체중',
    '고령·과체중': '과체중',
    '흡연': '흡연자',
    '흡연+음주': '음주자',
    '운동부족': '과체중',
}

def recommend_challenges(top_risk_factors: list) -> list:
    """
    top_risk_factors 기반으로 챌린지 추천
    Returns: 매칭된 target_risk_factors 목록
    """
    targets = set()
    for factor in top_risk_factors:
        mapped = RISK_FACTOR_MAP.get(factor)
        if mapped:
            targets.add(mapped)
    targets.add('공통')  # 항상 공통 챌린지 포함
    return list(targets)