import { NavLink, useNavigate } from "react-router-dom";
import "./Sidebar.css";

export default function Sidebar() {
  const navigate = useNavigate();

  const savedData = localStorage.getItem("healthData");
  const data = savedData ? JSON.parse(savedData) : null;
  const nickname = data?.nickname || "Buddy";

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <button className="sidebar-logo" onClick={() => navigate("/dashboard")}>
          MyHealthBuddy
        </button>

        <div className="sidebar-profile">
          <div className="sidebar-profile-avatar">
            {nickname.charAt(0).toUpperCase()}
          </div>
          <div className="sidebar-profile-text">
            <p className="sidebar-profile-name">{nickname} 님</p>
            <p className="sidebar-profile-sub">오늘도 함께 건강 루틴</p>
          </div>
        </div>

        <nav className="sidebar-menu">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            대시보드
          </NavLink>

          <NavLink
            to="/result"
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            AI 건강 분석
          </NavLink>

          <NavLink
            to="/challenge"
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            챌린지
          </NavLink>

          <NavLink
            to="/diet"
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            식단 분석
          </NavLink>

          <NavLink
            to="/growth"
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            성장 기록
          </NavLink>

          <NavLink
            to="/mypage"
            className={({ isActive }) =>
              isActive ? "sidebar-link active" : "sidebar-link"
            }
          >
            마이페이지
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-bottom">
        <button className="sidebar-logout-btn" onClick={() => navigate("/")}>
          로그아웃
        </button>
      </div>
    </aside>
  );
}