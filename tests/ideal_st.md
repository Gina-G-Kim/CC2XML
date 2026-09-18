Example Access Control System Security Target
Version 1.0
September 14, 2026

1. Introduction

This Security Target (ST) describes the Example Access Control System (the
TOE), a software product that authenticates users and mediates access to
protected resources. This ST claims conformance to Common Criteria (CC:2022),
Part 2 extended and Part 3 conformant, at assurance level EAL1.

2. Conformance Claims

This ST is Part 2 extended and Part 3 conformant with Common Criteria
(CC:2022). It claims conformance to the EAL1 assurance package with no
augmentation. It does not claim conformance to any Protection Profile.

3. Security Problem Definition

T.UNAUTH_ACCESS
An attacker who is not an authorized user of the TOE attempts to access
protected resources without first being identified and authenticated,
resulting in unauthorized disclosure or modification of protected data.

T.DATA_DISCLOSE
An authorized user of the TOE performs actions that are not recorded,
preventing an administrator from later determining who accessed protected
resources and when.

A.PHYSICAL
The environment in which the TOE operates provides physical protection
commensurate with the value of the protected resources, preventing an
attacker from bypassing the TOE through physical access to its underlying
platform.

A.MANAGE
The TOE is installed, configured, and managed by one or more competent
administrators who follow the guidance documentation and do not act in a
careless or hostile manner.

P.ACCOUNTABILITY
Users of the TOE shall be held accountable for their security-relevant
actions.

4.1 Security Objectives for the TOE

O.IDENTIFY
The TOE shall require each user to be successfully identified before
allowing any other TSF-mediated action on behalf of that user.

O.ACCESS_CONTROL
The TOE shall enforce an access control policy that permits only
authenticated, authorized users to access protected resources.

O.AUDIT
The TOE shall generate audit records of security-relevant actions and
associate each record with the identity of the user who performed it.

4.2 Security Objectives for the Operational Environment

OE.PHYSICAL
The operational environment shall provide physical protection for the TOE
commensurate with the value of the protected resources.

OE.MANAGE
The operational environment shall ensure that the TOE is managed by
competent, non-hostile administrators who follow the guidance documentation.

5. Extended Components Definition

FCS_RBG_EXT.1 Random bit generation
Family behaviour: this family defines requirements for random bit
generation used by the TSF.
Component levelling: FCS_RBG_EXT.1 is not hierarchical to any other
component.
Hierarchical to: No other components.
Dependencies: No dependencies.
FCS_RBG_EXT.1.1 The TSF shall perform all random bit generation services in
accordance with a deterministic random bit generator algorithm seeded by an
entropy source.

6. Security Functional Requirements

FIA_UID.2 User identification before any action
Hierarchical to: FIA_UID.1 Timing of identification
Dependencies: No dependencies.
FIA_UID.2.1 The TSF shall require each user to be successfully identified
before allowing any other TSF-mediated actions on behalf of that user.

FIA_UAU.2 User authentication before any action
Hierarchical to: FIA_UAU.1 Timing of authentication
Dependencies: FIA_UID.1
FIA_UAU.2.1 The TSF shall require each user to be successfully
authenticated before allowing any other TSF-mediated actions on behalf of
that user.

FMT_SMF.1 Specification of management functions
Hierarchical to: No other components.
Dependencies: No dependencies.
FMT_SMF.1.1 The TSF shall be capable of performing the following management
functions: [assignment: management of access control rules, management of
user accounts].

FMT_SMR.1 Security roles
Hierarchical to: No other components.
Dependencies: FIA_UID.1
FMT_SMR.1.1 The TSF shall maintain the roles [assignment: administrator,
authenticated user].
FMT_SMR.1.2 The TSF shall be able to associate users with roles.

FMT_MSA.1 Management of security attributes
Hierarchical to: No other components.
Dependencies: FDP_ACC.1, FMT_SMR.1, FMT_SMF.1
FMT_MSA.1.1 The TSF shall enforce the [assignment: access control policy]
to restrict the ability to [selection: modify, delete] the security
attributes [assignment: resource access rules] to [assignment:
administrator].

FMT_MSA.3 Static attribute initialisation
Hierarchical to: No other components.
Dependencies: FMT_MSA.1, FMT_SMR.1
FMT_MSA.3.1 The TSF shall enforce the [assignment: access control policy] to
provide [selection: restrictive] default values for security attributes
that are used to enforce the SFP.
FMT_MSA.3.2 The TSF shall allow the [assignment: administrator] to specify
alternative initial values to override the default values when an object or
information is created.

FDP_ACC.1 Subset access control
Hierarchical to: No other components.
Dependencies: FDP_ACF.1
FDP_ACC.1.1 The TSF shall enforce the [assignment: access control policy]
on [assignment: authenticated users, protected resources, read and write
operations].

FDP_ACF.1 Security attribute based access control
Hierarchical to: No other components.
Dependencies: FDP_ACC.1, FMT_MSA.3
FDP_ACF.1.1 The TSF shall enforce the [assignment: access control policy]
to objects based on the following: [assignment: user identity, resource
owner, resource access rules].
FDP_ACF.1.2 The TSF shall enforce the following rules to determine if an
operation among controlled subjects and controlled objects is allowed:
[assignment: a user may access a resource only if the resource access
rules for that resource permit the user's role].
FDP_ACF.1.3 The TSF shall explicitly authorise access of subjects to
objects based on the following additional rules: [assignment: none].
FDP_ACF.1.4 The TSF shall explicitly deny access of subjects to objects
based on the following additional rules: [assignment: none].

FAU_GEN.1 Audit data generation
Hierarchical to: No other components.
Dependencies: FPT_STM.1
FAU_GEN.1.1 The TSF shall be able to generate an audit record of the
following auditable events: [assignment: start-up and shutdown of the audit
functions, all auditable events for the not specified level of audit, user
authentication attempts, access control decisions].
FAU_GEN.1.2 The TSF shall record within each audit record at least the
following information: [assignment: date and time of the event, type of
event, subject identity, outcome of the event].

FAU_GEN.2 User identity association
Hierarchical to: No other components.
Dependencies: FAU_GEN.1, FIA_UID.1
FAU_GEN.2.1 The TSF shall associate each auditable event with the identity
of the user that caused the event.

FPT_STM.1 Reliable time stamps
Hierarchical to: No other components.
Dependencies: No dependencies.
FPT_STM.1.1 The TSF shall be able to provide reliable time stamps for its
own use.

7. Security Assurance Requirements

This ST claims the EAL1 assurance package, consisting of the following
security assurance requirements.

ADV_FSP.1 Basic functional specification
Hierarchical to: No other components.
Dependencies: No dependencies.
Developer action elements:
ADV_FSP.1.1D The developer shall provide a functional specification.
ADV_FSP.1.2D The developer shall provide a tracing from the functional
specification to the SFRs.
Content and presentation elements:
ADV_FSP.1.1C The functional specification shall describe the purpose and
method of use for each SFR-enforcing and SFR-supporting TSFI.
ADV_FSP.1.2C The functional specification shall identify all parameters
associated with each SFR-enforcing and SFR-supporting TSFI.
ADV_FSP.1.3C The functional specification shall provide rationale for the
implicit categorisation of interfaces as SFR-non-interfering.
ADV_FSP.1.4C The tracing shall demonstrate that the SFRs trace to TSFIs in
the functional specification.
Evaluator action elements:
ADV_FSP.1.1E The evaluator shall confirm that the information provided
meets all requirements for content and presentation of evidence.
ADV_FSP.1.2E The evaluator shall determine that the functional
specification is an accurate and complete instantiation of the SFRs.

AGD_OPE.1 Operational user guidance
Hierarchical to: No other components.
Dependencies: ADV_FSP.1
Developer action elements:
AGD_OPE.1.1D The developer shall provide operational user guidance.
Content and presentation elements:
AGD_OPE.1.1C The operational user guidance shall describe, for each user
role, the user-accessible functions and privileges that should be
controlled in a secure processing environment.
AGD_OPE.1.2C The operational user guidance shall describe, for each user
role, how to use the available interfaces provided by the TOE in a secure
manner.
AGD_OPE.1.3C The operational user guidance shall describe, for each user
role, the available functions and interfaces, in particular all security
parameters under the control of the user.
AGD_OPE.1.4C The operational user guidance shall clearly present each type
of security-relevant event relative to the user-accessible functions that
need to be performed.
AGD_OPE.1.5C The operational user guidance shall identify all possible
modes of operation of the TOE, including operation following failure or
operational error.
AGD_OPE.1.6C The operational user guidance shall describe the security
measures to be followed in order to fulfil the security objectives for the
operational environment.
AGD_OPE.1.7C The operational user guidance shall be clear and reasonable.
Evaluator action elements:
AGD_OPE.1.1E The evaluator shall confirm that the information provided
meets all requirements for content and presentation of evidence.

AGD_PRE.1 Preparative procedures
Hierarchical to: No other components.
Dependencies: No dependencies.
Developer action elements:
AGD_PRE.1.1D The developer shall provide the TOE, including its
preparative procedures.
Content and presentation elements:
AGD_PRE.1.1C The preparative procedures shall describe all the steps
necessary for secure acceptance of the delivered TOE.
AGD_PRE.1.2C The preparative procedures shall describe all the steps
necessary for secure installation of the TOE and for the secure
preparation of the operational environment.
Evaluator action elements:
AGD_PRE.1.1E The evaluator shall confirm that the information provided
meets all requirements for content and presentation of evidence.
AGD_PRE.1.2E The evaluator shall apply the preparative procedures to
confirm that the TOE can be prepared securely for operation.

8. Security Requirements Rationale

O.IDENTIFY
This objective addresses T.UNAUTH_ACCESS by ensuring that every user is
identified before the TOE performs any TSF-mediated action on that user's
behalf.

O.ACCESS_CONTROL
This objective addresses T.UNAUTH_ACCESS by ensuring that only
authenticated, authorized users can access protected resources.

O.AUDIT
This objective addresses T.DATA_DISCLOSE and P.ACCOUNTABILITY by ensuring
that security-relevant actions are recorded together with the identity of
the user who performed them.

OE.PHYSICAL
This objective addresses A.PHYSICAL by requiring the operational
environment to provide physical protection for the TOE.

OE.MANAGE
This objective addresses A.MANAGE by requiring the operational environment
to ensure the TOE is managed by competent, non-hostile administrators.

FIA_UID.2
This component satisfies O.IDENTIFY by requiring successful identification
of every user before any other TSF-mediated action.

FIA_UAU.2
This component satisfies O.ACCESS_CONTROL by requiring successful
authentication of every user before any other TSF-mediated action.

FDP_ACC.1
This component satisfies O.ACCESS_CONTROL by defining the scope of the
access control policy enforced by the TOE.

FDP_ACF.1
This component satisfies O.ACCESS_CONTROL by defining the rules the access
control policy uses to grant or deny access to protected resources.

FMT_MSA.1
This component satisfies O.ACCESS_CONTROL by restricting management of the
access control policy's security attributes to the administrator role.

FMT_MSA.3
This component satisfies O.ACCESS_CONTROL by ensuring restrictive default
values are used for newly created resources' access control attributes.

FMT_SMF.1
This component satisfies O.ACCESS_CONTROL by providing the management
functions the administrator role uses to configure the access control
policy.

FMT_SMR.1
This component satisfies O.ACCESS_CONTROL by maintaining the administrator
and authenticated user roles the access control policy relies on.

FAU_GEN.1
This component satisfies O.AUDIT by generating audit records of
security-relevant events.

FAU_GEN.2
This component satisfies O.AUDIT by associating each audit record with the
identity of the user that caused the event.

FPT_STM.1
This component satisfies O.AUDIT by providing the reliable time stamps
audit records depend on.

FCS_RBG_EXT.1
This component satisfies O.ACCESS_CONTROL by generating the random values
used to construct unpredictable session credentials.

9. TOE Summary Specification

The TOE implements identification and authentication using a local user
database; every action is mediated by an access control policy that
consults each resource's access control rules before permitting a read or
write operation; and every security-relevant action is recorded in an
audit trail together with a reliable time stamp and the acting user's
identity.
