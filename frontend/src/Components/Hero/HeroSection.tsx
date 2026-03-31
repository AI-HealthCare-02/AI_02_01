import { useNavigate } from "react-router-dom";

export default function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="hero-section">
      <div className="hero-image-placeholder">캐릭터 이미지</div>

      <div className="hero-brand">MyHealthBuddy</div>

      <h1 className="hero-title">내 건강을 함께 관리하는 친구</h1>

      <p className="hero-description">
        건강검진 결과와 생활습관을 분석해 건강한 변화를 시작해보세요.
      </p>

      <button
        className="start-button"
        onClick={() => navigate("/health-input")}
      >
        건강 분석 시작하기
      </button>
    </section>
  );
}