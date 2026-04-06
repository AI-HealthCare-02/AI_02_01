import Header from "../../components/Header/Header";
import HeroSection from "../../components/Hero/HeroSection";
import FeatureSection from "../../components/Feature/FeatureSection";
import "../../App.css";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <div className="landing-container">
        <Header />
        <HeroSection />
        <FeatureSection />
      </div>
    </div>
  );
}