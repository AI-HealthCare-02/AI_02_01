import { useNavigate } from "react-router-dom";
import "./HeroSection.css";

export default function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-text">
          <p className="hero-badge">심혈관 질환 예방을 위한 AI 건강관리</p>

          <h1 className="hero-title">
            내 건강을
            <br />
            함께 만들어가는
            <br />
            <span className="highlight">친구</span>
          </h1>

          <p className="hero-description">
            건강검진 수치를 바탕으로 심혈관 위험 신호를 분석하고,
            챌린지와 식단 피드백으로 더 건강한 일상을 만들어가는
            나만의 건강 친구가 되어드립니다.
          </p>

          <div className="hero-buttons">
            <button
              className="hero-primary-btn"
              onClick={() => navigate("/health-input")}
            >
              건강 분석 시작하기
            </button>
          </div>

          <p className="hero-note">무료 · 카드 등록 불필요 · 1분 분석</p>
        </div>

        <div className="hero-card">
          <div className="hero-card-header">
            <div className="hero-avatar">🐹</div>

            <div className="hero-card-header-text">
              <p className="hero-card-title">Buddy 님의 심혈관 상태</p>
              <p className="hero-card-subtitle">건강검진 기반 AI 예측 결과</p>
            </div>
          </div>

          <div className="hero-status-banner">
            <div className="hero-status-left">
              <span className="hero-status-dot" />
              <span className="hero-status-label">현재 상태</span>
            </div>
            <span className="hero-status-badge">보통</span>
          </div>

          <div className="hero-stats">
            <div className="hero-stat-box">
              <p className="hero-stat-value">보통</p>
              <p className="hero-stat-label">심혈관 위험도</p>
            </div>

            <div className="hero-stat-box">
              <p className="hero-stat-value">52세</p>
              <p className="hero-stat-label">실혈관 나이</p>
            </div>

            <div className="hero-stat-box">
              <p className="hero-stat-value">78</p>
              <p className="hero-stat-label">건강 점수</p>
            </div>
          </div>

          <div className="hero-risk-section">
            <p className="hero-risk-title">주요 위험 요인</p>

            <div className="hero-risk-list">
              <div className="hero-risk-item">
                <span className="hero-risk-icon">🩸</span>
                <div className="hero-risk-text">
                  <strong>혈압 관리</strong>
                  <span>수축기 혈압이 다소 높아요</span>
                </div>
              </div>

              <div className="hero-risk-item">
                <span className="hero-risk-icon">🧈</span>
                <div className="hero-risk-text">
                  <strong>콜레스테롤 주의</strong>
                  <span>식단 조절이 필요해요</span>
                </div>
              </div>
            </div>
          </div>

          <div className="hero-feedback-box">
            <p className="hero-feedback-title">AI 코멘트</p>
            <p className="hero-feedback-text">
              혈압과 콜레스테롤 관리가 중요해요.
              저염 식단과 가벼운 유산소 운동을 함께 시작해보세요.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}