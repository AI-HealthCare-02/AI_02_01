"""
심혈관 위험도 예측 모듈
ML1: XGBoost + SHAP
"""

import joblib
import numpy as np
import pandas as pd
import shap

# ── 모델 로드
MODEL_PATH = 'ai/models/xgboost_model.pkl'
SCALER_PATH = 'ai/models/scaler.pkl'

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
explainer = shap.TreeExplainer(model)

# ── 상수 정의

# 정규화 대상 피처
SCALE_COLS = ['age', 'height', 'weight', 'ap_hi', 'ap_lo', 'bmi']

# 위험 요인 한글 매핑
FACTOR_MAP = {
    'ap_hi': '고혈압',
    'ap_lo': '고혈압',
    'cholesterol': '고콜레스테롤',
    'gluc': '고혈당',
    'bmi': '과체중',
    'smoke': '흡연',
    'alco': '음주',
    'active': '운동부족',
    'age': '고령',
    'gender': '성별',
    'risk_class': '복합위험군',
    'pulse_pressure': '고혈압'
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
    """
    사용자 입력 데이터 전처리
    """
    df = pd.DataFrame([user_data])

    # BMI 계산
    df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)

    # 맥압 계산
    df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']

    # 복합 위험군 클래스 생성
    df['hypertension'] = (df['ap_hi'] >= 140).astype(int)
    df['high_cholesterol'] = (df['cholesterol'] >= 2).astype(int)
    df['obesity'] = (df['bmi'] >= 30).astype(int)
    df['risk_class'] = (
        df['hypertension'] +
        df['high_cholesterol'] +
        df['obesity'] +
        df['smoke'] +
        df['alco']
    )

    # 불필요한 컬럼 제거
    df = df.drop(columns=['hypertension', 'high_cholesterol', 'obesity'],
                 errors='ignore')

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
    """SHAP 기반 위험 요인 상위 n개 추출"""
    shap_values = explainer.shap_values(df_input)

    shap_df = pd.DataFrame({
        'feature': df_input.columns.tolist(),
        'shap_value': abs(shap_values[0])
    }).sort_values('shap_value', ascending=False)

    top_features = shap_df.head(n)['feature'].tolist()

    # 중복 제거 (ap_hi, ap_lo 둘 다 고혈압)
    result = []
    seen = set()
    for f in top_features:
        label = FACTOR_MAP.get(f, f)
        if label not in seen:
            seen.add(label)
            result.append(label)

    return result[:n]


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
    df_input = preprocess(user_data)

    # 예측
    risk_percent = float(
        model.predict_proba(df_input)[0][1] * 100
    )

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