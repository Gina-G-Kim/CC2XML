# 수정 9 — 검증 규칙 조정

## 제거 항목
- `MISSING_DEP_RATIONALE` 오류 (수정 6에서 dependency_rationale 선택적 포함으로 변경)

## 변경 항목

**V2.2 SPD ref 링크** (완화):
```
변경 전: spd_ref id가 SPD에 없으면 ERROR
변경 후: spd_ref id가 SPD에 없으면 WARNING
근거: rationale이 SPD 요소 일부만 참조하는 경우도 표준 허용
```

## 유지 항목
V1.1~V1.4, V2.1, V2.3~V2.7 전부 유지.
