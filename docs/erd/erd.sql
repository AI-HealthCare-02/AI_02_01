-- MyHealthBuddy ERD SQL
-- 실제 SQLAlchemy 모델 기준으로 작성
-- 생성일: 2026-05-06

CREATE TABLE `users` (
  `id`              INT          PRIMARY KEY AUTO_INCREMENT COMMENT '사용자 고유 식별자',
  `provider`        VARCHAR(20)  NOT NULL DEFAULT 'google'  COMMENT '소셜 로그인 제공자 (현재 google만 지원)',
  `provider_id`     VARCHAR(128) NOT NULL UNIQUE             COMMENT '소셜 로그인 제공자 고유 ID',
  `email`           VARCHAR(255) NULL                        COMMENT '소셜 로그인 시 제공된 이메일',
  `nickname`        VARCHAR(20)  NOT NULL                    COMMENT '서비스 전역 닉네임 (1~20자)',
  `profile_image`   VARCHAR(512) NULL                        COMMENT '프로필 이미지 URL',
  `role`            VARCHAR(10)  NOT NULL DEFAULT 'USER'     COMMENT 'USER / ADMIN',
  `gender`          VARCHAR(1)   NULL                        COMMENT 'M: 남성 / F: 여성 (최초 입력 후 변경 불가)',
  `birth_year`      INT          NULL                        COMMENT '출생 연도 (나이 동적 계산 기준)',
  `character_stage` INT          NOT NULL DEFAULT 0          COMMENT '캐릭터 진화 단계 (0~3)',
  `current_point`   INT          NOT NULL DEFAULT 0          COMMENT '현재 보유 포인트',
  `is_deleted`      BOOLEAN      NOT NULL DEFAULT FALSE      COMMENT '탈퇴 여부 (Soft Delete)',
  `deleted_at`      DATETIME     NULL                        COMMENT '탈퇴 처리 시각',
  `withdraw_reason` VARCHAR(500) NULL                        COMMENT '탈퇴 사유',
  `created_at`      DATETIME     NOT NULL DEFAULT NOW()      COMMENT '계정 생성 시각'
);

CREATE TABLE `health_records` (
  `id`                INT          PRIMARY KEY AUTO_INCREMENT COMMENT '건강검진 기록 ID',
  `user_id`           INT          NULL                        COMMENT 'FK → users (비로그인 사용자는 NULL)',
  `systolic_bp`       INT          NOT NULL                    COMMENT '수축기 혈압 (mmHg)',
  `diastolic_bp`      INT          NOT NULL                    COMMENT '이완기 혈압 (mmHg)',
  `total_cholesterol` INT          NOT NULL                    COMMENT '총 콜레스테롤 (mg/dL)',
  `glucose`           INT          NOT NULL                    COMMENT '혈당 (mg/dL)',
  `height`            DECIMAL(5,1) NOT NULL                    COMMENT '키 (cm)',
  `weight`            DECIMAL(5,1) NOT NULL                    COMMENT '몸무게 (kg)',
  `bmi`               DECIMAL(4,1) NULL                        COMMENT 'BMI 자동 계산',
  `smoke_yn`          BOOLEAN      NOT NULL                    COMMENT '흡연 여부',
  `alcohol_yn`        BOOLEAN      NOT NULL                    COMMENT '음주 여부',
  `exercise_yn`       BOOLEAN      NOT NULL                    COMMENT '규칙적 운동 여부',
  `created_at`        DATETIME     NOT NULL DEFAULT NOW()      COMMENT '입력 시각'
);

CREATE TABLE `prediction_results` (
  `id`               INT          PRIMARY KEY AUTO_INCREMENT                              COMMENT '예측 결과 ID',
  `record_id`        INT          NOT NULL                                                COMMENT 'FK → health_records',
  `trigger_type`     ENUM('new_record', 'challenge_streak', 'manual') NOT NULL           COMMENT '예측 트리거 유형',
  `cvd_risk_percent` DECIMAL(5,2) NOT NULL                                               COMMENT '심혈관 발생 확률 (0~100%)',
  `cvd_age`          INT          NOT NULL                                               COMMENT '심혈관 나이',
  `risk_level`       ENUM('low', 'moderate', 'medium', 'high', 'very_high') NOT NULL    COMMENT '위험도 등급',
  `top_risk_factors` JSON         NULL                                                   COMMENT 'SHAP 기반 위험 요인 상위 3개',
  `ai_evaluation`    TEXT         NULL                                                   COMMENT 'ChatGPT 수치 평가 코멘트',
  `ai_alert`         TEXT         NULL                                                   COMMENT 'ChatGPT 위험 경고 (없으면 NULL)',
  `ai_missions`      JSON         NULL                                                   COMMENT 'ChatGPT 추천 챌린지 3개',
  `ai_encouragement` TEXT         NULL                                                   COMMENT 'ChatGPT 동기부여 문장',
  `created_at`       DATETIME     NOT NULL DEFAULT NOW()                                 COMMENT '생성 시각'
);

CREATE TABLE `challenges` (
  `id`                    INT          PRIMARY KEY AUTO_INCREMENT                          COMMENT '챌린지 ID',
  `category`              ENUM('diet', 'exercise', 'lifestyle') NOT NULL                  COMMENT '챌린지 카테고리',
  `title`                 VARCHAR(100) NOT NULL                                           COMMENT '챌린지 제목',
  `description`           TEXT         NULL                                               COMMENT '챌린지 상세 설명',
  `expected_effect`       TEXT         NULL                                               COMMENT '기대효과',
  `verification_method`   ENUM('checklist', 'input', 'cv') NOT NULL                      COMMENT '인증 방식',
  `target_risk_factors`   VARCHAR(200) NULL                                               COMMENT '대상 위험 요인 (쉼표 구분)',
  `duration_days`         INT          NOT NULL                                           COMMENT '전체 수행 기간 (일)',
  `required_success_days` INT          NOT NULL                                           COMMENT '완료 인정 최소 인증 일수'
);

CREATE TABLE `user_challenges` (
  `id`             INT      PRIMARY KEY AUTO_INCREMENT                                         COMMENT '사용자 챌린지 참여 ID',
  `user_id`        INT      NOT NULL                                                           COMMENT 'FK → users',
  `challenge_id`   INT      NOT NULL                                                           COMMENT 'FK → challenges',
  `status`         ENUM('active', 'completed', 'abandoned', 'failed') NOT NULL                COMMENT '참여 상태',
  `current_streak` INT      NOT NULL DEFAULT 0                                                COMMENT '연속 달성 일수 (7일 시 재예측)',
  `start_date`     DATE     NOT NULL                                                           COMMENT '시작 날짜',
  `completed_at`   DATETIME NULL                                                               COMMENT '완료 시각'
);

CREATE TABLE `challenge_logs` (
  `id`                INT      PRIMARY KEY AUTO_INCREMENT                      COMMENT '인증 기록 ID',
  `user_challenge_id` INT      NOT NULL                                        COMMENT 'FK → user_challenges',
  `log_date`          DATE     NOT NULL                                        COMMENT '인증 날짜',
  `verification_type` ENUM('checklist', 'input', 'cv') NOT NULL               COMMENT '인증 방식',
  `input_value`       VARCHAR(100) NULL                                        COMMENT '수치 입력값 (개피수, 걸음수 등)',
  `cv_result_id`      INT      NULL                                            COMMENT 'FK → cv_analysis_logs (cv 인증 시)',
  `created_at`        DATETIME NOT NULL DEFAULT NOW()                          COMMENT '기록 생성 시각'
);

CREATE TABLE `cv_analysis_logs` (
  `id`            INT          PRIMARY KEY AUTO_INCREMENT                          COMMENT 'CV 분석 결과 ID',
  `user_id`       INT          NOT NULL                                            COMMENT 'FK → users',
  `image_url`     VARCHAR(500) NULL                                                COMMENT '업로드 이미지 경로',
  `analysis_type` ENUM('diet', 'health_checkup', 'exercise') NOT NULL             COMMENT '분석 유형',
  `result_json`   JSON         NULL                                                COMMENT 'GPT Vision API 분석 결과',
  `created_at`    DATETIME     NOT NULL DEFAULT NOW()                              COMMENT '분석 시각'
);

CREATE TABLE `point_logs` (
  `id`         INT      PRIMARY KEY AUTO_INCREMENT                                                                   COMMENT '포인트 변동 ID',
  `user_id`    INT      NOT NULL                                                                                     COMMENT 'FK → users',
  `amount`     INT      NOT NULL                                                                                     COMMENT '양수: 적립 / 음수: 차감',
  `reason`     ENUM('challenge_complete', 'streak_bonus', 'badge_earned', 'diet_report', 'shop_purchase') NOT NULL  COMMENT '변동 사유',
  `created_at` DATETIME NOT NULL DEFAULT NOW()                                                                       COMMENT '변동 시각'
);

CREATE TABLE `friendships` (
  `id`           INT      PRIMARY KEY AUTO_INCREMENT                              COMMENT '친구 요청 ID',
  `requester_id` INT      NOT NULL                                                COMMENT '요청 보낸 사용자',
  `receiver_id`  INT      NOT NULL                                                COMMENT '요청 받은 사용자',
  `status`       ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'BLOCKED') NOT NULL     COMMENT '요청 상태',
  `created_at`   DATETIME NOT NULL DEFAULT NOW()                                  COMMENT '요청 시각',
  UNIQUE KEY `uq_friendships_requester_receiver` (`requester_id`, `receiver_id`)
);

CREATE TABLE `friend_list` (
  `id`         INT      PRIMARY KEY AUTO_INCREMENT COMMENT '친구 목록 ID',
  `user_id`    INT      NOT NULL                   COMMENT '사용자 ID',
  `friend_id`  INT      NOT NULL                   COMMENT '친구 ID',
  `created_at` DATETIME NOT NULL DEFAULT NOW()     COMMENT '친구 확정 시각',
  UNIQUE KEY `uq_friend_list_user_friend` (`user_id`, `friend_id`)
);

-- Foreign Keys
ALTER TABLE `health_records`     ADD FOREIGN KEY (`user_id`)           REFERENCES `users` (`id`);
ALTER TABLE `prediction_results` ADD FOREIGN KEY (`record_id`)         REFERENCES `health_records` (`id`);
ALTER TABLE `user_challenges`    ADD FOREIGN KEY (`user_id`)           REFERENCES `users` (`id`);
ALTER TABLE `user_challenges`    ADD FOREIGN KEY (`challenge_id`)      REFERENCES `challenges` (`id`);
ALTER TABLE `challenge_logs`     ADD FOREIGN KEY (`user_challenge_id`) REFERENCES `user_challenges` (`id`);
ALTER TABLE `challenge_logs`     ADD FOREIGN KEY (`cv_result_id`)      REFERENCES `cv_analysis_logs` (`id`);
ALTER TABLE `cv_analysis_logs`   ADD FOREIGN KEY (`user_id`)           REFERENCES `users` (`id`);
ALTER TABLE `point_logs`         ADD FOREIGN KEY (`user_id`)           REFERENCES `users` (`id`);
ALTER TABLE `friendships`        ADD FOREIGN KEY (`requester_id`)      REFERENCES `users` (`id`);
ALTER TABLE `friendships`        ADD FOREIGN KEY (`receiver_id`)       REFERENCES `users` (`id`);
ALTER TABLE `friend_list`        ADD FOREIGN KEY (`user_id`)           REFERENCES `users` (`id`);
ALTER TABLE `friend_list`        ADD FOREIGN KEY (`friend_id`)         REFERENCES `users` (`id`);
