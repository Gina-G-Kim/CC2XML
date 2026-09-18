# ST 문서 가공 가이드

실제 ST/PP 문서를 `cc2xml`이 파싱할 수 있는 표준 형식 텍스트로 "가공"할 때 참고하는
안내서. `ST_TEMPLATE.md`가 실제 예시이고, 이 문서는 그 예시의 각 블록이 어떤 패턴을
보여주는지, 그리고 EAL/PP 전 수준에 어떻게 적용하는지를 설명함. `ST_TEMPLATE.md`는
그 자체로 `python3 -m cc2xml.cli templates/ST_TEMPLATE.md` 실행 시 `PASS`, zero issues로
검증됨 - 아래 설명은 전부 실제로 확인된 동작임 (가정이 아님).

## 문서 골격 (항상 이 순서, `devnotes/` 수정 1~10 기준)

```
{제목}
{버전}
{날짜}

1. Introduction
2. Conformance Claims
3. Security Problem Definition
4.1 Security Objectives for the TOE
4.2 Security Objectives for the Operational Environment
5. Extended Components Definition
6. Security Functional Requirements
7. Security Assurance Requirements
8. Security Requirements Rationale
9. TOE Summary Specification
```

**표지(맨 위 3줄)**: 제목/버전/날짜만 적는다. `Sponsor:`/`Developer:` 같은 줄은 추가하지
말 것 - `parse_doc_reference`가 이런 라벨을 인식하지 않고, 오히려 제목 뒤에 잘못
붙어버림(제목 추출은 처음 10줄 중 버전/날짜가 아닌 줄을 최대 2개까지 그냥 이어붙임).
Sponsor/Developer 정보가 필요하면 Introduction 본문 서술에 자연스럽게 녹여 쓴다 -
`identifier`/`author`/`sponsor` 출력 필드는 현재 항상 빈 값이다.

## 2. Conformance Claims

- CC 버전: `Common Criteria (CC:2022)` 처럼 문서 어딘가에 이 형식으로 한 번 언급.
- Part 2/3 준수: `Part 2 extended` 또는 `Part 2 conformant`(=strict), `Part 3
  conformant` 문구를 그대로 포함.
- **PP claim**: `PP-` 또는 `PP_`로 시작하는 토큰이 있어야 인식됨 (예: `PP-Example-Base`).
  그냥 "the Example Base Protection Profile"처럼 자연어로만 쓰면 인식 안 됨 - 반드시
  `PP-`/`PP_` 접두 id 형태로 한 번은 언급.
- **EAL/패키지 claim**: `EAL2 augmented by ALC_FLR.2`처럼 EAL 숫자 바로 뒤에 콤마 없이
  `augmented`가 와야 augmented 플래그가 켜짐. `EAL2, augmented by ALC_FLR.2`(콤마 있음)는
  augmented가 `false`로 잘못 잡힘 - **콤마를 넣지 말 것**. 어떤 특정 컴포넌트로
  augmented되는지(`ALC_FLR.2`)는 이 속성에 반영되지 않고 boolean만 잡힘 - 실제 목록은
  7장 SAR 섹션에 그 컴포넌트를 직접 나열해서 표현.
- PP를 claim하지 않으면 그냥 PP 관련 문구를 아예 안 쓰면 됨 (별도의 "no PP" 표기 불필요).

## 3. SPD / 4. Objectives — 공통 패턴

id 한 줄 + 그 다음 줄부터 다음 id 전까지가 전부 description이 됨. 표(table) 형식은
지원하지 않음 - 항상 이 "id 줄 + 서술 문단" 형태로 가공.

- Threat: `T.NAME`, Assumption: `A.NAME`, OSP: `P.NAME` 또는 `OSP.NAME`
- TOE 목적: `O.NAME`, 환경 목적: `OE.NAME` (`OT.` 형태는 인식 안 함)

## 5. Extended Components Definition

- 확장 컴포넌트가 없으면 "없다"는 문장 한 줄이면 충분 (섹션 자체는 남겨두되 컴포넌트
  블록은 없음).
- 있으면 SFR과 같은 헤더+element 형식을 그대로 씀. `Family Behaviour:`/`Component
  levelling:`/`Management:`/`Audit:` 마커는 다른 필드(Hierarchical to/Dependencies)의
  경계를 잡는 용도로만 쓰이고, **그 내용 자체는 출력에 보존되지 않음**(`<family_behaviour>`/
  `<component_levelling>`은 항상 빈 태그) - 길게 쓸 필요 없음, 짧게 형식만 갖추면 됨.

## 6. Security Functional Requirements — 패턴별 예시 (템플릿의 각 블록)

| 패턴 | 템플릿 예시 | 언제 쓰나 |
|---|---|---|
| 이름만 언급 (카탈로그 폴백) | `FIA_UID.2` | 표준/PP에서 변경 없이 그대로 가져온 요구사항. Hierarchical to/Dependencies/element 원문이 전부 `cc_2022.xml`에서 자동으로 채워짐(`source="catalog"`) |
| 완전 재서술 | `FIA_UAU.2` | ST가 실제로 운영을 완료한 요구사항. `Hierarchical to:`/`Dependencies:` 명시 + element 원문 전부 작성 |
| AND 종속성 여러 개 | `FDP_ACF.1` (`Dependencies: FDP_ACC.1, FMT_MSA.3`) | 콤마로 나열 = 전부 필요(AND). 각각 새 줄에 따로 써도 됨(`FDP_ACC.1`\n`FMT_MSA.3`) - 단, id만 있고 다른 텍스트가 전혀 없는 줄이어야 함 |
| OR 종속성(대안 중 하나) | `FDP_ETC.1` (`Dependencies: [FDP_ACC.1 or FDP_IFC.1]`) | 대괄호 `[A or B]` 형식이 명확함. 대괄호 없이 `A or B`도 인식은 되지만 대괄호 권장 |
| 정당화된 미충족 종속성 | `FDP_IFF.1`의 `FMT_MSA.3 not resolved. ...` | 카탈로그가 요구하는 종속성을 이 TOE에서는 충족시키지 않을 때. id로 새 줄을 시작하고 바로 `not resolved`/`not applicable`/`not satisfied`/`is not met` 중 하나가 이어져야 인식됨. **같은 줄에 압축해서 쓰면 인식 안 됨** - 반드시 새 줄 |
| 반복(iteration) | `FCS_COP.1/Hash` | 같은 컴포넌트를 다른 용도로 여러 번 쓸 때. id와 모든 element id에 `/라벨`을 일관되게 붙임 |
| Application Note | `FDP_ACF.1`의 `Application note: ...` | 그대로 텍스트 보존됨(`<application_note>`) |
| selection-based 포함 | `FTP_ITC.1`의 "This SFR is selection-based, ..." | 블록 본문 어딘가에 `selection-based` 문구 포함 |
| optional 포함 | `FAU_SAR.1`의 "This SFR is optional, ..." | 블록 본문에 `optional SFR` 또는 `(O)` 포함 |
| objective 포함 | `FAU_GEN.2`의 "This is an objective SFR, ..." | 블록 본문에 `objective SFR` 또는 `(objective)` 포함 |
| assignment/selection | 여러 element | `[assignment: ...]`, `[selection: ...]` 그대로. `iteration`/`refinement`는 별도 브래킷 문법이 없음 - refinement는 그냥 평문에 녹여 서술 |

**EAL 전 수준 적용**: 이 표의 두 핵심 패턴(이름만 언급 vs 완전 재서술)만 있으면 SFR
개수가 몇 개든(작은 EAL1급 제품이든 SFR이 많은 고사양 제품이든) 전부 표현 가능. 실제로
어떤 SFR을 쓸지는 claim하는 PP/패키지에 따라 다르므로 `ref/cc_2022.xml` 또는
`ref/ISO_IEC_15408-2_2026(en).pdf`에서 필요한 컴포넌트를 찾아 같은 형식으로 채우면 됨.

## 7. Security Assurance Requirements — EAL 전 수준 적용

패턴은 SFR과 동일하게 두 가지뿐:
- **이름만 언급** (`ADV_TDS.1`, `AGD_OPE.1`, `AGD_PRE.1`, `ATE_IND.2`, `AVA_VAN.2`,
  `ALC_FLR.2`처럼) - EAL 패키지를 그대로 claim하는 대부분의 경우. `cc_2022.xml`에서
  Hierarchical to/Dependencies/D·C·E element 원문이 전부 자동으로 채워짐.
- **완전 재서술** (`ADV_FSP.1`) - ST가 특정 SAR element에 대해 실제 assignment 등을
  완료해야 할 때만. `Developer action elements:`/`Content and presentation
  elements:`/`Evaluator action elements:` 헤더 줄은 가독성을 위한 것일 뿐 파싱에는
  영향 없음(element id 자체의 `D`/`C`/`E` 접미사만으로 타입이 결정됨) - 안 써도 되지만
  넣는 걸 권장.

**EAL1~EAL7 전부**: 어떤 EAL이든 필요한 SAR 컴포넌트 목록만 다르고 두 패턴 자체는
동일. EAL별 정확한 컴포넌트 목록은 `ref/ISO_IEC_15408-5_2026(en).pdf`(사전 정의 패키지)
참고. 대부분은 "이름만 언급"으로 충분 - 실제 발간된 ST들도 EAL 패키지의 모든
컴포넌트를 일일이 재서술하지 않는 게 흔함(`tests/arbit_data_diode_st.md`가 실제 사례).

## 8. Security Requirements Rationale

- `objectives_rationale`/`sfr_rationale` 둘 다: id 한 줄 + 그 다음 줄부터 다음 id
  전까지가 justification. 표 형식 대신 이 서술형만 지원.
- **`dependency_rationale`은 여기서 직접 안 씀** - 6장/7장 본문에서 "정당화된 미충족
  종속성" 패턴으로 쓴 내용이 자동으로 여기 채워짐 (`collect_dependency_justifications`).
- 모든 SFR을 `sfr_rationale`에서 언급하지 않으면 `UNMAPPED_SFR` 경고(WARNING, 문서
  전체를 FAIL로 만들진 않음)가 남음 - 완결된 문서를 원하면 전부 다뤄야 함.

## 9. TOE Summary Specification

자유 서술. 특별한 패턴 없음, 원문 그대로 `<raw>`에 CDATA로 보존됨.

## PP 문서 작성 시 차이점

- "Security Target"보다 "Protection Profile" 언급이 더 많아야 `doc_type="PP"`로
  판정됨 (`detect_doc_type`은 단순 빈도 비교).
- PP는 `toe_version`이 항상 빈 값으로 출력됨(ST일 때만 채워짐) - 표지에 버전을 써도
  무방하지만 출력에는 반영 안 됨.
- 그 외 구조(SPD/Objectives/SFR/SAR/Rationale)는 ST와 완전히 동일한 패턴 사용.

## 알려진 한계 (가공 시 참고)

- `Management:`/`Audit:` 아래 내용도 `Family Behaviour:`/`Component levelling:`처럼
  출력에 보존되지 않음 - 필드 경계 구분용으로만 인식됨.
- 표 형식(X-매트릭스, 열 정렬) 파싱은 지원하지 않음 - "표 형식은 고려할 필요 없다"는
  전제하에 가공 단계에서 전부 위 서술형으로 풀어써야 함.
- 종속성 정당화 문구는 새 줄에서 id로 시작해야 인식됨 - 같은 줄에 압축된 표기는
  인식 못함 (`devnotes/done/15` 참고).
- `dependency_rationale`의 부분 충족(일부는 충족, 나머지만 정당화)은 컴포넌트별
  `Dependencies:` 필드 안에서 만족된 id와 미충족 id를 섞어 쓰면 그대로 지원됨
  (`FDP_IFF.1` 예시가 정확히 이 경우).
