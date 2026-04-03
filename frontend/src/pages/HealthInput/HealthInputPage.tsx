import "./HealthInputPage.css";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

const HealthInputPage = () => {
  const navigate = useNavigate();

  const [smoking, setSmoking] = useState<boolean | null>(null);
  const [drinking, setDrinking] = useState<boolean | null>(null);
  const [exercise, setExercise] = useState<boolean | null>(null);

  const [formData, setFormData] = useState({
    nickname: "",
    age: "",
    gender: "",
    height: "",
    weight: "",
    systolic: "",
    diastolic: "",
    glucose: "",
    cholesterol: "",
    smokingFrequency: "",
    drinkingFrequency: "",
    exerciseFrequency: "",
  });

  const handleInputChange = (key: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSubmit = () => {
    if (
      !formData.nickname ||
      !formData.age ||
      !formData.gender ||
      !formData.height ||
      !formData.weight ||
      !formData.systolic ||
      !formData.diastolic ||
      !formData.glucose ||
      !formData.cholesterol
    ) {
      alert("필수 항목을 모두 입력해주세요.");
      return;
    }

    const healthData = {
      ...formData,
      smoking,
      drinking,
      exercise,
    };

    localStorage.setItem("healthData", JSON.stringify(healthData));
    navigate("/result");
  };

  return (
    <div className="health-input-page">
      <div className="health-input-container">
        <div className="health-input-header">
          <p className="health-input-badge">건강 데이터 입력</p>
          <h1 className="health-input-title">건강검진 정보를 입력해주세요</h1>
          <p className="health-input-desc">
            기본 건강 수치와 생활습관 정보를 입력하면 결과를 분석해드려요.
          </p>
        </div>

        <div className="checkup-card">
          <div className="habit-section">
            <h2 className="section-title">기본 정보</h2>

            <div className="checkup-grid">
              <div className="input-group">
                <label>닉네임</label>
                <input
                  type="text"
                  placeholder="사용하실 닉네임을 입력하세요."
                  value={formData.nickname}
                  onChange={(e) => handleInputChange("nickname", e.target.value)}
                />
              </div>

              <div className="input-group">
                <label>나이</label>
                <input
                  type="number"
                  placeholder="예: 50"
                  value={formData.age}
                  onChange={(e) => handleInputChange("age", e.target.value)}
                />
              </div>

              <div className="input-group">
                <label>성별</label>
                <select
                  value={formData.gender}
                  onChange={(e) => handleInputChange("gender", e.target.value)}
                >
                  <option value="">선택해주세요</option>
                  <option value="female">여성</option>
                  <option value="male">남성</option>
                </select>
              </div>

              <div className="input-group">
                <label>신장(cm)</label>
                <input
                  type="number"
                  placeholder="예: 175"
                  value={formData.height}
                  onChange={(e) => handleInputChange("height", e.target.value)}
                />
              </div>

              <div className="input-group">
                <label>체중(kg)</label>
                <input
                  type="number"
                  placeholder="예: 80"
                  value={formData.weight}
                  onChange={(e) => handleInputChange("weight", e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="habit-section">
            <h2 className="section-title">건강 검진 수치</h2>

            <div className="checkup-grid">
              <div className="input-group">
                <label>수축기 혈압(mmHg)</label>
                <input
                  type="number"
                  placeholder="예: 120"
                  value={formData.systolic}
                  onChange={(e) => handleInputChange("systolic", e.target.value)}
                />
              </div>

              <div className="input-group">
                <label>이완기 혈압(mmHg)</label>
                <input
                  type="number"
                  placeholder="예: 80"
                  value={formData.diastolic}
                  onChange={(e) => handleInputChange("diastolic", e.target.value)}
                />
              </div>

              <div className="input-group">
                <label>공복 혈당(mg/dL)</label>
                <input
                  type="number"
                  placeholder="예: 95"
                  value={formData.glucose}
                  onChange={(e) => handleInputChange("glucose", e.target.value)}
                />
              </div>

              <div className="input-group">
                <label>총 콜레스테롤(mg/dL)</label>
                <input
                  type="number"
                  placeholder="예: 180"
                  value={formData.cholesterol}
                  onChange={(e) => handleInputChange("cholesterol", e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="habit-section">
            <h2 className="section-title">생활습관 정보</h2>

            <div className="habit-grid">
              <div className="habit-item">
                <label>흡연 여부</label>

                <div className="option-row">
                  <button
                    type="button"
                    className={`option-btn ${smoking === true ? "active" : ""}`}
                    onClick={() => setSmoking(true)}
                  >
                    예
                  </button>

                  <button
                    type="button"
                    className={`option-btn ${smoking === false ? "active" : ""}`}
                    onClick={() => {
                      setSmoking(false);
                      handleInputChange("smokingFrequency", "");
                    }}
                  >
                    아니오
                  </button>
                </div>

                {smoking === true && (
                  <select
                    value={formData.smokingFrequency}
                    onChange={(e) =>
                      handleInputChange("smokingFrequency", e.target.value)
                    }
                  >
                    <option value="">흡연 빈도 선택</option>
                    <option value="주 1~2회">주 1~2회</option>
                    <option value="주 3~6회">주 3~6회</option>
                    <option value="매일">매일</option>
                  </select>
                )}
              </div>

              <div className="habit-item">
                <label>음주 여부</label>

                <div className="option-row">
                  <button
                    type="button"
                    className={`option-btn ${drinking === true ? "active" : ""}`}
                    onClick={() => setDrinking(true)}
                  >
                    예
                  </button>

                  <button
                    type="button"
                    className={`option-btn ${drinking === false ? "active" : ""}`}
                    onClick={() => {
                      setDrinking(false);
                      handleInputChange("drinkingFrequency", "");
                    }}
                  >
                    아니오
                  </button>
                </div>

                {drinking === true && (
                  <select
                    value={formData.drinkingFrequency}
                    onChange={(e) =>
                      handleInputChange("drinkingFrequency", e.target.value)
                    }
                  >
                    <option value="">음주 빈도 선택</option>
                    <option value="주 1회">주 1회</option>
                    <option value="주 2~3회">주 2~3회</option>
                    <option value="주 4회 이상">주 4회 이상</option>
                  </select>
                )}
              </div>

              <div className="habit-item">
                <label>운동 여부</label>

                <div className="option-row">
                  <button
                    type="button"
                    className={`option-btn ${exercise === true ? "active" : ""}`}
                    onClick={() => setExercise(true)}
                  >
                    예
                  </button>

                  <button
                    type="button"
                    className={`option-btn ${exercise === false ? "active" : ""}`}
                    onClick={() => {
                      setExercise(false);
                      handleInputChange("exerciseFrequency", "");
                    }}
                  >
                    아니오
                  </button>
                </div>

                {exercise === true && (
                  <select
                    value={formData.exerciseFrequency}
                    onChange={(e) =>
                      handleInputChange("exerciseFrequency", e.target.value)
                    }
                  >
                    <option value="">운동 빈도 선택</option>
                    <option value="주 1~2회">주 1~2회</option>
                    <option value="주 3~4회">주 3~4회</option>
                    <option value="주 5회 이상">주 5회 이상</option>
                  </select>
                )}
              </div>
            </div>
          </div>

          <div className="checkup-action">
            <button className="analyze-btn" onClick={handleSubmit}>
              분석하기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthInputPage;