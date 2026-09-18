# 수정 6 — Rationale 구조 단순화

## 제거
- `<rationale_table_raw>` 및 테이블형 파싱 시도 로직
- `direct` rationale 분기 처리 전체
- `rationale_type` 속성 (`cc_document` 루트에서 제거)

## 근거
표준(ASE_OBJ.2, ASE_REQ.2)이 정의하는 rationale은 텍스트 서술형.
테이블형(X 매트릭스)은 기업 관행이지 표준 요구사항이 아님.
direct/derived 구분은 파서 복잡도를 높이는 데 비해 실익 없음.
`direct` rationale(ASE_OBJ.1)은 별도 Rationale 섹션이 없으므로
rationale 섹션 자체를 빈 요소로 두면 충분.

## 변경 후 Rationale 구조

```xml
<rationale>
  <objectives_rationale>
    <!-- objective_id → justification 텍스트 + SPD refs -->
    <mapping objective_id="O.NAME">
      <justification><![CDATA[근거 텍스트]]></justification>
      <spd_refs>
        <spd_ref id="T.NAME"/>
      </spd_refs>
    </mapping>
  </objectives_rationale>

  <sfr_rationale>
    <!-- comp_id → justification 텍스트 + objective refs -->
    <mapping comp_id="FAU_GEN.1">
      <justification><![CDATA[근거 텍스트]]></justification>
      <obj_refs>
        <obj_ref id="O.NAME"/>
      </obj_refs>
    </mapping>
  </sfr_rationale>

  <dependency_rationale>
    <!-- 불충족 종속에 대한 근거. 충족된 경우 선택적 포함. -->
    <mapping comp_id="FAU_ARP.1" dep_id="FAU_SAA.1">
      <satisfied_by comp_id=""/>   <!-- 불충족이면 비워둠 -->
      <justification><![CDATA[근거 텍스트]]></justification>
    </mapping>
  </dependency_rationale>
</rationale>
```

`rationale_type` 속성 → `cc_document` 루트에서 제거.
Rationale 섹션 없는 문서 → `<rationale/>`.

> `dependency_rationale`은 이 시점(수정 6)에는 R-규칙(추출 규칙)이 없어 항상 비어있는
> 상태였음 - 이후 [`15-unsatisfied-dependency-rationale-rule.md`](15-unsatisfied-dependency-rationale-rule.md)에서 채움.
