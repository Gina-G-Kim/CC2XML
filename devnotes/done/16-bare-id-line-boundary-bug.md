# 16 — id만 있고 이름이 없는 줄이 컴포넌트 헤더로 오인되던 버그 수정

**상태: 완료 (2026-09-18).** `templates/ST_TEMPLATE.md` 작성 중 발견.

## 문제

`Dependencies:` 아래에 AND-필수 종속성을 콤마로 나열하지 않고 각각 새 줄에 id만
단독으로 적으면(예: `FCS_CKM.3` 한 줄), `_next_marker_index`/`find_component_blocks`가
이 줄을 "새 컴포넌트 헤더"로 오인함 - `COMP_HEADER_RE`가 id 뒤에 이름이 없어도
(`name` 그룹이 빈 문자열) 매치되기 때문. 결과:
- `_next_marker_index`: 그 종속성 필드가 그 줄 직전에서 끊겨 해당 id 자체가 소실됨.
- `find_component_blocks`: SFR/SAR 섹션 전체를 나누는 최상위 스캔이라 더 심각함 -
  실제로는 존재하지 않는 "이름 없는 컴포넌트" 경계가 생기면서, **그 다음 진짜 내용
  (바로 다음 컴포넌트의 element 원문 전체)이 그 유령 블록에 통째로 흡수됨** - 이
  유령 블록은 `parse_sfrs`의 `named_blocks` 필터(이름이 비어있으면 버림)에서 그냥
  버려지므로, 정당한 컴포넌트의 실제 element 원문이 **완전히 소실**되고 카탈로그
  폴백이 조용히 그 자리를 범용 텍스트로 채워버림 - `devnotes/done/15` 작업 때 발견한
  것과 동일한 근본 원인(id로 시작하는 줄은 뒤에 뭐가 오든 `COMP_HEADER_RE`가
  무조건 매치)의 세 번째 사례.

## 수정

`_next_marker_index`와 `find_component_blocks` 둘 다, `COMP_HEADER_RE` 매치 후
`name` 그룹이 비어있지 않은 경우에만 "새 컴포넌트/경계"로 인정하도록 변경. 어차피
이름 없는 헤더는 `parse_sfrs`가 애초에 컴포넌트로 인정 안 하므로, 경계로도 취급 안
하는 게 일관적이고 안전함.

## 검증

`templates/ST_TEMPLATE.md`의 `FCS_COP.1/Hash` (Dependencies가 `[FCS_CKM.1 or
FCS_CKM.5]` 브래킷 + 별도 줄 `FCS_CKM.3`로 구성) 기준:
- 수정 전: `n_deps=1`(브래킷 OR-그룹만), `FCS_CKM.3` 소실, element 원문도 소실되어
  `source="catalog"`로 대체됨 (문서 자체는 `WARN`으로 "정상"처럼 보임).
- 수정 후: `n_deps=2`(OR-그룹 + `FCS_CKM.3` 단독 AND), element `source="st"`로
  실제 작성한 원문이 정확히 남음.

`tests/`의 기존 3개 fixture + `templates/ST_TEMPLATE.md` 전부 `PASS`, 회귀 없음.
