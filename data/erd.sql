CREATE TABLE `users` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `provider` varchar(255) COMMENT '소셜 로그인 종류 (kakao, google, naver)',
  `provider_id` varchar(255) COMMENT '소셜 로그인 고유 ID',
  `nickname` varchar(255) COMMENT '서비스 전역에서 사용될 닉네임',
  `role` varchar(255) DEFAULT 'USER' COMMENT '권한 (USER, ADMIN)',
  `character_stage` int DEFAULT 0 COMMENT '캐릭터 진화 단계 (0~3)',
  `current_point` int DEFAULT 0 COMMENT '현재 보유 포인트',
  `created_at` timestamp
);

CREATE TABLE `health_records` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `age` int,
  `gender` varchar(255) COMMENT 'M / F',
  `systolic_bp` int COMMENT '수축기 혈압',
  `diastolic_bp` int COMMENT '이완기 혈압',
  `total_cholesterol` int COMMENT '총 콜레스테롤',
  `fasting_blood_sugar` int COMMENT '공복혈당',
  `height` decimal COMMENT '키 (cm)',
  `weight` decimal COMMENT '몸무게 (kg)',
  `bmi` decimal COMMENT '자동 계산된 BMI',
  `smoke_yn` boolean COMMENT '현재 흡연 여부',
  `alcohol_yn` boolean COMMENT '음주 여부',
  `exercise_yn` boolean COMMENT '규칙적 운동 여부',
  `created_at` timestamp
);

CREATE TABLE `prediction_results` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `record_id` int,
  `trigger_type` varchar(255) COMMENT '예측 발생 원인 (예: INITIAL, 7_DAY_STREAK, MANUAL)',
  `cvd_risk_percent` decimal COMMENT '10년 내 심혈관 질환 발생 확률 (%)',
  `cvd_age` int COMMENT '심혈관 나이',
  `risk_level` varchar(255) COMMENT '위험 등급 (LOW, NORMAL, MODERATE, HIGH, VERY_HIGH)',
  `top_risk_factors` json COMMENT '상위 위험 요인 3개 (예: ["고혈압", "흡연", "비만"])',
  `ai_evaluation` text COMMENT 'Claude API: 수치 평가 코멘트',
  `ai_alert` text COMMENT 'Claude API: 위험 경고 (없으면 null)',
  `ai_missions` json COMMENT 'Claude API: 추천 챌린지 3개',
  `ai_encouragement` text COMMENT 'Claude API: 동기부여 문구',
  `created_at` timestamp
);

CREATE TABLE `challenges` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `category` varchar(255) COMMENT '분류 (BP, SUGAR, SMOKE, ALCOHOL, EXERCISE)',
  `title` varchar(255) COMMENT '챌린지 명 (예: 저염식사 하기, 하루 7천보 걷기)',
  `description` text COMMENT '챌린지 상세 설명'
);

CREATE TABLE `user_challenges` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `challenge_id` int,
  `status` varchar(255) DEFAULT 'IN_PROGRESS' COMMENT '진행상태 (IN_PROGRESS, COMPLETED)',
  `current_streak` int DEFAULT 0 COMMENT '현재 연속 달성 일수',
  `start_date` date,
  `completed_at` timestamp
);

CREATE TABLE `challenge_logs` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_challenge_id` int,
  `log_date` date COMMENT '달성 날짜',
  `created_at` timestamp
);

CREATE TABLE `daily_logs` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `log_date` date COMMENT '기록 날짜',
  `daily_systolic_bp` int COMMENT '오늘 측정한 수축기 혈압 (선택)',
  `daily_diastolic_bp` int COMMENT '오늘 측정한 이완기 혈압 (선택)',
  `daily_blood_sugar` int COMMENT '오늘 측정한 공복혈당 (선택)',
  `smoke_yn` boolean COMMENT '오늘 금연 성공 여부 ✅',
  `alcohol_yn` boolean COMMENT '오늘 금주 성공 여부 ✅',
  `exercise_yn` boolean COMMENT '오늘 운동 완료 여부',
  `steps` int COMMENT '오늘 걸음 수 (선택)',
  `created_at` timestamp
);

CREATE TABLE `badges` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `category` varchar(255) COMMENT '뱃지 분류 (출석, 챌린지 완주, 건강 개선 등)',
  `name` varchar(255) COMMENT '뱃지 이름 (예: 금연 챔피언)',
  `description` text COMMENT '획득 조건',
  `reward_point` int COMMENT '획득 시 지급되는 포인트'
);

CREATE TABLE `user_badges` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `badge_id` int,
  `acquired_at` timestamp
);

CREATE TABLE `point_logs` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `amount` int COMMENT '지급(+) 또는 차감(-) 포인트 양',
  `reason` varchar(255) COMMENT '사유 (예: 7일 연속 달성 보너스, 캐릭터 아이템 구매)',
  `created_at` timestamp
);

CREATE TABLE `friendships` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int,
  `friend_id` int,
  `status` varchar(255) DEFAULT 'PENDING' COMMENT '상태 (PENDING:대기, ACCEPTED:수락, BLOCKED:차단)',
  `created_at` timestamp
);

ALTER TABLE `users` COMMENT = '회원 정보 테이블. 비로그인 사용자의 데이터는 DB에 저장하지 않고 프론트 단에서 처리하므로, 이곳에는 실제 가입된 유저만 존재합니다.';

ALTER TABLE `health_records` COMMENT = '정기 건강검진 수치를 저장하는 테이블 (3~6개월 단위 갱신). ML 예측의 기준 데이터가 됩니다.';

ALTER TABLE `prediction_results` COMMENT = '건강검진 수치(health_records)를 바탕으로 ML1(XGBoost)과 ML2(Claude)가 분석한 결과값. 데일리 체크로 인한 재예측이 발생하므로 하나의 검진 기록에 여러 예측 결과가 쌓입니다.';

ALTER TABLE `challenges` COMMENT = '서비스에서 제공하는 전체 챌린지 마스터(목록) 테이블.';

ALTER TABLE `user_challenges` COMMENT = '한 유저가 동시에 여러 챌린지를 진행할 수 있도록 연결해주는 매핑 테이블.';

ALTER TABLE `challenge_logs` COMMENT = '어떤 유저가 특정 챌린지를 "며칠 날" 성공했는지 하루하루의 도장을 찍어주는 테이블. 달력 뷰(REQ-CHAR-002) 구현 시 필수입니다.';

ALTER TABLE `daily_logs` COMMENT = '당일 데일리 체크리스트 통합 데이터. 백엔드는 이 데이터를 인서트할 때 조건에 맞는 challenge_logs도 함께 생성해야 합니다.';

ALTER TABLE `badges` COMMENT = '총 25종의 뱃지 정보를 담고 있는 마스터 테이블.';

ALTER TABLE `user_badges` COMMENT = '유저가 획득한 뱃지 이력을 관리하는 테이블.';

ALTER TABLE `point_logs` COMMENT = '포인트의 증감 내역(Log)을 모두 기록하여 포인트 추적 및 복구가 가능하게 하는 테이블.';

ALTER TABLE `friendships` COMMENT = '유저 간의 친구 관계를 관리하는 테이블. 친구의 건강 수치는 백엔드 API 단에서 철저히 마스킹(비노출) 처리해야 합니다.';

ALTER TABLE `health_records` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `prediction_results` ADD FOREIGN KEY (`record_id`) REFERENCES `health_records` (`id`);

ALTER TABLE `user_challenges` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_challenges` ADD FOREIGN KEY (`challenge_id`) REFERENCES `challenges` (`id`);

ALTER TABLE `challenge_logs` ADD FOREIGN KEY (`user_challenge_id`) REFERENCES `user_challenges` (`id`);

ALTER TABLE `daily_logs` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_badges` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `user_badges` ADD FOREIGN KEY (`badge_id`) REFERENCES `badges` (`id`);

ALTER TABLE `point_logs` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `friendships` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `friendships` ADD FOREIGN KEY (`friend_id`) REFERENCES `users` (`id`);
