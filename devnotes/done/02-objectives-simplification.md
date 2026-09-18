# 수정 2 — Security Objectives 구조 단순화

## 제거
- `<application_note/>` 필드
- `OT.NAME` 형태 허용 분기 (표준은 `O.NAME` / `OE.NAME`)
- `direct` rationale 전용 inline `<spd_refs>` 채움 로직

## 근거
ASE_OBJ.2 Content 요구사항(ISO/IEC 15408-3):
- 1C: TOE 및 환경 보안 목적 기술
- 2C~6C: security objectives rationale이 traceability 담당

표준은 목적 블록 내 application note를 정의하지 않음.
spd_refs traceability는 rationale 섹션(ASE_OBJ rationale)에서만 처리.
목적 식별자는 표준에서 `O.`(TOE) / `OE.`(환경) 형태로 정의.

## 변경 후 Objectives 구조

```xml
<security_objectives>
  <toe_objectives>
    <objective id="O.NAME">
      <description><![CDATA[원문 텍스트]]></description>
    </objective>
  </toe_objectives>
  <env_objectives>
    <objective id="OE.NAME">
      <description><![CDATA[원문 텍스트]]></description>
    </objective>
  </env_objectives>
</security_objectives>
```

`spd_refs`는 `<objectives_rationale>` 섹션에서만 채움.
