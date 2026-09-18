# CC 파서 데브노트

`devNote.md` 한 파일에 모든 수정 이력을 이어붙이던 방식을 그만두고, 노트 하나(수정 하나)당
파일 하나로 분리해 완료(`done/`)와 미완료(`todo/`)로 나눔. 앞으로 새 수정 사항은 매번 새
번호의 노트 파일로 추가한다 - 기존 파일을 고쳐 쓰지 않는다.

## 배경

ISO/IEC 15408(CC) ST/PP 자연어 텍스트를 XML로 파싱하는 파서. 아래 원칙에 맞춰 파서 코드와
XML 스키마를 수정해 나감.

## 수정 원칙

**설계 기준**:
- 제거: 기업이 작성한 ST 문서(ANSSI-ST, CASA-ST 등) 기반 파싱 규칙 일체
- 유지: ISO/IEC 15408-1/2/3/4/5:2026 및 cc_2022.xml만 기준 (원문은 `../ref/`)

기업 ST 문서는 표준을 자유롭게 변형하여 작성하므로 설계 기준으로 부적합.
파서는 표준 구조만 처리하고, 표준 범위를 벗어난 텍스트는 `unparsed_fragment`로 보존.

## 완료 (`done/`)

| # | 제목 | 요약 |
|---|------|------|
| [01](done/01-spd-simplification.md) | SPD 구조 단순화 | assets/agents/direct rationale 제거 |
| [02](done/02-objectives-simplification.md) | Objectives 구조 단순화 | application_note/OT./inline spd_refs 제거 |
| [03](done/03-conformance-claims-simplification.md) | Conformance Claims 구조 단순화 | allowed_with/conformance_rationale 제거 |
| [04](done/04-introduction-simplification.md) | Introduction 구조 단순화 | toe_reference를 toe_overview로 통합 |
| [05](done/05-sar-attributes-simplification.md) | SAR 구조 단순화 | package_inherited/augmented 속성 제거 |
| [06](done/06-rationale-simplification.md) | Rationale 구조 단순화 | 테이블형 파싱/direct-derived 분기 제거 |
| [07](done/07-root-attributes-cleanup.md) | 루트 요소 속성 정리 | rationale_type 속성 제거 |
| [08](done/08-r4-parsing-rule-simplification.md) | R4 파싱 규칙 단순화 | 목적 식별자 O./OE.만 인식 |
| [09](done/09-validation-rules-adjustment.md) | 검증 규칙 조정 | V2.2 완화, MISSING_DEP_RATIONALE 제거 |
| [10](done/10-synthetic-st-update.md) | 합성 ST 텍스트 업데이트 | asset_refs 관련 줄 제거 |
| [11](done/11-catalog-fallback.md) | cc_2022.xml 폴백 규칙 | hierarchical_to/dependencies/elements 무조건 채움, `source` 속성 |
| [12](done/12-r7-dependency-and-or-fix.md) | R7 Dependencies AND/OR 버그 수정 | 콤마 나열 = AND, "or" 명시 시만 OR |
| [13](done/13-three-fields-design-exceptions.md) | 3요소 설계상 예외 케이스 조사 | 표준 원문 근거로 전수 조사 (문서화만) |
| [14](done/14-hierarchical-substitution-validation-gap.md) | 계층적 상위 컴포넌트 종속성 충족 인식 | Stage-1 V1.2 오탐 수정 |
| [15](done/15-unsatisfied-dependency-rationale-rule.md) | 정당화된 미충족 종속성 추출 규칙 | dependency_rationale 채움, find_component_blocks 부수 버그도 발견해 수정 |
| [16](done/16-bare-id-line-boundary-bug.md) | id만 있는 줄이 컴포넌트 헤더로 오인되던 버그 | templates/ST_TEMPLATE.md 작성 중 발견·수정 |

## 미완료 (`todo/`)

현재 없음.

## 관례

- 노트가 완료되면 `todo/`에서 `done/`으로 **파일을 옮긴다** (번호는 바꾸지 않음 - 번호는
  발행 순서를 나타내는 영구 식별자).
- 새 수정 사항은 done/todo 중 맞는 쪽에 다음 번호로 새 파일을 추가한다 (현재 최대 번호: 16).
- 이 README의 표는 노트를 추가/이동할 때마다 같이 갱신한다.
