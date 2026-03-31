import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../App.css";

export default function HealthInputPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    nickname: "",
    age: "",
    gender: "",
    height: "",
    weight: "",
    systolic: "",
    diastolic: "",
    cholesterol: "",
    glucose: "",
    smoking: "no",
    smokingFrequency: "",
    drinking: "no",
    drinkingFrequency: "",
    exercise: "no",
    exerciseFrequency: "",
  });

  const handleChange = (key: string, value: string) => {
    setForm((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSubmit = () => {
    console.log("입력 데이터:", form);
    navigate("/dashboard");
  };

  return (
    <div className="health-page">
      <div className="health-container">
        <header className="health-header">
          <div className="health-logo">MyHealthBuddy</div>
          <button className="health-login-button">로그인</button>
        </header>

        <h1 className="health-title">건강 데이터 입력</h1>

        <div className="health-form-card">
          <div className="health-grid">
            <section className="health-section">
              <h2 className="section-title">기본 정보</h2>

              <label className="input-label">닉네임</label>
              <input
                className="text-input"
                value={form.nickname}
                onChange={(e) => handleChange("nickname", e.target.value)}
              />

              <label className="input-label">나이</label>
              <input
                className="text-input"
                type="number"
                value={form.age}
                onChange={(e) => handleChange("age", e.target.value)}
              />

              <label className="input-label">성별</label>
              <div className="choice-row">
                <button
                  type="button"
                  className={`choice-button ${form.gender === "male" ? "selected" : ""}`}
                  onClick={() => handleChange("gender", "male")}
                >
                  남
                </button>
                <button
                  type="button"
                  className={`choice-button ${form.gender === "female" ? "selected" : ""}`}
                  onClick={() => handleChange("gender", "female")}
                >
                  여
                </button>
              </div>

              <label className="input-label">키</label>
              <input
                className="text-input"
                type="number"
                value={form.height}
                onChange={(e) => handleChange("height", e.target.value)}
              />

              <label className="input-label">체중</label>
              <input
                className="text-input"
                type="number"
                value={form.weight}
                onChange={(e) => handleChange("weight", e.target.value)}
              />
            </section>

            <section className="health-section">
              <h2 className="section-title">건강검진 수치</h2>

              <label className="input-label">수축기 혈압</label>
              <input
                className="text-input"
                type="number"
                value={form.systolic}
                onChange={(e) => handleChange("systolic", e.target.value)}
              />

              <label className="input-label">이완기 혈압</label>
              <input
                className="text-input"
                type="number"
                value={form.diastolic}
                onChange={(e) => handleChange("diastolic", e.target.value)}
              />

              <label className="input-label">총 콜레스테롤</label>
              <input
                className="text-input"
                type="number"
                value={form.cholesterol}
                onChange={(e) => handleChange("cholesterol", e.target.value)}
              />

              <label className="input-label">공복혈당</label>
              <input
                className="text-input"
                type="number"
                value={form.glucose}
                onChange={(e) => handleChange("glucose", e.target.value)}
              />
            </section>
          </div>

          <section className="health-section lifestyle-section">
            <h2 className="section-title">생활 습관</h2>

            <div className="habit-grid">
              <div className="habit-item">
                <label className="input-label">흡연 여부</label>
                <div className="choice-row">
                  <button
                    type="button"
                    className={`choice-button ${form.smoking === "yes" ? "selected" : ""}`}
                    onClick={() => handleChange("smoking", "yes")}
                  >
                    예
                  </button>
                  <button
                    type="button"
                    className={`choice-button ${form.smoking === "no" ? "selected" : ""}`}
                    onClick={() => {
                      handleChange("smoking", "no");
                      handleChange("smokingFrequency", "");
                    }}
                  >
                    아니오
                  </button>
                </div>

                {form.smoking === "yes" && (
                  <>
                    <label className="input-label extra-label">흡연 빈도</label>
                    <select
                      className="text-input"
                      value={form.smokingFrequency}
                      onChange={(e) => handleChange("smokingFrequency", e.target.value)}
                    >
                      <option value="">선택</option>
                      <option value="sometimes">가끔</option>
                      <option value="weekly">주 1~3회</option>
                      <option value="daily">매일</option>
                    </select>
                  </>
                )}
              </div>

              <div className="habit-item">
                <label className="input-label">음주 여부</label>
                <div className="choice-row">
                  <button
                    type="button"
                    className={`choice-button ${form.drinking === "yes" ? "selected" : ""}`}
                    onClick={() => handleChange("drinking", "yes")}
                  >
                    예
                  </button>
                  <button
                    type="button"
                    className={`choice-button ${form.drinking === "no" ? "selected" : ""}`}
                    onClick={() => {
                      handleChange("drinking", "no");
                      handleChange("drinkingFrequency", "");
                    }}
                  >
                    아니오
                  </button>
                </div>

                {form.drinking === "yes" && (
                  <>
                    <label className="input-label extra-label">음주 빈도</label>
                    <select
                      className="text-input"
                      value={form.drinkingFrequency}
                      onChange={(e) => handleChange("drinkingFrequency", e.target.value)}
                    >
                      <option value="">선택</option>
                      <option value="sometimes">가끔</option>
                      <option value="weekly">주 1~3회</option>
                      <option value="often">주 4회 이상</option>
                    </select>
                  </>
                )}
              </div>

              <div className="habit-item">
                <label className="input-label">운동 여부</label>
                <div className="choice-row">
                  <button
                    type="button"
                    className={`choice-button ${form.exercise === "yes" ? "selected" : ""}`}
                    onClick={() => handleChange("exercise", "yes")}
                  >
                    예
                  </button>
                  <button
                    type="button"
                    className={`choice-button ${form.exercise === "no" ? "selected" : ""}`}
                    onClick={() => {
                      handleChange("exercise", "no");
                      handleChange("exerciseFrequency", "");
                    }}
                  >
                    아니오
                  </button>
                </div>

                {form.exercise === "yes" && (
                  <>
                    <label className="input-label extra-label">운동 빈도</label>
                    <select
                      className="text-input"
                      value={form.exerciseFrequency}
                      onChange={(e) => handleChange("exerciseFrequency", e.target.value)}
                    >
                      <option value="">선택</option>
                      <option value="weekly1">주 1회</option>
                      <option value="weekly3">주 2~3회</option>
                      <option value="weekly5">주 4~5회</option>
                      <option value="daily">거의 매일</option>
                    </select>
                  </>
                )}
              </div>
            </div>
          </section>
        </div>

        <button className="analyze-button" onClick={handleSubmit}>
          분석하기
        </button>
      </div>
    </div>
  );
}