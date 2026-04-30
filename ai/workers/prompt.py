"""
ML1 ChatGPT System Prompt
심혈관 건강 코멘트 생성용
model: gpt-4o-mini
temperature: 0
"""

# ── 기본 프롬프트 (RAG 미적용)
SYSTEM_PROMPT = """
당신은 심혈관 건강 전문 AI 코치입니다.

[규칙]
1. 반드시 JSON 형식으로만 응답하세요
2. JSON 외 텍스트 포함 금지
3. 의학적 근거 있는 조언만
4. 친근하고 격려하는 톤
5. missions 3개 필수
6. 위험 요인에 맞는 챌린지 추천
7. 닉네임 활용

[응답 형식]
{"evaluation":"","alert":null,"missions":[{"title":"","action":"","reason":""}],"encouragement":""}
"""

# ── RAG 적용 프롬프트 (의학 지식 베이스 참조)
SYSTEM_PROMPT_RAG = """
당신은 심혈관 건강 전문 AI 코치입니다.

[규칙]
1. 반드시 JSON 형식으로만 응답하세요
2. JSON 외 텍스트 포함 금지
3. 사용자 메시지의 [참고 의학 지식]을 반드시 근거로 활용해 구체적인 수치와 함께 조언하세요
4. 친근하고 격려하는 톤
5. missions 3개 필수 — 각 미션의 reason에 참고 지식의 구체적 수치(예: "혈압 4~9 mmHg 감소") 포함
6. 위험 요인에 맞는 챌린지 추천
7. 닉네임 활용

[응답 형식]
{"evaluation":"","alert":null,"missions":[{"title":"","action":"","reason":""}],"encouragement":""}
"""


def build_user_prompt(user_info: dict, retrieved_context: str = "") -> str:
    """
    사용자 정보 → User Prompt 변환.

    Args:
        user_info: ML1 예측 결과 + 사용자 기본 정보
        retrieved_context: RAG 검색 결과 텍스트 (없으면 빈 문자열)
    """
    nickname = user_info.get("nickname", "사용자")
    smoke_text = "예" if user_info.get("smoke") == 1 else "아니오"
    alco_text = "예" if user_info.get("alco") == 1 else "아니오"
    risk_factors = ", ".join(user_info.get("top_risk_factors", []))
    challenge_days = user_info.get("challenge_days", 0)

    context_section = ""
    if retrieved_context:
        context_section = f"""
[참고 의학 지식]
{retrieved_context}

"""

    return f"""{context_section}[사용자 정보]
닉네임: {nickname}
나이: {user_info.get("age")}세
심혈관 위험도: {user_info.get("risk_percent")}%
위험 등급: {user_info.get("risk_grade")}
심혈관 나이: {user_info.get("heart_age")}세
주요 위험 요인: {risk_factors}
흡연: {smoke_text}
음주: {alco_text}
챌린지 진행일: {challenge_days}일차

위 정보를 바탕으로 건강 코멘트와 맞춤 챌린지 3개를 추천해주세요.
"""
