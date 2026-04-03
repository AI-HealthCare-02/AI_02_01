import Header from "../../Components/Header/Header";
import HeroSection from "../../Components/Hero/HeroSection";
import FeatureSection from "../../Components/Feature/FeatureSection";
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