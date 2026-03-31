type FeatureCardProps = {
  title: string;
};

export default function FeatureCard({ title }: FeatureCardProps) {
  return (
    <div className="feature-card">
      <span className="feature-card-title">{title}</span>
    </div>
  );
}