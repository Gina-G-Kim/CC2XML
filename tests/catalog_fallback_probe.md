Catalog Fallback Probe ST
Version 1.0
September 18, 2026

1. Introduction

This Security Target (ST) describes the Catalog Fallback Probe TOE, a
minimal product used only to exercise cc_2022.xml catalog fallback: some
SFRs/SARs below are claimed by name only, inherited unchanged from the base
standard, without restating their hierarchical-to, dependencies, or element
text - the parser must fill those three fields from cc_2022.xml rather than
leaving them empty.

2. Conformance Claims

This ST is Part 2 extended and Part 3 conformant with Common Criteria
(CC:2022). It claims conformance to the EAL1 assurance package with no
augmentation. It does not claim conformance to any Protection Profile.

3. Security Problem Definition

T.PROBE
An attacker attempts to exercise the fallback logic path.

4.1 Security Objectives for the TOE

O.PROBE
The TOE shall generate and retain the evidence needed to exercise the
fallback logic.

4.2 Security Objectives for the Operational Environment

OE.PROBE
The operational environment does not interfere with the TOE's operation.

6. Security Functional Requirements

FAU_GEN.1 Audit data generation

Claimed unchanged from the base standard. Not restated here.

FIA_UID.2 User identification before any action

Claimed unchanged from the base standard. Not restated here.

7. Security Assurance Requirements

ADV_FSP.1 Basic functional specification

Claimed unchanged from the base standard. Not restated here.

8. Security Requirements Rationale

O.PROBE
This objective addresses T.PROBE by ensuring security-relevant events are
recorded and attributable to an identified user.

OE.PROBE
This objective addresses T.PROBE by requiring the operational environment
not to interfere with the TOE's own enforcement of O.PROBE.

FAU_GEN.1
This component satisfies O.PROBE by generating audit records for
security-relevant events.

FIA_UID.2
This component satisfies O.PROBE by requiring successful identification of
every user before any other TSF-mediated action.

9. TOE Summary Specification

The TOE generates audit records for security-relevant events and requires
successful identification before any other TSF-mediated action.
