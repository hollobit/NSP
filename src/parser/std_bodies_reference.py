#!/usr/bin/env python3
"""
Authoritative reference of ISO/IEC Joint Technical Committees and their
sub-committees / working groups, used to seed the std_bodies registry even
when the 2026 시행계획 본문이 해당 기구를 명시적으로 언급하지 않더라도
대시보드가 관련 구조를 표시할 수 있게 한다.

Source: ISO/IEC 공식 웹사이트 (JTC1 https://www.iso.org/isoiec-jtc-1.html) 정리.

Each entry has:
  id         — SB-<name-with-_>  (레지스트리 key)
  name       — canonical name (예: "ISO/IEC JTC1/SC42")
  type       — 'formal' (공적)
  level      — 'jtc' (Joint Technical Committee 기관 레벨)
             | 'tc'  (Sub-Committee 또는 WG)
  parent     — 상위 JTC id (SC/WG인 경우)
  scope      — 소관 영역 요약
  primary_tech_category_ids — 본 대시보드의 T01~T18 매핑 (1..N)
"""
from __future__ import annotations

# ISO/IEC Joint Technical Committees
JTCS = [
    {
        "id": "SB-ISO_IEC_JTC1",
        "name": "ISO/IEC JTC1",
        "type": "formal",
        "level": "jtc",
        "parent": None,
        "scope": "Information technology — the primary joint committee of ISO and IEC",
        "primary_tech_category_ids": ["T01", "T04", "T06", "T15", "T17", "T18"],
        "established": 1987,
    },
    {
        "id": "SB-ISO_IEC_JTC2",
        "name": "ISO/IEC JTC2",
        "type": "formal",
        "level": "jtc",
        "parent": None,
        "scope": "Energy efficiency and renewable energy sources (historical, dissolved in 2013; activities merged into TC 301 and related TCs)",
        "primary_tech_category_ids": ["T11"],
        "established": 2009,
        "status": "dissolved",
    },
    {
        "id": "SB-ISO_IEC_JTC3",
        "name": "ISO/IEC JTC3",
        "type": "formal",
        "level": "jtc",
        "parent": None,
        "scope": "Quantum technologies (newly established 2024)",
        "primary_tech_category_ids": ["T02"],
        "established": 2024,
    },
    {
        "id": "SB-ISO_IEC_JTC4",
        "name": "ISO/IEC JTC4",
        "type": "formal",
        "level": "jtc",
        "parent": None,
        "scope": "(Reserved/Not yet established — placeholder for future ISO/IEC joint committee)",
        "primary_tech_category_ids": [],
        "status": "reserved",
    },
    {
        "id": "SB-ISO_IEC_JTC5",
        "name": "ISO/IEC JTC5",
        "type": "formal",
        "level": "jtc",
        "parent": None,
        "scope": "(Reserved/Not yet established — placeholder for future ISO/IEC joint committee)",
        "primary_tech_category_ids": [],
        "status": "reserved",
    },
]

# ISO/IEC JTC1 Sub-Committees (selected — most relevant to 18 기술 분류)
JTC1_SCS = [
    # SC  2: Coded character sets — omitted (low relevance)
    # SC  6: Telecommunications and information exchange between systems
    {"id": "SB-ISO_IEC_JTC1_SC6",
     "name": "ISO/IEC JTC1/SC6",
     "scope": "Telecommunications and information exchange between systems",
     "primary_tech_category_ids": ["T04", "T18"]},
    # SC  7: Software and systems engineering
    {"id": "SB-ISO_IEC_JTC1_SC7",
     "name": "ISO/IEC JTC1/SC7",
     "scope": "Software and systems engineering",
     "primary_tech_category_ids": []},
    # SC 22: Programming languages
    # SC 24: Computer graphics, image processing and environmental data representation
    {"id": "SB-ISO_IEC_JTC1_SC24",
     "name": "ISO/IEC JTC1/SC24",
     "scope": "Computer graphics, image processing, AR/VR/MR data representation",
     "primary_tech_category_ids": ["T15"]},
    # SC 27: Information security, cybersecurity and privacy protection
    {"id": "SB-ISO_IEC_JTC1_SC27",
     "name": "ISO/IEC JTC1/SC27",
     "scope": "Information security, cybersecurity and privacy protection",
     "primary_tech_category_ids": ["T17"]},
    # SC 29: Coding of audio, picture, multimedia and hypermedia information (JPEG, MPEG)
    {"id": "SB-ISO_IEC_JTC1_SC29",
     "name": "ISO/IEC JTC1/SC29",
     "scope": "Coding of audio, picture, multimedia and hypermedia information (JPEG, MPEG)",
     "primary_tech_category_ids": ["T15"]},
    # SC 31: Automatic identification and data capture techniques (RFID, barcodes)
    {"id": "SB-ISO_IEC_JTC1_SC31",
     "name": "ISO/IEC JTC1/SC31",
     "scope": "Automatic identification and data capture (RFID, barcodes)",
     "primary_tech_category_ids": ["T18"]},
    # SC 32: Data management and interchange
    {"id": "SB-ISO_IEC_JTC1_SC32",
     "name": "ISO/IEC JTC1/SC32",
     "scope": "Data management and interchange (SQL, metadata)",
     "primary_tech_category_ids": ["T01"]},
    # SC 34: Document description and processing languages
    # SC 35: User interfaces — accessibility, gestures
    # SC 36: IT for learning, education and training
    # SC 37: Biometrics
    {"id": "SB-ISO_IEC_JTC1_SC37",
     "name": "ISO/IEC JTC1/SC37",
     "scope": "Biometrics",
     "primary_tech_category_ids": ["T17"]},
    # SC 38: Cloud computing and distributed platforms
    {"id": "SB-ISO_IEC_JTC1_SC38",
     "name": "ISO/IEC JTC1/SC38",
     "scope": "Cloud computing and distributed platforms",
     "primary_tech_category_ids": ["T01", "T18"]},
    # SC 39: Sustainability, IT and data centres
    {"id": "SB-ISO_IEC_JTC1_SC39",
     "name": "ISO/IEC JTC1/SC39",
     "scope": "Sustainability, IT and data centres",
     "primary_tech_category_ids": ["T11"]},
    # SC 40: IT service management and IT governance
    # SC 41: Internet of things and digital twin
    {"id": "SB-ISO_IEC_JTC1_SC41",
     "name": "ISO/IEC JTC1/SC41",
     "scope": "Internet of Things and digital twin",
     "primary_tech_category_ids": ["T18"]},
    # SC 42: Artificial intelligence
    {"id": "SB-ISO_IEC_JTC1_SC42",
     "name": "ISO/IEC JTC1/SC42",
     "scope": "Artificial intelligence — foundational, trustworthiness, computational approaches, use cases, governance (ISO/IEC 22989, 23053, 23894, 42001 등)",
     "primary_tech_category_ids": ["T01"]},
    # SC 43: Brain-computer interfaces
    {"id": "SB-ISO_IEC_JTC1_SC43",
     "name": "ISO/IEC JTC1/SC43",
     "scope": "Brain-computer interfaces (신설 2024)",
     "primary_tech_category_ids": ["T01", "T10"]},
]
for sc in JTC1_SCS:
    sc.update({"type": "formal", "level": "tc", "parent": "SB-ISO_IEC_JTC1"})

# ISO/IEC JTC3 Working Groups (Quantum technologies)
JTC3_WGS = [
    {"id": "SB-ISO_IEC_JTC3_WG1",
     "name": "ISO/IEC JTC3/WG1",
     "scope": "Quantum computing — foundational concepts and terminology",
     "primary_tech_category_ids": ["T02"]},
    {"id": "SB-ISO_IEC_JTC3_WG2",
     "name": "ISO/IEC JTC3/WG2",
     "scope": "Quantum communication — QKD protocols, performance",
     "primary_tech_category_ids": ["T02", "T17"]},
    {"id": "SB-ISO_IEC_JTC3_WG3",
     "name": "ISO/IEC JTC3/WG3",
     "scope": "Quantum sensing and metrology",
     "primary_tech_category_ids": ["T02"]},
]
for wg in JTC3_WGS:
    wg.update({"type": "formal", "level": "tc", "parent": "SB-ISO_IEC_JTC3"})


def all_reference_bodies() -> list[dict]:
    """Return all reference bodies in a stable order."""
    out = []
    for jtc in JTCS:
        out.append(jtc)
        pid = jtc["id"]
        # Attach sub-committees for this JTC
        if pid == "SB-ISO_IEC_JTC1":
            out.extend(JTC1_SCS)
        elif pid == "SB-ISO_IEC_JTC3":
            out.extend(JTC3_WGS)
    return out


if __name__ == "__main__":
    import json
    bodies = all_reference_bodies()
    print(json.dumps(
        {"count": len(bodies), "bodies": bodies},
        ensure_ascii=False, indent=2,
    ))
