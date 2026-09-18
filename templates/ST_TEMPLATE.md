Template Reference Security Target
Version 1.0
2026-01-01

1. Introduction

This Security Target (ST) describes the Template Reference TOE, a
fictitious product used only to demonstrate every text pattern
`cc2xml/parser.py` recognizes. It claims conformance to a Protection
Profile and to EAL2 augmented, so both PP-conformant and package-only
component styles appear below. See `templates/GUIDE.md` for a
pattern-by-pattern explanation of every block in this file.

2. Conformance Claims

This ST is Part 2 extended and Part 3 conformant with Common Criteria
(CC:2022). It claims conformance to PP-Example-Base. It claims conformance
to EAL2 augmented by ALC_FLR.2.

3. Security Problem Definition

T.EXAMPLE_THREAT
An attacker attempts to perform an unauthorized action against the TOE.

A.EXAMPLE_ASSUMPTION
The operational environment provides physical protection for the TOE.

P.EXAMPLE_POLICY
The TOE shall enforce the example access control policy at all times.

4.1 Security Objectives for the TOE

O.EXAMPLE_OBJECTIVE
The TOE shall counter T.EXAMPLE_THREAT by enforcing P.EXAMPLE_POLICY.

4.2 Security Objectives for the Operational Environment

OE.EXAMPLE_OBJECTIVE
The operational environment shall satisfy A.EXAMPLE_ASSUMPTION.

5. Extended Components Definition

FCS_RBG_EXT.1 Random bit generation

Family Behaviour:
This family defines requirements for random bit generation used by other
cryptographic SFRs.

Component levelling:
FCS_RBG_EXT: Random bit generation 1

Management: No management activities foreseen.
Audit: No auditable events foreseen.

FCS_RBG_EXT.1.1 The TSF shall perform all random bit generation services in
accordance with [assignment: standard] using [selection: hardware-based
noise source, software-based deterministic RBG] seeded by an entropy
source.

6. Security Functional Requirements

FIA_UID.2 User identification before any action

FIA_UAU.2 User authentication before any action

Hierarchical to: FIA_UAU.1
Dependencies: FIA_UID.1

FIA_UAU.2.1 The TSF shall require each user to be successfully
authenticated before allowing any other TSF-mediated action on behalf of
that user.

FDP_ACC.1 Subset access control

Hierarchical to: No other components.
Dependencies: FDP_ACF.1

FDP_ACC.1.1 The TSF shall enforce the [assignment: example access control
policy] on [assignment: subjects, objects, and operations among subjects
and objects covered by the SFP].

FDP_ACF.1 Security attribute based access control

Hierarchical to: No other components.
Dependencies: FDP_ACC.1, FMT_MSA.3

Application note: This SFR's assignment operations are completed
consistently with the access control policy named in FDP_ACC.1.

FDP_ACF.1.1 The TSF shall enforce the [assignment: example access control
policy] to objects based on [assignment: security attributes].

FDP_ACF.1.2 The TSF shall enforce the following rules to determine if an
operation among controlled subjects and controlled objects is allowed:
[assignment: rules governing access].

FDP_ACF.1.3 The TSF shall explicitly authorise access of subjects to
objects based on the following additional rules: [assignment: no
additional rules].

FDP_ACF.1.4 The TSF shall explicitly deny access of subjects to objects
based on the following additional rules: [assignment: no additional
rules].

FDP_ETC.1 Export of user data without security attributes

Dependencies: [FDP_ACC.1 or FDP_IFC.1]

FDP_ETC.1.1 The TSF shall enforce the [assignment: example access control
policy] when exporting user data, controlled under the SFP(s), outside of
the TOE.

FDP_ETC.1.2 The TSF shall export the user data without the user data's
associated security attributes.

FDP_IFF.1 Simple security attributes

Hierarchical to: No other components.
Dependencies: FDP_IFC.1
FMT_MSA.3 not resolved. This TOE's configuration is static and has
therefore no concept of manageable security attributes, so this
dependency is not applicable.

FDP_IFF.1.1 The TSF shall enforce the [assignment: example information
flow control policy] based on [assignment: security attributes].

FCS_COP.1/Hash Cryptographic operation

Dependencies: [FCS_CKM.1 or FCS_CKM.5]
FCS_CKM.3

FCS_COP.1.1/Hash The TSF shall perform hashing in accordance with a
specified cryptographic algorithm [assignment: SHA-256] and cryptographic
key sizes [assignment: none] that meet the following: [assignment: FIPS
180-4].

FAU_GEN.2 User identity association

This is an objective SFR, included to strengthen accountability beyond
the mandatory baseline.

Dependencies: FAU_GEN.1, FIA_UID.1

FAU_GEN.2.1 The TSF shall associate each auditable event with the identity
of the user that caused the event.

FAU_SAR.1 Audit review

This SFR is optional, included only when a local audit review interface
is provided.

Dependencies: FAU_GEN.1

FAU_SAR.1.1 The TSF shall provide [assignment: authorised users] with the
capability to read [assignment: list of audit information] from the audit
records.

FTP_ITC.1 Inter-TSF trusted channel

This SFR is selection-based, included if the selection in FCS_COP.1
identifies a networked hashing use case.

FTP_ITC.1.1 The TSF shall be capable of using [selection: IPsec, TLS] to
provide a trusted communication channel.

7. Security Assurance Requirements

This ST claims the EAL2 assurance package augmented by ALC_FLR.2.

ADV_FSP.1 Basic functional specification

Developer action elements:
ADV_FSP.1.1D The developer shall provide a functional specification.

Content and presentation elements:
ADV_FSP.1.1C The functional specification shall describe the purpose and
method of use for each SFR-enforcing and SFR-supporting TSFI.

Evaluator action elements:
ADV_FSP.1.1E The evaluator shall confirm that the information provided
meets all requirements for content and presentation of evidence.

ADV_TDS.1 Basic design

AGD_OPE.1 Operational user guidance

AGD_PRE.1 Preparative procedures

ATE_IND.2 Independent testing - sample

AVA_VAN.2 Vulnerability analysis

ALC_FLR.2 Flaw reporting procedures

8. Security Requirements Rationale

O.EXAMPLE_OBJECTIVE
This objective addresses T.EXAMPLE_THREAT and P.EXAMPLE_POLICY by
requiring the TOE to enforce access control on every operation.

OE.EXAMPLE_OBJECTIVE
This objective addresses A.EXAMPLE_ASSUMPTION by requiring the operational
environment to physically protect the TOE.

FDP_ACC.1
This component satisfies O.EXAMPLE_OBJECTIVE by defining the scope of the
access control policy.

FDP_ACF.1
This component satisfies O.EXAMPLE_OBJECTIVE by defining the rules the
access control policy uses to grant or deny access.

FIA_UID.2
This component satisfies O.EXAMPLE_OBJECTIVE by requiring identification
before any other TSF-mediated action.

FIA_UAU.2
This component satisfies O.EXAMPLE_OBJECTIVE by requiring authentication
before any other TSF-mediated action.

FDP_ETC.1
This component satisfies O.EXAMPLE_OBJECTIVE by controlling how user data
is exported from the TOE.

FDP_IFF.1
This component satisfies O.EXAMPLE_OBJECTIVE by enforcing the example
information flow control policy.

FCS_COP.1/Hash
This component satisfies O.EXAMPLE_OBJECTIVE by providing the hashing
operation used elsewhere in the example access control policy.

FAU_GEN.2
This component satisfies O.EXAMPLE_OBJECTIVE by associating audit records
with the identity of the user who caused them.

FAU_SAR.1
This component satisfies O.EXAMPLE_OBJECTIVE by allowing authorised users
to review the audit trail.

FTP_ITC.1
This component satisfies O.EXAMPLE_OBJECTIVE by protecting the
communication channel used by the networked hashing use case.

9. TOE Summary Specification

The TOE identifies and authenticates every user before granting access,
then enforces the example access control policy on every subsequent
operation, mapped to FIA_UID.2, FIA_UAU.2, FDP_ACC.1, and FDP_ACF.1.
