import { useNavigate } from "react-router-dom";

export default function Header() {
  const navigate = useNavigate();

  return (
    <header className="header">
      <div className="logo">MyHealthBuddy</div>
      <button className="login-button" onClick={() => navigate("/login")}>
        로그인
      </button>
    </header>
  );
}