# 수정 5 — SAR 구조 단순화

## 제거
- `package_inherited` 속성 및 관련 처리 로직
- `augmented` 속성 (component 수준)

## 근거
파서는 텍스트에 실제로 기술된 SAR 컴포넌트를 그대로 읽음.
EAL 패키지 상속 여부는 파서가 판단할 수 없고, 판단할 필요도 없음.
element 텍스트가 있으면 읽고, 없으면 `<elements/>`로 표기.
augmented 여부도 마찬가지로 파서 관심사 밖.

## 변경 후 SAR component 속성

```xml
<component
  id="ADV_FSP.4"
  name="Complete functional specification"
  inclusion="mandatory">
```

`package_inherited`, `augmented` 속성 제거.
