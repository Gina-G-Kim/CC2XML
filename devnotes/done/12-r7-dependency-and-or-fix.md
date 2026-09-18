# 수정 12 — R7 Dependencies 파싱 버그 수정 (AND vs OR)

## 문제
`Dependencies:` 한 줄에 컴포넌트 id가 2개 이상 콤마로 나열되면("Dependencies: FDP_ACC.1,
FMT_SMR.1, FMT_SMF.1") 파서가 이를 "셋 중 하나만 있으면 됨"(OR-그룹, 단일
`<dependency><alternatives>`)으로 잘못 해석했음. 실제로는 셋 다 각각 필요한 AND 관계 - 기존
합성 ST(`tests/ideal_st.md`)의 여러 컴포넌트(FMT_MSA.1/FMT_MSA.3/FDP_ACF.1/FAU_GEN.2 등)에서
실제로 발생하고 있었으나, Stage-1 V1.2가 "명시한 id가 카탈로그 종속성 목록의 부분집합인지"만
검사하고 "카탈로그가 요구하는 AND-그룹이 전부 있는지"는 검사하지 않아 지금까지 발견되지 않음.

## 수정
콤마로 나열된 id들은 각각 별도의 `<dependency>`(단일 alternative)로 분리. 명시적으로
"or"라는 단어가 같이 있을 때만("Dependencies: FIA_UID.1 or FIA_UID.2") 하나의
OR-그룹(`<alternatives>` 복수)으로 유지. 대괄호 OR-그룹 표기(`[FIA_UID.1 or FIA_UID.2]`)는
원래도 올바르게 동작했으므로 변경 없음.

## 검증
`tests/ideal_st.md`의 FMT_MSA.1(3개 AND-dependency)과 새 fixture
`tests/arbit_data_diode_st.md`의 FDP_IFF.1(2개 AND-dependency)에서 각각 별도의
`<dependency>`로 정확히 분리됨을 확인. 전체 fixture PASS 유지, 회귀 없음.
