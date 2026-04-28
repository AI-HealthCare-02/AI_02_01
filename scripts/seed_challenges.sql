-- 챌린지 시드 데이터
-- 실행 전: challenge_logs, user_challenges 의존 데이터도 초기화됨에 주의

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE challenge_logs;
TRUNCATE TABLE user_challenges;
TRUNCATE TABLE challenges;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO challenges (category, title, description, expected_effect, verification_method, target_risk_factors, duration_days, required_success_days) VALUES
('diet',      '저염식사',        '오늘 하루 나트륨 2,000mg 이하로 줄여보세요',        '7일 지속 시 수축기 혈압 3mmHg 감소',              'checklist', '고혈압',         7,  5),
('diet',      '포화지방 줄이기', '삼겹살, 버터 대신 생선과 견과류로 바꿔보세요',      '꾸준히 실천하면 나쁜 콜레스테롤 수치 개선',      'checklist', '고콜레스테롤',   7,  5),
('diet',      '당류 줄이기',     '음료수, 과자 대신 과일로 당 섭취를 줄여보세요',    '꾸준히 실천하면 공복혈당 수치 안정화',            'checklist', '고혈당',         7,  5),
('diet',      '야식 금지',       '저녁 9시 이후에는 아무것도 먹지 않아요',           '꾸준히 실천하면 체중 감소 및 BMI 개선',           'checklist', '과체중 (BMI 25+)', 7, 5),
('exercise',  '유산소 운동 20분','빠르게 걷기, 자전거, 뛰기 20분 움직여보세요',      '7일 지속 시 혈압 4mmHg 감소, BMI 0.2 개선',      'cv',        '고혈압,과체중',  7,  5),
('exercise',  '하루 7,000보',    '만보기 앱으로 오늘 7,000보를 채워보세요',          '꾸준히 실천하면 콜레스테롤 수치 개선',            'cv',        '고콜레스테롤',   7,  5),
('exercise',  '식후 15분 걷기',  '밥 먹고 15분만 천천히 걸어보세요',                '꾸준히 실천하면 식후 혈당 스파이크 완화',         'checklist', '고혈당',         7,  5),
('lifestyle', '물 2L 마시기',    '하루 8잔의 물로 혈액 순환을 도와주세요',           '충분한 수분 섭취 시 심혈관 질환 발생률 감소',     'checklist', '공통',           7,  5),
('lifestyle', '금연 (단계별)',   '오늘 피운 담배 개비 수를 입력해주세요',            '완전 금연 시 심혈관 위험도 30% 감소',             'input',     '흡연자',         30, 21),
('lifestyle', '금주 (단계별)',   '이번 주 음주 횟수를 기록해주세요',                 '완전 금주 시 혈압 및 심혈관 위험도 개선',         'input',     '음주자',         30, 21);
