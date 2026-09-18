# 15 — "정당화된 미충족 종속성" 추출 규칙이 R7에 없음 (dependency_rationale 항상 빈 상태)

**상태: 완료 (2026-09-18), 단 하나의 잔여 한계 있음 (아래 참고).**

## 수정

- `UNSATISFIED_DEP_RE` 추가: 줄 맨 앞이 컴포넌트 id로 시작하고 곧바로
  "not resolved"/"not applicable"/"not satisfied"/"is not met" 중 하나가 따라오면
  정당화된 미충족 종속성으로 인식.
- `_next_marker_index`가 이 패턴에 매치되는 줄을 "새 필드 마커/컴포넌트 헤더"로 오인해
  Dependencies 필드를 조기 종료시키던 문제 수정 (해당 줄은 그냥 통과시킴).
- **`find_component_blocks`에서도 같은 오탐이 별도로 발생함을 추가로 발견해 수정함** -
  이 함수는 SFR/SAR 섹션 전체를 컴포넌트 단위로 나누는 최상위 스캔인데, 여기서도
  `COMP_HEADER_RE`가 id로 시작하는 모든 줄에 무조건 매치되는 바람에, 정당화 문구가 새
  컴포넌트("FMT_MSA.3 not resolved...")로 오인되어 **원래 컴포넌트(FDP_IFF.1)의 나머지
  본문(자신의 element 5개 전부)이 이 유령 컴포넌트 쪽으로 통째로 잘못 귀속되는** 더 심각한
  손상이 있었음 - `_next_marker_index`만 고치고 처음 돌려봤을 때 실제로 발생해서 잡음.
  같은 `UNSATISFIED_DEP_RE` 가드를 여기에도 추가해 해결.
- `parse_dependencies`에 `_extract_unsatisfied_dependencies` 추가 - 정당화 문구를 찾아
  `{'alternatives': [id], 'unsatisfied': True, 'justification': text}`로 만들고, 해당
  줄들을 일반 충족-종속성 스캔에서 제외(마스킹)함.
- `collect_dependency_justifications`로 SFR/SAR 트리 전체에서 미충족·정당화된 종속성을
  모아 `build_rationale_xml`에 전달, `<dependency_rationale><mapping comp_id=".."
  dep_id="..">` + 빈 `<satisfied_by/>` + `<justification>`으로 렌더링.

## 검증

`tests/arbit_data_diode_st.md`의 FDP_IFF.1에 실제 Arbit ST 원문 그대로("FMT_MSA.3 not
resolved. The TOE configuration is static...") 복원해 넣고 확인:

```xml
<dependencies source="st">
  <dependency unsatisfied="true">
    <alternatives><comp_ref id="FMT_MSA.3"/></alternatives>
  </dependency>
  <dependency>
    <alternatives><comp_ref id="FDP_IFC.1"/></alternatives>
  </dependency>
</dependencies>
```
```xml
<dependency_rationale>
  <mapping comp_id="FDP_IFF.1" dep_id="FMT_MSA.3">
    <satisfied_by comp_id=""/>
    <justification><![CDATA[not resolved. The TOE configuration is static and has
    therefore no concept of manageable security attributes. This dependency is
    therefore not applicable.]]></justification>
  </mapping>
</dependency_rationale>
```

전체 문서 `PASS`, zero issues. `tests/`의 나머지 2개 fixture도 회귀 없이 `PASS` 유지.

## 잔여 한계 (의도적으로 남겨둠)

정당화 문구가 **같은 줄에** 붙어 있으면("Dependencies: FDP_IFC.1, FMT_MSA.3 (not
applicable...)") 여전히 인식 못하고 정상 충족 종속성으로 잘못 취급됨 -
`UNSATISFIED_DEP_RE`가 줄 맨 앞(`^`)에서만 매치하기 때문. 실제 관찰된 문서(Arbit ST)는
표 형태를 텍스트로 옮기면 자연스럽게 "줄바꿈" 형태가 되므로 이 케이스가 실제로 커버하는
게 맞다고 판단, 안 만나본 가상의 압축 표기까지 잡으려고 정규식을 더 느슨하게 만드는 건
지금은 보류함 (실제 사례가 나오면 재검토).

## 문제 (원 조사 내용)

ASE_REQ.1.6C / ASE_REQ.2.7C:
> Each dependency of the security requirements shall either be satisfied, or the security
> requirements rationale shall justify the dependency not being satisfied.

ISO/IEC 15408-1:2026 §8.3은 정당화 사유를 3가지로 제시: (a) 종속성이 불필요/무의미함,
(b) 운영 환경의 보안 목적이 대신 처리함, (c) 다른 SFR(들)의 조합으로 이미 처리됨.
