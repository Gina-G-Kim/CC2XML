# 수정 4 — Introduction 구조 단순화

## 제거
- `<toe_reference>` 블록 (ST 전용 표기 제거, doc_type 속성으로 대체)

## 근거
ASE_INT.1.1C: ST introduction은 ST reference, TOE reference, TOE overview, TOE description을 포함.
TOE reference는 별도 블록보다 `<toe_overview>` 내에 통합하는 것이 스키마 단순화에 유리.
doc_type 속성이 ST/PP 구분을 이미 담당.

## 변경 후 Introduction 구조

```xml
<introduction>
  <doc_reference>
    <identifier/>   <!-- ST 또는 PP 고유 식별자 -->
    <title/>
    <version/>
    <date/>
    <author/>
    <sponsor/>
  </doc_reference>
  <toe_overview>
    <toe_name/>         <!-- TOE 제품명 (ST) 또는 TOE 유형명 (PP) -->
    <toe_version/>      <!-- ST이면 구체적 버전, PP이면 비워둠 -->
    <toe_type/>         <!-- "smart card", "gateway", "OS" 등 -->
    <description/>      <!-- TOE overview + TOE description 원문 -->
  </toe_overview>
</introduction>
```
