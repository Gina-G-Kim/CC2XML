# 수정 3 — Conformance Claims 구조 단순화

## 제거
- `<allowed_with>` 블록 (PP 전용 exact PP 허용 목록)
- `<conformance_rationale/>` 필드

## 근거
ASE_CCL.1 Content 요구사항에서 `allowed_with`는
PP-Configuration 평가(ACE) 맥락에서 등장하며 ST 파싱 범위 밖.
conformance rationale은 서술형으로 description에 포함.

## 변경 후 Conformance Claims 구조

```xml
<conformance_claims>
  <cc_conformance>
    <cc_version/>         <!-- "CC:2022" 등 -->
    <part2_conformance/>  <!-- "extended" | "strict" -->
    <part3_conformance/>  <!-- "extended" | "strict" -->
  </cc_conformance>
  <pp_claims>
    <!-- ST: 클레임하는 PP. PP 문서이면 빈 요소. -->
    <pp_claim ref="" conformance_type=""/>
  </pp_claims>
  <package_claims>
    <!-- "EAL4", "EAL4+", "EAL5" 등 원문 그대로 -->
    <package_claim ref="" augmented=""/>
  </package_claims>
</conformance_claims>
```
