# 수정 11 — SFR/SAR component의 hierarchical_to/dependencies/elements(설명) cc_2022.xml 폴백

## 배경
ST가 표준 컴포넌트를 이름만 언급하고("FAU_GEN.1 Audit data generation") 본문(Hierarchical
to/Dependencies/element 텍스트)을 재서술하지 않는 경우(기반 PP에서 변경 없이 상속) 세 필드가
빈 채로 남아, 요구사항명과 달리 계층/종속/설명이 "무조건" 채워진다는 보장이 없었음.

## 변경
`<hierarchical_to>`/`<dependencies>`/`<elements>` 각각에 `source` 속성 추가:
- `source="st"`: ST 본문에서 실제로 파싱됨 (기존 동작, 변경 없음)
- `source="catalog"`: ST 본문에 해당 필드가 비어 있어 cc_2022.xml에서 채움

폴백 적용 순서: ST 파싱 결과가 비어 있을 때만 카탈로그 값으로 채움 (병합하지 않음, ST가 뭔가
적어놓았으면 그대로 유지). `elements` 폴백 시 element 텍스트는 카탈로그의 범용(미완성)
`[assignment: ...]`/`[selection: ...]` 원문이며, ST가 실제로 완성한 값이 아님 - `source`로
구분 가능하므로 평가자가 오인하지 않음.

## 적용 범위
- extended component(`extended="true"`)는 제외 - 카탈로그에 없는(벤더 자체 정의) 컴포넌트이므로
  ST 본문이 유일한 정보원.
- 카탈로그에 없는 컴포넌트 id(`UNKNOWN_COMPONENT`)도 제외 - 채울 근거 자료 자체가 없음.
- ST가 아예 언급하지 않은 컴포넌트(즉 `<component>` 자체가 없는 경우)는 대상 아님 - 이 규칙은
  "ST가 이름은 언급했는데 본문을 안 채운" 경우만 다룸.

## 근거
파서 사용자(평가자)가 요구사항명·계층관계·종속관계·설명을 매번 "혹시 비어있나" 확인할 필요
없이 항상 값을 신뢰할 수 있어야 함. cc_2022.xml은 이미 Stage-1 검증의 근거 자료이므로 같은
자료를 파싱 단계의 폴백 근거로도 쓰는 것이 일관적임.

## `source` 태그 사용 시 주의
계층/종속관계는 출처(`st`/`catalog`)와 무관하게 동일한 표준 정의 사실 - 가중치를 둘 이유
없음. 반면 설명(element 텍스트)은 출처에 따라 내용 자체가 다름
(`source="catalog"` = 표준의 범용 미완성 placeholder, `source="st"` = TOE에 특화된 완성된
서술) - 후속 소비자(NLP 단계 등)가 이 차이를 반영해야 함.
