# 18개 중점 표준화 분야 (Tech Taxonomy v1)

**출처**: 「제6차 국가표준기본계획(2026-2030)」 VI. 중점 추진과제 > 1. 미래 핵심산업 표준화 > 중점 표준화 분야 선정 (p.12-13)

**선정 근거**: 3개 전략의 교집합/합집합
- ① 첨단산업 표준화전략 (1개: 원자력)
- ② NEXT 기술전략 (국정과제 28) (1개: 첨단바이오)
- ③ 주요국(美·中) 표준화전략 (5개: 차세대통신, 메타버스, 항공우주, 차세대보안, 시티버스)
- ①∩②∩③ 교집합 (7개: AI, 양자, 반도체, 디스플레이, 핵심소재, 이차전지)
- ①∩② (4개: 첨단제조, 미래차, 미래선박, 로봇)

---

## 18개 기술 분류표

| ID | 한글명 | 영문명(권장) | 주요 표준화기구 | Anchor? | 유형 |
|----|--------|-------------|----------------|---------|-----|
| T01 | 인공지능 | AI | ISO/IEC JTC1/SC42, IEEE-P7001 | **✓ (AI Anchor)** | 기반·융합 |
| T02 | 양자기술 | Quantum | ISO/IEC JTC3, QuINSA | | 신흥 |
| T03 | 첨단제조 | Advanced Manufacturing | ISO/TC65 | | 산업 |
| T04 | 차세대통신 | Next-Gen Communication (6G) | ITU, 3GPP | | 신흥 |
| T05 | 디스플레이 | Display | IEC/TC110, VESA | | 유형1(주도권) |
| T06 | 반도체 | Semiconductor | IEC/TC47, SEMI | | 유형1(주도권) |
| T07 | 미래차 | Future Mobility | ISO/TC22/SC32, SAE | | 유형1(주도권) |
| T08 | 미래선박 | Future Shipping | ISO/TC8, API | | 유형1(주도권) |
| T09 | 로봇 | Robotics | ISO/TC299, IEEE-RAS | | 산업 |
| T10 | 첨단바이오 | Advanced Biotech | ISO/TC276, IEEE-SDC | | 산업 |
| T11 | 청정에너지 | Clean Energy | ISO/TC197, Hydrogen Council | | 신흥 |
| T12 | 핵심소재 | Key Materials | ISO/TC38, ASTM | | 산업 |
| T13 | 원자력 | Nuclear | ISO/TC85, IEC/TC45, ASME | | 유형1(주도권) |
| T14 | 이차전지 | Secondary Battery | IEC/TC21, UL | | 산업 |
| T15 | 메타버스 | Metaverse | IEC/TC100/TA21, IEEE | | 유형2(신속대응) |
| T16 | 항공우주 | Aerospace | ISO/TC20/SC16 AAM, ASTM | | 산업 |
| T17 | 차세대보안 | Next-Gen Security | ITU/SG17, FIDO | | 유형2(신속대응) |
| T18 | 시티버스(IoT) | CityVerse / IoT | ITU/SG20, IEEE | | 유형2(신속대응) |

---

## 분류 동의어 사전 (초안 — 파서에서 사용)

```yaml
T01_인공지능:
  aliases: [AI, 인공지능, 생성형, LLM, 머신러닝, 딥러닝, 지능형, AX, 초거대AI]
  negative: []   # 오탐 방지 키워드

T02_양자기술:
  aliases: [양자, quantum, 양자컴퓨팅, 양자통신, 양자암호, 양자센싱]

T03_첨단제조:
  aliases: [첨단제조, 스마트제조, 스마트팩토리, 적층제조, 3D프린팅]

T04_차세대통신:
  aliases: [6G, 5G-Advanced, 차세대통신, 이동통신, 위성통신, 비면허대역]

T05_디스플레이:
  aliases: [디스플레이, OLED, iLED, QD-LED, 롤러블, 마이크로LED]

T06_반도체:
  aliases: [반도체, 웨이퍼, 뉴로모픽, 차세대반도체, 메모리, 시스템반도체, HBM]

T07_미래차:
  aliases: [자율주행, 전기차, 수소차, 미래차, 모빌리티, 자율차, UAM, 도심항공]

T08_미래선박:
  aliases: [미래선박, 친환경선박, 자율운항선박, 암모니아선박, 수소선박, 전기추진선박]

T09_로봇:
  aliases: [로봇, 협동로봇, 서비스로봇, 휴머노이드, 로보틱스]

T10_첨단바이오:
  aliases: [첨단바이오, 디지털헬스, 정밀의료, 합성생물학, 바이오헬스, 유전자치료]

T11_청정에너지:
  aliases: [수소, 청정에너지, 재생에너지, 태양광, 풍력, 암모니아, 연료전지, CCUS]

T12_핵심소재:
  aliases: [핵심소재, 소재부품, 첨단소재, 나노소재, 탄소소재, 희토류]

T13_원자력:
  aliases: [원자력, SMR, 소형모듈원자로, 원전, 방사선, 핵융합]

T14_이차전지:
  aliases: [이차전지, 배터리, 전고체, 리튬이온, LFP, 배터리재활용]

T15_메타버스:
  aliases: [메타버스, XR, VR, AR, MR, 확장현실, 디지털휴먼]

T16_항공우주:
  aliases: [항공우주, 위성, 발사체, 드론, UAM, 성층권]

T17_차세대보안:
  aliases: [사이버보안, 개인정보, 제로트러스트, FIDO, 양자내성암호, PQC, 생체인증]

T18_시티버스:
  aliases: [스마트시티, 디지털트윈, IoT, 사물인터넷, 수중통신, 시티버스]
```

---

## AI-Anchor 기반 연계 분석 설계

**Anchor**: T01 (인공지능) 을 중심축으로 둔다.

**연계 도출 규칙**:
1. 동일 Project 내 T01 ∈ tech_category_ids 이고 T0N (N≠1) ∈ tech_category_ids 이면 AI↔T0N 엣지 +1
2. 동일 중점과제(CoreTask) 내 공동 주관 → 간접 연계(가중치 0.5)
3. 예산 가중: `weight = co_occurrence_count × log(1 + sum_budget_million_krw)`

**기대 인사이트 (샘플)**:
- AI↔반도체 (T01↔T06): 뉴로모픽, HBM, AI반도체 표준
- AI↔미래차 (T01↔T07): 자율주행 인지·판단 AI
- AI↔첨단바이오 (T01↔T10): 의료영상 AI, AI 신약개발
- AI↔차세대보안 (T01↔T17): 생성형 AI 보안, AI 모델 무결성
- AI↔로봇 (T01↔T09): 지능형 로봇, 휴머노이드 제어
- AI↔시티버스 (T01↔T18): 디지털트윈 AI, 스마트시티 AI

---

## 데이터 모델 매핑

```json
{
  "id": "T01",
  "name_ko": "인공지능",
  "name_en": "AI",
  "is_ai_anchor": true,
  "type": "기반·융합",
  "std_bodies": ["ISO/IEC JTC1/SC42", "IEEE-P7001"],
  "source": {
    "file": "제6차 국가표준기본계획(2026-2030).pdf",
    "page": 12
  },
  "aliases": ["AI", "인공지능", "생성형", "LLM", "머신러닝", "딥러닝", "지능형", "AX"]
}
```

파서 `src/parser/tech_classify.py`가 이 taxonomy를 로드해 멀티-레이블 태깅을 수행한다.
