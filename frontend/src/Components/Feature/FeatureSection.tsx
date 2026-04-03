import FeatureCard from "./FeatureCard";
import "./FeatureSection.css";

export default function FeatureSection() {
  return (
    <section className="feature-section" id="feature">
      <div className="feature-header">
        <p className="feature-label">핵심 기능</p>
        <h2 className="feature-title">
          기록에서 끝나지 않고
          <br />
          심혈관 건강 관리로 이어집니다
        </h2>
      </div>

      <div className="feature-grid">
        <FeatureCard
          icon="🫀"
          title="심혈관 AI 예측"
          description="혈압, 혈당, 콜레스테롤 수치를 바탕으로 심혈관 질환 위험도와 건강 점수를 분석해요."
        />
        <FeatureCard
          icon="🏃"
          title="맞춤 챌린지"
          description="금연, 금주, 걷기, 운동하기 등 생활습관 챌린지로 건강한 변화를 시작할 수 있어요."
        />
        <FeatureCard
          icon="🥗"
          title="식단 사진 분석"
          description="음식 사진을 올리면 탄단지 비율과 나트륨, 비타민, 무기질 관련 피드백을 받아볼 수 있어요."
        />
        <FeatureCard
          icon="🐹"
          title="Buddy와 함께"
          description="반복되는 일상 속에서도 햄스터 Buddy와 함께 건강 루틴을 만들고 습관을 이어갈 수 있어요."
        />
      </div>
    </section>
  );
}