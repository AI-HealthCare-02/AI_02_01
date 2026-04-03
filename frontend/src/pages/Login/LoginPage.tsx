import "./LoginPage.css";

const LoginPage = () => {
  return (
    <div className="login-page">
      <div className="login-shell">
        <div className="login-left">
          <div className="brand-badge">MyHealthBuddy</div>
          <h1 className="login-main-title">
            건강 관리를
            <br />
            조금 더 쉽고
            <br />
            꾸준하게
          </h1>
          <p className="login-description">
            매일의 건강 입력, 챌린지, 맞춤형 피드백을 한곳에서 관리해보세요.
            작은 습관이 쌓여 더 건강한 일상을 만들 수 있어요.
          </p>

          <div className="feature-list">
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <span>하루 건강 습관 기록</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <span>챌린지 기반 동기부여</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">✓</span>
              <span>나만의 건강 버디와 함께 관리</span>
            </div>
          </div>
        </div>

        <div className="login-right">
          <div className="login-card">
            <div className="card-top">
              <div className="card-logo">💚</div>
              <h2 className="card-title">로그인</h2>
              <p className="card-subtitle">
                구글 계정으로 빠르게 시작해보세요
              </p>
            </div>

            <button className="temp-login-button">
              Google 로그인
            </button>

            <p className="login-footer-text">
              로그인하면 MyHealthBuddy의 서비스 이용약관 및 개인정보 처리방침에
              동의한 것으로 간주됩니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;