import Header from "../../components/Header/Header";
import HeroSection from "../../components/Hero/HeroSection";
import FeatureSection from "../../components/Feature/FeatureSection";
import BottomCTASection from "../../components/Bottom/BottomCTASection";
import "./LandingPage.css";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <Header />

      <main className="landing-main">
        <section className="hero-band">
          <HeroSection />
        </section>

        <section className="feature-band" id="feature">
          <FeatureSection />
        </section>

        <section className="cardio-band" id="ai">
          <div className="section-inner">
            <div className="section-heading">
              <p className="section-badge">AI 심혈관 분석</p>
              <h2 className="section-title">
                건강검진 수치로 미리 보는
                <br />
                심혈관 질환 위험 신호
              </h2>
              <p className="section-description">
                수축기 혈압, 이완기 혈압, 공복 혈당, 총 콜레스테롤 같은
                건강검진 데이터를 기반으로 AI가 심혈관 위험도를 분석합니다.
                숫자로만 보이던 결과를 실제 건강 신호로 해석하고,
                생활습관 개선 방향까지 함께 제안해드려요.
              </p>
            </div>

            <div className="cardio-grid">
              <div className="cardio-card">
                <p className="cardio-card-label">분석 항목</p>
                <h3 className="cardio-card-title">심혈관 위험도</h3>
                <p className="cardio-card-text">
                  혈압과 혈당, 콜레스테롤 수치를 바탕으로 현재 심혈관 질환 관련
                  위험 신호를 분석합니다.
                </p>
              </div>

              <div className="cardio-card">
                <p className="cardio-card-label">예측 결과</p>
                <h3 className="cardio-card-title">심혈관 나이</h3>
                <p className="cardio-card-text">
                  실제 나이와 비교한 혈관 건강 상태를 확인하고 생활습관 개선
                  방향을 파악할 수 있어요.
                </p>
              </div>

              <div className="cardio-card">
                <p className="cardio-card-label">종합 평가</p>
                <h3 className="cardio-card-title">건강 점수</h3>
                <p className="cardio-card-text">
                  여러 건강 데이터를 종합해 현재 상태를 점수로 보여주고, 주요
                  위험 요인과 AI 코멘트를 제공합니다.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="diet-band">
          <div className="section-inner">
            <div className="section-heading">
              <p className="section-badge">식단 분석</p>
              <h2 className="section-title">
                심혈관 건강을 위한
                <br />
                AI 식단 분석
              </h2>
              <p className="section-description">
                음식 사진을 업로드하면 AI가 탄수화물, 단백질, 지방 비율과
                나트륨, 비타민, 무기질 상태를 분석합니다.
                고혈압과 고콜레스테롤 관리에 도움이 되는 식사 방향을 쉽게
                확인할 수 있어요.
              </p>
            </div>

            <div className="diet-preview-card">
              <div className="diet-preview-top">
                <div className="diet-food-thumb">🥗</div>

                <div className="diet-food-info">
                  <h3 className="diet-food-title">식단 분석 예시 리포트</h3>
                  <p className="diet-food-subtitle">
                    음식 사진 한 장으로 영양 밸런스를 빠르게 확인하세요
                  </p>
                </div>

                <div className="diet-score-box">
                  <span className="diet-score-label">종합 점수</span>
                  <strong className="diet-score-value">4.2 / 5</strong>
                </div>
              </div>

              <div className="diet-summary-grid">
                <div className="diet-summary-item">
                  <p className="diet-summary-label">탄단지 비율</p>
                  <strong className="diet-summary-value">
                    탄수화물 50 · 단백질 30 · 지방 20
                  </strong>
                </div>

                <div className="diet-summary-item">
                  <p className="diet-summary-label">나트륨 상태</p>
                  <strong className="diet-summary-value warning">높음</strong>
                </div>

                <div className="diet-summary-item">
                  <p className="diet-summary-label">비타민 / 무기질</p>
                  <strong className="diet-summary-value">조금 부족</strong>
                </div>
              </div>

              <div className="diet-feedback-grid">
                <div className="diet-feedback-card">
                  <p className="diet-feedback-title">AI 분석 피드백</p>
                  <p className="diet-feedback-text">
                    나트륨 섭취가 조금 높은 편이에요. 채소와 과일 섭취를 늘리면
                    심혈관 건강 관리에 더 도움이 됩니다.
                  </p>
                </div>

                <div className="diet-feedback-card">
                  <p className="diet-feedback-title">추천 식사 방향</p>
                  <p className="diet-feedback-text">
                    저염 식단과 채소 중심 식단은 고혈압과 고콜레스테롤 관리에
                    도움이 될 수 있어요.
                  </p>
                </div>
              </div>

              <div className="diet-point-box">
                <div>
                  <p className="diet-point-title">포인트로 맞춤 코멘트 열기</p>
                  <p className="diet-point-text">
                    챌린지로 모은 포인트를 사용하면 더 자세한 식단 코멘트와
                    개인화된 건강 조언을 받을 수 있어요.
                  </p>
                </div>

                <button className="diet-point-button">맞춤 코멘트 보기</button>
              </div>
            </div>
          </div>
        </section>

        <section className="hamster-band">
          <div className="section-inner">
            <div className="hamster-story-inner">
              <div className="hamster-story-text">
                <p className="section-badge dark">Buddy 스토리</p>
                <h2 className="section-title light">
                  쳇바퀴 같은 일상 속에서도
                  <br />
                  심혈관 건강은 함께 챙길 수 있어요
                </h2>
                <p className="section-description light">
                  우리의 하루는 늘 바쁘고 반복됩니다. 일하고, 먹고, 쉬는 사이
                  건강은 자꾸 뒤로 밀리곤 하죠.
                  <br />
                  <br />
                  햄스터 Buddy는 그런 우리의 일상을 닮았어요. 작은 기록과 작은
                  실천이 쌓이면 반복되는 하루도 더 건강한 루틴으로 바뀔 수
                  있습니다.
                </p>

                <div className="hamster-highlight-list">
                  <div className="hamster-highlight-item">
                    건강검진 기반 AI 예측
                  </div>
                  <div className="hamster-highlight-item">
                    금연 · 금주 · 운동 챌린지
                  </div>
                  <div className="hamster-highlight-item">
                    식단 분석과 건강 피드백
                  </div>
                </div>
              </div>

              <div className="hamster-story-card">
                <div className="hamster-avatar-large">🐹</div>
                <h3 className="hamster-card-title">
                  Buddy와 함께 건강 습관 만들기
                </h3>
                <p className="hamster-card-text">
                  건강 기록을 남기고 챌린지를 실천할수록 Buddy도 함께 성장해요.
                  <br />
                  혼자가 아니라 친구처럼 같이 만들어가는 건강 루틴이에요.
                </p>

                <div className="habit-streak-box">
                  <p className="habit-streak-label">이번 주 건강 스트릭</p>
                  <div className="habit-streak-grid">
                    <span className="streak-day active">월</span>
                    <span className="streak-day active">화</span>
                    <span className="streak-day active">수</span>
                    <span className="streak-day">목</span>
                    <span className="streak-day">금</span>
                    <span className="streak-day">토</span>
                    <span className="streak-day">일</span>
                  </div>
                  <p className="habit-streak-text">
                    3일 연속 기록 중 · 오늘도 한 걸음 더!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="cta-band" id="challenge">
          <BottomCTASection />
        </section>
      </main>
    </div>
  );
}