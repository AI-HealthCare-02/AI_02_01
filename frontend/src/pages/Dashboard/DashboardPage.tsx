import { useEffect, useState } from "react";

type HealthFormData = {
  nickname: string;
  age: string;
  gender: string;
  systolic: string;
  diastolic: string;
  cholesterol: string;
  glucose: string;
  height: string;
  weight: string;
  smoking: string;
  smokingFrequency: string;
  drinking: string;
  drinkingFrequency: string;
  exercise: string;
  exerciseFrequency: string;
};

export default function DashboardPage() {
  const [data, setData] = useState<HealthFormData | null>(null);

  useEffect(() => {
    const savedData = localStorage.getItem("healthFormData");

    if (savedData) {
      setData(JSON.parse(savedData));
    }
  }, []);

  if (!data) {
    return (
      <div style={{ padding: "40px" }}>
        <h1>Dashboard Page</h1>
        <p>저장된 건강 데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "40px" }}>
      <h1>{data.nickname}님의 건강 요약</h1>

      <p>나이: {data.age}</p>
      <p>성별: {data.gender === "male" ? "남성" : "여성"}</p>
      <p>수축기 혈압: {data.systolic}</p>
      <p>이완기 혈압: {data.diastolic}</p>
      <p>총 콜레스테롤: {data.cholesterol}</p>
      <p>공복혈당: {data.glucose}</p>
      <p>키: {data.height}</p>
      <p>몸무게: {data.weight}</p>
      <p>흡연 여부: {data.smoking === "yes" ? "예" : "아니오"}</p>
      <p>흡연 빈도: {data.smokingFrequency || "-"}</p>
      <p>음주 여부: {data.drinking === "yes" ? "예" : "아니오"}</p>
      <p>음주 빈도: {data.drinkingFrequency || "-"}</p>
      <p>운동 여부: {data.exercise === "yes" ? "예" : "아니오"}</p>
      <p>운동 빈도: {data.exerciseFrequency || "-"}</p>
    </div>
  );
}