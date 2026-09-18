# 수정 13 — 3요소(계층/종속/설명)가 "재서술 생략" 외에 설계상 비어있을 수 있는 경우

`ref/ISO_IEC_15408-{1,2,3,4,5}_2026(en).pdf` (2026년판 표준 원문) 근거로 조사함. **아래는 전부
표준이 명시적으로 허용/정의하는 설계상 예외이며, 휴먼에러·오타·파싱 실패 같은 비정상 케이스는
포함하지 않음.**

이 노트 자체(조사 및 문서화)는 완료됨. 조사 중 발견한 미구현 갭 2건은 별도 노트로 분리했다가
(당시엔 `todo/`) 이후 둘 다 수정 완료되어 `done/`으로 옮겨짐 -
[`14-hierarchical-substitution-validation-gap.md`](14-hierarchical-substitution-validation-gap.md),
[`15-unsatisfied-dependency-rationale-rule.md`](15-unsatisfied-dependency-rationale-rule.md).

## 종속관계 (dependencies)

1. **원래 종속성 없음.** Part 2 §7.4.3: "Some components may list 'No dependencies'." -
   기반 컴포넌트는 애초에 종속성이 없음. 폴백이 채워도 여전히 빈 게 정답.
2. **OR-그룹 중 하나만 충족.** Part 2 §7.4.3: "in some cases the dependency is optional in
   that a number of functional components are provided, where each one of them would be
   sufficient" (예: FDP_ETC.1은 FDP_ACC.1 또는 FDP_IFC.1 중 하나만 있으면 됨). 이미 대괄호
   OR-그룹(`[A or B]`) 구문으로 처리 중.
3. **카탈로그가 요구하는 컴포넌트 대신, 그보다 계층적으로 상위인 컴포넌트로 충족.** Part 1
   §8.3: "a security requirement based on a component that is hierarchically higher than B"도
   유효한 충족 방법. Part 2 §7.4.3: "Components that are hierarchical to the identified
   component may also be used to satisfy the dependency." 예: FDP_IFF.1은 FDP_IFC.1에
   종속되지만, ST가 FDP_IFC.1 대신 (그보다 상위인) FDP_IFC.2를 포함해도 종속성은 충족됨.
   → 수정 완료, [`14`](14-hierarchical-substitution-validation-gap.md) 참고.
4. **명시적으로 "미충족"이라고 근거와 함께 선언(불충족 정당화).** ASE_REQ.1.6C/ASE_REQ.2.7C:
   "Each dependency of the security requirements shall either be satisfied, or the security
   requirements rationale shall justify the dependency not being satisfied." Part 1 §8.3은
   정당화 사유를 3가지로 제시: (a) 종속성이 불필요/무의미함, (b) 운영 환경의 보안 목적이
   대신 처리함, (c) 다른 SFR(들)의 조합으로 이미 처리됨. 실제 사례:
   `input/1096V2b_pdf.pdf`(Arbit Data Diode ST)의 FDP_IFF.1이 FMT_MSA.3 종속성에 대해
   "TOE configuration is static... this dependency is therefore not applicable"라고 명시.
   → 수정 완료, [`15`](15-unsatisfied-dependency-rationale-rule.md) 참고.
5. **패키지 차원에서는 종속성이 다 안 채워져도 됨.** Part 1 §9.3 "Package dependencies": "It
   is allowed that a package does not satisfy all the dependencies of the components
   contained within it. However, the dependencies shall be met by a PP, PP-Module,
   PP-Configuration or ST that includes the package." - 패키지 자체 정의 시점에는 종속성 미해결
   상태로 둘 수 있고, 그 패키지를 포함하는 문서(PP/ST)가 채우면 됨. ST 파싱 관점에서는 결국
   위 1~4 중 하나로 귀결되므로 별도 처리 불필요, 근거로만 기록.
6. **Extended component는 자신의 종속성을 스스로 완전히 정의해야 함.** Part 1 §8.4.2: "The
   author also shall make sure that all the applicable dependencies of an extended
   component are included in the definition of that extended component." - 카탈로그가 없으니
   ST/PP 본문이 유일한 정보원. 현재 구현(extended 컴포넌트는 폴백 대상에서 제외)과 일치.

## 계층관계 (hierarchical_to)

1. **원래 계층 없음.** 패밀리 내에서 유일하거나 가장 낮은 레벨인 컴포넌트는 hierarchical-to가
   없는 게 정상 (Part 2 §7.4.3 "a hierarchical-to list"는 있을 수도 없을 수도 있는 목록으로
   정의됨). 종속관계의 "No dependencies"와 동일한 성격 - 비어있음이 곧 정답.
2. 종속관계처럼 "정당화하고 비워도 되는" 별도 예외는 표준에서 찾지 못함 - hierarchical_to는
   ST가 "주장"하는 게 아니라 그 컴포넌트가 표준/PP에 정의된 그대로의 구조적 사실이라, 있거나
   없거나 둘 중 하나이며 정당화가 필요한 중간 상태가 없음. (단, 3번 항목처럼 다른 컴포넌트의
   종속성 충족에 "사용되는" 쪽으로는 의미가 있음.)

## 설명 (elements의 raw 원문)

1. **PP/표준에서 상속받아 재서술 생략.** (기존에 논의됨) 표준이 명시적으로 "재서술 생략을
   허용한다"고 서술한 조문은 찾지 못했으나, ASE_REQ.1.1C/ASE_REQ.2.1C은 "describe"를
   요구할 뿐 축자적 재기술을 강제하지 않고, 실제로 이런 식으로 작성된(그리고 인증받은) ST가
   존재함(`1096V2b_pdf.pdf`) - 관행적으로 확립된 설계상 예외로 취급.
2. **패키지(EAL 등)를 이름으로만 인용하고 개별 컴포넌트 재서술 생략.** Part 1 §9.2.2: EAL은
   ISO/IEC 15408-5에 사전 정의된 assurance package. 패키지는 이미 표준 자체에 완전히
   정의되어 있으므로, "EAL7 augmented by ALC_FLR.1"처럼 패키지를 이름으로 인용하는 것만으로
   구성 SAR 전체를 포함시킨 것으로 볼 수 있음 - PP 상속(1번)과는 근거가 다르지만(claim 대상이
   PP가 아니라 사전 정의된 패키지), 파서 입장에서는 "본문 없음 → 카탈로그 폴백"으로 동일하게
   처리해도 무방. 실제 사례: `1096V2b_pdf.pdf`가 ADV_SPM.1의 assignment 하나만 재서술하고
   EAL7의 나머지 SAR(ADV_FSP.6, ALC_FLR.1 등)은 이름조차 개별 언급하지 않음.
3. **(참고, 다른 카테고리) selection-based SFR이 선택되지 않으면 컴포넌트 자체가 목록에서
   빠짐.** Part 1 §8.2.4.2: 선택(selection)에 연동된 SFR은 그 선택이 실제로 이루어진 경우에만
   포함됨. 이건 "컴포넌트는 있는데 설명이 빔"이 아니라 "컴포넌트 자체가 존재하지 않음"이라
   범주가 다름 - `parser.py`의 `detect_inclusion`(selection_based/optional/objective)이 이미
   이 개념을 반영 중이므로 새로 처리할 필요는 없고, 참고로만 기록.
