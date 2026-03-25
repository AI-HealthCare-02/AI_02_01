# 데이터셋 설명

## 사용 데이터셋

### Cardiovascular Disease Dataset
- **출처**: Kaggle
- **링크**: https://www.kaggle.com/datasets/sulianova/cardiovascular-disease-dataset
- **파일명**: cardio_train.csv
- **샘플 수**: 70,000명
- **라이선스**: CC0 Public Domain (자유롭게 사용 가능)

---

## 피처 설명

| 피처 | 한글명 | 타입 | 설명 |
|---|---|---|---|
| age | 나이 | int | 일(day) 단위 → 세로 변환 필요 (age / 365) |
| gender | 성별 | int | 1=여성, 2=남성 |
| height | 키 | int | cm |
| weight | float | 몸무게 | kg |
| ap_hi | 수축기 혈압 | int | 윗 혈압 (mmHg) |
| ap_lo | 이완기 혈압 | int | 아랫 혈압 (mmHg) |
| cholesterol | 콜레스테롤 | int | 1=정상, 2=경계, 3=높음 |
| gluc | 혈당 | int | 1=정상, 2=경계, 3=높음 |
| smoke | 흡연 여부 | int | 0=비흡연, 1=흡연 |
| alco | 음주 여부 | int | 0=비음주, 1=음주 |
| active | 운동 여부 | int | 0=비활동, 1=활동 |
| cardio | 심혈관 질환 | int | 0=정상, 1=질환 **(타겟 변수)** |

---

## 서비스 입력 항목 ↔ 피처 매핑

| 서비스 입력 항목 | 데이터셋 피처 |
|---|---|
| 나이 | age |
| 성별 | gender |
| 수축기 혈압 | ap_hi |
| 이완기 혈압 | ap_lo |
| 총 콜레스테롤 | cholesterol |
| 공복혈당 | gluc |
| 키 / 몸무게 | height / weight |
| BMI (자동 계산) | 파생 변수 (weight / (height/100)²) |
| 흡연 여부 | smoke |
| 음주 여부 | alco |
| 운동 여부 | active |

---

## 데이터 파일 위치
```
data/
├── README.md         ← 현재 파일
└── cardio_train.csv  ← 원본 데이터 (Git에 올리지 않음)
```

## 주의사항
- `cardio_train.csv`는 용량이 크므로 `.gitignore`에 추가되어 있음
- 데이터는 위 Kaggle 링크에서 직접 다운로드 후 `data/` 폴더에 넣기