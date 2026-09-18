# 14 — Stage-1 V1.2가 "계층적 상위 컴포넌트로 종속성 충족"을 인식하지 못함

**상태: 완료 (2026-09-18).**

## 수정

`cc2xml/validate.py`에 `_satisfies_dependency(catalog, claimed_id, required_ids)` 추가 -
`claimed_id`가 `required_ids` 중 하나와 직접 같거나, 카탈로그의 `hierarchical_to` 체인을
재귀적으로 따라가 `required_ids` 중 하나에 도달하면(즉 그보다 계층적으로 상위이면) 충족으로
인정. V1.2의 `alt_ids.issubset(catalog_union)` 단순 부분집합 검사를 이 함수 기반 검사로
교체.

## 검증

수정 전 재현:
```
Dependencies: FDP_IFC.2   (FDP_IFF.1의 카탈로그 종속성 FDP_IFC.1을 계층적 상위로 충족)
-> DEPENDENCY_MISMATCH ERROR, result: FAIL   (표준을 완전히 지킨 문서가 잘못 FAIL)
```

수정 후 동일 케이스: `stage1_errors=0`, `DEPENDENCY_MISMATCH` 없음 - 확인됨.
`tests/`의 기존 3개 fixture 전부 `PASS` 유지, 회귀 없음.

## 문제 (원 조사 내용)

ISO/IEC 15408-1:2026 §8.3 및 15408-2:2026 §7.4.3:
> a security requirement based on a component that is hierarchically higher than B [는
> B에 대한 종속성을 충족시킴] / "Components that are hierarchical to the identified
> component may also be used to satisfy the dependency."

예: FDP_IFF.1은 카탈로그상 FDP_IFC.1에 종속되지만, ST가 FDP_IFC.1 대신 (그보다 계층적으로
상위인) FDP_IFC.2를 포함해도 종속성은 정당하게 충족된 것으로 봐야 함.
