import Layout from "../../components/Layout/Layout";
import "./DashboardPage.css";

const savedData = localStorage.getItem("healthData");
const data = savedData ? JSON.parse(savedData) : null;
const nickname = data?.nickname || "Buddy";

export default function DashboardPage() {
  return (
    <Layout>
      <div className="dashboard-page">
        <section className="dashboard-topbar">
          <div className="dashboard-greeting">
            <p className="dashboard-greeting-badge">🐹 Buddy와 함께하는 오늘의 건강</p>
            <h1 className="dashboard-title">안녕하세요, {nickname}님 👋</h1>
            <p className="dashboard-subtitle">
              오늘도 심혈관 건강을 위한 작은 습관을 시작해볼까요?
            </p>
          </div>

          <div className="dashboard-topbar-right">
            <div className="dashboard-streak-badge">🔥 14일 연속 달성 중</div>
          </div>
        </section>

        <section className="dashboard-hero-card">
          <div className="dashboard-hero-left">
            <div className="dashboard-buddy-avatar">🐹</div>

            <div className="dashboard-hero-text">
              <div className="dashboard-score-row">
                <span className="dashboard-score-number">72</span>
                <span className="dashboard-score-label">점 · 오늘의 건강 점수</span>
              </div>

              <div className="dashboard-progress-bar">
                <div className="dashboard-progress-fill" />
              </div>

              <div className="dashboard-status-inline">
                <span>혈압 정상</span>
                <span>혈당 정상</span>
                <span>걸음 6,240보</span>
              </div>
            </div>
          </div>

          <div className="dashboard-hero-right">
            <div className="dashboard-target-box">
              <p className="dashboard-target-title">목표까지</p>
              <p className="dashboard-target-value">1,800보 남았어요!</p>
            </div>

            <button className="dashboard-side-action">🥗 식단 기록하기</button>
          </div>
        </section>

        <section className="dashboard-metrics-grid">
          <div className="dashboard-metric-card">
            <p className="dashboard-metric-label">혈압</p>
            <h3 className="dashboard-metric-value">118 / 76 mmHg</h3>
            <p className="dashboard-metric-status good">정상</p>
          </div>

          <div className="dashboard-metric-card">
            <p className="dashboard-metric-label">공복 혈당</p>
            <h3 className="dashboard-metric-value">98 mg/dL</h3>
            <p className="dashboard-metric-status good">정상</p>
          </div>

          <div className="dashboard-metric-card">
            <p className="dashboard-metric-label">콜레스테롤</p>
            <h3 className="dashboard-metric-value">215 mg/dL</h3>
            <p className="dashboard-metric-status warning">주의</p>
          </div>

          <div className="dashboard-metric-card">
            <p className="dashboard-metric-label">걸음 수</p>
            <h3 className="dashboard-metric-value">6,240 보</h3>
            <p className="dashboard-metric-status progress">목표 78%</p>
          </div>
        </section>

        <section className="dashboard-challenge-card">
          <div className="dashboard-section-header">
            <div>
              <p className="dashboard-section-eyebrow">✅ 오늘의 챌린지</p>
              <h2 className="dashboard-section-title">오늘 해야 할 건강 루틴</h2>
            </div>

            <div className="dashboard-section-pill">3 / 4 완료</div>
          </div>

          <div className="dashboard-challenge-progress">
            <div className="dashboard-challenge-progress-fill" />
          </div>

          <p className="dashboard-challenge-progress-text">75% 달성</p>

          <div className="dashboard-challenge-grid">
            <div className="dashboard-challenge-item">
              <div className="dashboard-challenge-icon">🚭</div>
              <div className="dashboard-challenge-content">
                <p className="dashboard-challenge-title">담배 안 피웠나요?</p>
              </div>
              <div className="dashboard-challenge-check done" />
            </div>

            <div className="dashboard-challenge-item">
              <div className="dashboard-challenge-icon">🚶</div>
              <div className="dashboard-challenge-content">
                <p className="dashboard-challenge-title">30분 걸었나요?</p>
              </div>
              <div className="dashboard-challenge-check done" />
            </div>

            <div className="dashboard-challenge-item">
              <div className="dashboard-challenge-icon">💧</div>
              <div className="dashboard-challenge-content">
                <p className="dashboard-challenge-title">물 8잔 마셨나요?</p>
              </div>
              <div className="dashboard-challenge-check done" />
            </div>

            <div className="dashboard-challenge-item">
              <div className="dashboard-challenge-icon">🥗</div>
              <div className="dashboard-challenge-content">
                <p className="dashboard-challenge-title">채소 먹었나요?</p>
              </div>
              <div className="dashboard-challenge-check" />
            </div>
          </div>
        </section>

        <section className="dashboard-bottom-grid">
          <div className="dashboard-social-card">
            <div className="dashboard-card-header-inline">
              <h3 className="dashboard-card-title">친구 챌린지 피드</h3>
              <button className="dashboard-outline-btn">응원하기</button>
            </div>

            <div className="dashboard-friend-list">
              <div className="dashboard-friend-item">
                <div className="dashboard-friend-avatar">영</div>
                <div className="dashboard-friend-text">
                  <strong>영현</strong>
                  <span>XX 챌린지 30일 연속 달성!</span>
                </div>
                <button className="dashboard-outline-btn small">응원하기</button>
              </div>

              <div className="dashboard-friend-item">
                <div className="dashboard-friend-avatar">형</div>
                <div className="dashboard-friend-text">
                  <strong>형석</strong>
                  <span>XX 챌린지 완료!</span>
                </div>
                <button className="dashboard-outline-btn small">응원하기</button>
              </div>

              <div className="dashboard-friend-item">
                <div className="dashboard-friend-avatar">승</div>
                <div className="dashboard-friend-text">
                  <strong>승희</strong>
                  <span>XX 챌린지 완료!</span>
                </div>
                <button className="dashboard-outline-btn small">응원하기</button>
              </div>

              <div className="dashboard-friend-item">
                <div className="dashboard-friend-avatar">소</div>
                <div className="dashboard-friend-text">
                  <strong>소윤</strong>
                  <span>XX 챌린지 완료!</span>
                </div>
                <button className="dashboard-outline-btn small">응원하기</button>
              </div>
            </div>
          </div>

          <div className="dashboard-social-card">
            <div className="dashboard-card-header-inline">
              <h3 className="dashboard-card-title">친구 추가</h3>
            </div>

            <div className="dashboard-search-row">
              <input className="dashboard-search-input" defaultValue="A" />
              <button className="dashboard-search-btn">검색</button>
            </div>

            <div className="dashboard-add-list">
              <div className="dashboard-add-item">
                <div className="dashboard-add-avatar">A</div>
                <span className="dashboard-add-name">Apple</span>
                <button className="dashboard-add-btn">대기</button>
              </div>

              <div className="dashboard-add-item">
                <div className="dashboard-add-avatar">A</div>
                <span className="dashboard-add-name">Amy</span>
                <button className="dashboard-add-btn">대기</button>
              </div>

              <div className="dashboard-add-item">
                <div className="dashboard-add-avatar">A</div>
                <span className="dashboard-add-name">Amily</span>
                <button className="dashboard-add-btn">대기</button>
              </div>
            </div>

            <div className="dashboard-recommend-box">
              <p className="dashboard-recommend-text">
                친구 추천 · 3명의 친구가 같은 챌린지를 진행하고 있습니다.
              </p>

              <div className="dashboard-recommend-grid">
                <div className="dashboard-recommend-item">
                  <div className="dashboard-recommend-avatar">B</div>
                  <strong>Berry</strong>
                  <span>1일차 진행 중</span>
                </div>

                <div className="dashboard-recommend-item">
                  <div className="dashboard-recommend-avatar">C</div>
                  <strong>Christopher</strong>
                  <span>15일차 진행 중</span>
                </div>

                <div className="dashboard-recommend-item">
                  <div className="dashboard-recommend-avatar">S</div>
                  <strong>Sandy</strong>
                  <span>7일차 진행 중</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </Layout>
  );
}