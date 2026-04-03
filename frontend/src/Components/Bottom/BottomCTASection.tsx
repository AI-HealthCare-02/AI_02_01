import { useNavigate } from "react-router-dom";
import "./BottomCTASection.css";

export default function BottomCTASection() {
  const navigate = useNavigate();

  return (
    <section className="bottom-cta-section" id="challenge">
      <div className="bottom-cta-content">
        <div className="bottom-cta-text">
          <p className="bottom-cta-label">꾸준한 기록</p>
          <h2>
            하루도 빠짐없이,
            <br />
            함께 기록해요
          </h2>
          <p>
            연속 기록 스트릭으로 동기부여를 유지하세요.
            <br />
            오늘의 기록이 내일의 건강을 만듭니다.
          </p>

          <button
            className="bottom-cta-button"
            onClick={() => navigate("/health-input")}
          >
            건강검진 분석 시작하기
          </button>
        </div>

        <div className="bottom-cta-calendar">
          <div className="calendar-grid">
            <div className="calendar-day">1</div>
            <div className="calendar-day active">2</div>
            <div className="calendar-day active">3</div>
            <div className="calendar-day active">4</div>
            <div className="calendar-day active">5</div>
            <div className="calendar-day">6</div>
            <div className="calendar-day">7</div>

            <div className="calendar-day active">8</div>
            <div className="calendar-day active">9</div>
            <div className="calendar-day active">10</div>
            <div className="calendar-day active">11</div>
            <div className="calendar-day active">12</div>
            <div className="calendar-day active">13</div>
            <div className="calendar-day">14</div>

            <div className="calendar-day active">15</div>
            <div className="calendar-day active">16</div>
            <div className="calendar-day active">17</div>
            <div className="calendar-day active">18</div>
            <div className="calendar-day active">19</div>
            <div className="calendar-day active">20</div>
            <div className="calendar-day">21</div>

            <div className="calendar-day active">22</div>
            <div className="calendar-day active">23</div>
            <div className="calendar-day active">24</div>
            <div className="calendar-day active">25</div>
            <div className="calendar-day active">26</div>
            <div className="calendar-day active">27</div>
            <div className="calendar-day">28</div>
          </div>
        </div>
      </div>
    </section>
  );
}