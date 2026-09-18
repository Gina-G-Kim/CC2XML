# 수정 1 — SPD 구조 단순화

## 제거
- `<asset_refs>` 및 `<assets>` 블록 전체
- `<agents>` 블록
- Threat 블록 내 `<rationale>` (direct rationale 전용)
- "Directly threatened asset(s):" 패턴 파싱 규칙

## 근거
ASE_SPD.1 Content 요구사항(ISO/IEC 15408-3):
- 1C: threats 기술
- 2C: threat agent, asset, adverse action 포함
- 3C: OSP 기술
- 4C: assumptions 기술

표준은 Threat 내에 asset/agent를 서술하도록 요구하지만
별도 `<assets>` 섹션을 정의하지 않음.
기업 ST마다 asset 표기 방식이 상이하므로 구조화 추출 대신
Threat description에 원문 그대로 포함시킴.

## 변경 후 Threat 구조

```xml
<threat id="T.NAME">
  <description><![CDATA[
    원문 텍스트 전체. threat agent, asset, adverse action 포함.
  ]]></description>
</threat>
```

## 변경 후 Assumption / OSP 구조

```xml
<assumption id="A.NAME">
  <description><![CDATA[원문 텍스트]]></description>
</assumption>

<osp id="P.NAME">
  <description><![CDATA[원문 텍스트]]></description>
</osp>
```
