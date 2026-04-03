import { useNavigate } from "react-router-dom";
import Layout from "../../components/Layout/Layout";
import "./ResultPage.css";

const mockChallenges = [
  {
    title: "하루 30분 걷기",
    description: "혈압 관리에 도움이 되는 가벼운 유산소 운동",
  },
  {
    title: "저염식 실천하기",
    description: "나트륨 섭취를 줄여 혈압 상승 위험 낮추기",
  },
  {
    title: "주 3회 규칙 운동",
    description: "심혈관 건강 개선을 위한 기본 습관 만들기",
  },
];

export default function ResultPage() {
  const navigate = useNavigate();

  const savedData = localStorage.getItem("healthData");
  const data = savedData ? JSON.parse(savedData) : null;

  const nickname = data?.nickname || "Buddy";

  const systolic = Number(data?.systolic || 0);
  const diastolic = Number(data?.diastolic || 0);
  const glucose = Number(data?.glucose || 0);
  const cholesterol = Number(data?.cholesterol || 0);
  const age = Number(data?.age || 25);

  const riskFactors: string[] = [];

  if (systolic >= 140 || diastolic >= 90) {
    riskFactors.push("혈압 수치가 높습니다.");
  }
  if (glucose >= 100) {
    riskFactors.push("공복혈당이 경계 수준이거나 높습니다.");
  }
  if (cholesterol >= 200) {
    riskFactors.push("총 콜레스테롤 수치가 높습니다.");
  }
  if (data?.smoking === true) {
    riskFactors.push("흡연 습관이 심혈관 위험을 높일 수 있습니다.");
  }
  if (data?.drinking === true) {
    riskFactors.push("음주 습관이 혈압 및 대사 건강에 영향을 줄 수 있습니다.");
  }
  if (data?.exercise === false) {
    riskFactors.push("운동 부족이 위험도 상승에 영향을 줄 수 있습니다.");
  }

  if (riskFactors.length === 0) {
    riskFactors.push("현재 입력 기준으로 뚜렷한 고위험 요인은 크지 않아 보여요.");
  }

  let riskLevel = "보통";
  let cardioAge = age + 3;
  let healthScore = 72;

  if (riskFactors.length >= 4) {
    riskLevel = "높음";
    cardioAge = age + 8;
    healthScore = 48;
  } else if (riskFactors.length <= 1) {
    riskLevel = "낮음";
    cardioAge = Math.max(age - 1, 20);
    healthScore = 86;
  }

  const aiComment =
    riskLevel === "높음"
      ? "현재 입력된 건강 수치와 생활습관을 종합했을 때 심혈관 건강 관리가 필요한 상태로 보여요. 특히 혈압, 혈당, 생활습관 요인이 함께 작용하고 있을 가능성이 있으니 규칙적인 운동과 식습관 조정이 중요합니다."
      : riskLevel === "보통"
      ? "현재 상태는 즉각적인 고위험군으로 보이진 않지만, 혈압·혈당·생활습관 중 일부가 심혈관 건강에 영향을 줄 수 있어요. 작은 생활습관 변화만으로도 충분히 좋은 방향으로 개선할 수 있습니다."
      : "현재 입력 기준으로는 비교적 안정적인 상태로 보여요. 다만 심혈관 건강은 생활습관의 영향을 크게 받기 때문에 운동, 수면, 식습관을 꾸준히 유지하는 것이 중요합니다.";

  const riskClassName =
    riskLevel === "높음"
      ? "high"
      : riskLevel === "낮음"
      ? "low"
      : "medium";

  return (
    <Layout>
      <div className="result-page">
        <section className="result-topbar">
          <div className="result-heading">
            <p className="result-badge">🫀 AI 건강 분석 결과</p>
            <h1 className="result-title">{nickname} 님의 심혈관 건강 리포트</h1>
            <p className="result-subtitle">
              건강검진 수치와 생활습관 정보를 바탕으로 분석한 결과예요.
            </p>
          </div>

          <div className={`result-level-pill ${riskClassName}`}>
            심혈관 위험도 {riskLevel}
          </div>
        </section>

        <section className="result-summary-grid">
          <div className="result-summary-card">
            <p className="result-summary-label">심혈관 위험도</p>
            <h3 className={`result-summary-value ${riskClassName}`}>{riskLevel}</h3>
            <p className="result-summary-sub">현재 생활습관과 수치 기준</p>
          </div>

          <div className="result-summary-card">
            <p className="result-summary-label">심혈관 나이</p>
            <h3 className="result-summary-value">{cardioAge}세</h3>
            <p className="result-summary-sub">실제 나이 대비 추정</p>
          </div>

          <div className="result-summary-card">
            <p className="result-summary-label">건강 점수</p>
            <h3 className="result-summary-value">{healthScore}점</h3>
            <p className="result-summary-sub">종합 건강 상태 점수</p>
          </div>
        </section>

        <section className="result-main-grid">
          <div className="result-card">
            <div className="result-card-header">
              <h2 className="result-card-title">주요 위험 요인</h2>
            </div>

            <ul className="result-risk-list">
              {riskFactors.map((factor, index) => (
                <li className="result-risk-item" key={index}>
                  <span className="result-risk-dot" />
                  <span>{factor}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="result-card">
            <div className="result-card-header">
              <h2 className="result-card-title">AI 종합 코멘트</h2>
            </div>

            <p className="result-ai-comment">{aiComment}</p>
          </div>
        </section>

        <section className="result-card">
          <div className="result-card-header challenge-header-row">
            <div>
              <p className="result-section-eyebrow">추천 루틴</p>
              <h2 className="result-card-title">추천 챌린지</h2>
            </div>

            <button
              className="result-primary-btn"
              onClick={() => navigate("/login")}
            >
              로그인하고 챌린지 보기
            </button>
          </div>

          <p className="result-card-desc">
            챌린지를 확인하려면 로그인 또는 회원가입이 필요해요.
          </p>

          <div className="result-challenge-grid">
            {mockChallenges.map((challenge, index) => (
              <div className="result-challenge-card" key={index}>
                <div className="result-challenge-lock">🔒</div>
                <h3 className="result-challenge-title">{challenge.title}</h3>
                <p className="result-challenge-desc">{challenge.description}</p>

                <button
                  className="result-outline-btn"
                  onClick={() => navigate("/login")}
                >
                  로그인하고 보기
                </button>
              </div>
            ))}
          </div>
        </section>

        <p className="result-warning">
          입력한 건강 데이터는 참고용 분석 결과이며 실제 진단을 대체하지 않습니다.
        </p>
      </div>
    </Layout>
  );
}