import { useNavigate } from "react-router-dom";
import "./Header.css";

export default function Header() {
  const navigate = useNavigate();

  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-left">
          <button className="header-logo" onClick={() => navigate("/")}>
            MyHealthBuddy
          </button>
        </div>

        <nav className="header-nav">
          <a href="#feature">기능</a>
          <a href="#challenge">챌린지</a>
        </nav>

        <div className="header-right">
          <button
            className="header-login-btn"
            onClick={() => navigate("/login")}
          >
            로그인
          </button>
        </div>
      </div>
    </header>
  );
}