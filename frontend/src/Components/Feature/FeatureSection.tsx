import FeatureCard from "./FeatureCard";

export default function FeatureSection() {
  return (
    <section className="feature-section">
      <FeatureCard title="건강 분석" />
      <FeatureCard title="AI 건강 코멘트" />
      <FeatureCard title="맞춤 챌린지" />
      <FeatureCard title="캐릭터 성장" />
    </section>
  );
}