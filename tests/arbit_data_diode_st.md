Arbit Data Diode 10GbE Security Target Lite
Version 1.13
05.12.2025
Sponsor: Arbit Cyber Defence Systems ApS
Developer: Arbit Cyber Defence Systems ApS

1. Introduction

The TOE is a one-way data diode for optical information. The increasing
threat from various actors to gain access to confidential company data or
cause unauthorized modifications to the IT infrastructure has forced many
companies to separate their production network from less trusted networks
such as the Internet. A data diode combines the advantages of physical
separation and automated transfer: it is the connection point between a
Sending network and a Receiving network, and it ensures that information
can only flow from the Sending Network to the Receiving Network, but not
the other way.

2. Conformance Claims

This Security Target claims conformance to Common Criteria (CC:2022), Part
2 conformant and Part 3 conformant, with a claimed Evaluation Assurance
Level of EAL7, augmented by ALC_FLR.1. This Security Target does not claim
conformance to any Protection Profile.

3. Security Problem Definition

T.DATA_LEAK
TA-SENDING and/or TA-RECEIVING threat agents may be able to manipulate the
INPUT and/or OUTPUT port such that RECEIVING-INFO is able to exit the TOE
through the INPUT port.

A.INTEGRATOR
The integrator who is performing the installation of the TOE is
well-trained and competent in the prevention of signal leakage and will
properly adhere to the TOE guidance.

A.PHYSICAL
The TOE and its interfaces will be physically protected from unauthorized
access and mechanical, electrical, optical, radiation or any other form of
physical influence.

A.POWER
Power supply to the TOE shall be 3.3 V +/-5%. The minimum current
capacity, both continuous and peak, shall be 500 mA.

P.ONE_WAY_FLOW
The TOE shall allow information to enter through the INPUT port and then
leave through the OUTPUT port and deny information flow from the OUTPUT
port to the INPUT port.

4.1 Security Objectives for the TOE

O.NO_RECEIVING_INFO
The TOE must ensure that no information that may have entered through the
OUTPUT port is able to leave through the INPUT port.

4.2 Security Objectives for the Operational Environment

OE.INTEGRATOR
The integrator who is performing the installation of the TOE shall be
well-trained and competent in the prevention of signal leakage and shall
properly adhere to the TOE guidance.

OE.PHYSICAL
The TOE and its interfaces shall be physically protected from unauthorized
access.

OE.POWER
Power supply to the TOE shall be 3.3 V +/-5%. The minimum current
capacity, both continuous and peak, shall be 500 mA.

5. Extended Components Definition

No additional extended components are needed and therefore none are
defined.

6. Security Functional Requirements

FDP_IFC.2 Complete information flow control

FDP_IFC.2.1 The TSF shall enforce the [assignment: One-Way SFP] on
[assignment: the subjects INPUT port and OUTPUT port] and all operations
that cause that information to flow to and from subjects covered by the
SFP.

FDP_IFC.2.2 The TSF shall ensure that all operations that cause any
information in the TOE to flow to and from any subject in the TOE are
covered by an information flow control SFP.

FDP_IFF.1 Simple security attributes

Hierarchical to: No other components.
Dependencies: FDP_IFC.1
FMT_MSA.3 not resolved. The TOE configuration is static and has therefore
no concept of manageable security attributes. This dependency is
therefore not applicable.

Application note: No security attributes are stated. Any instance of the
defined information type, independent of its further properties, is
covered by this SFR.

FDP_IFF.1.1 The TSF shall enforce the [assignment: One-Way SFP] based on
the following types of subject and information security attributes:
[assignment: subjects INPUT port and OUTPUT port].

FDP_IFF.1.2 The TSF shall permit an information flow between a controlled
subject and controlled information via a controlled operation if the
following rules hold: [assignment: information read from the INPUT port
shall allow the transformation operation f, from an optical signal to an
electrical signal, to write to the OUTPUT port; information read from the
OUTPUT port shall deny the transformation operation g, from an electrical
signal to an optical signal, to write to the INPUT port].

FDP_IFF.1.3 The TSF shall enforce the [assignment: rule in FDP_IFF.1.2
only].

FDP_IFF.1.4 The TSF shall explicitly authorise an information flow based
on the following rules: [assignment: no further rules].

FDP_IFF.1.5 The TSF shall explicitly deny an information flow based on the
following rules: [assignment: no further rules].

7. Security Assurance Requirements

The security assurance requirements for the TOE are the Evaluation
Assurance Level 7 components, augmented by ALC_FLR.1.

ADV_SPM.1 Formal TOE security policy model

ADV_SPM.1.1D The developer shall provide a formal security policy model
for the [assignment: One-Way SFP defined by FDP_IFC.2 and FDP_IFF.1].

ALC_FLR.1 Basic flaw remediation

8. Security Requirements Rationale

O.NO_RECEIVING_INFO
This objective addresses T.DATA_LEAK by ensuring that no information is
able to spill over inside the TOE from the OUTPUT port to the INPUT port.

OE.INTEGRATOR
This objective addresses A.INTEGRATOR and T.DATA_LEAK by ensuring that the
integrator who performs the installation of the TOE is well-trained and
competent in the prevention of signal leakage and properly adheres to the
TOE guidance.

OE.PHYSICAL
This objective addresses A.PHYSICAL and T.DATA_LEAK by ensuring that the
TOE and its interfaces are physically protected from unauthorized access.

OE.POWER
This objective addresses A.POWER and T.DATA_LEAK by ensuring that
components are operating within power supply specification.

FDP_IFC.2
This component satisfies O.NO_RECEIVING_INFO by ensuring that any
information flow in the TOE is covered by the One-Way SFP.

FDP_IFF.1
This component satisfies O.NO_RECEIVING_INFO by denying any information
from the OUTPUT port to leave through the INPUT port.

9. TOE Summary Specification

The TOE provides one security functionality, which represents the overall
TOE Security Function. The TOE implements the one-way data diode: a fiber
optic network cable is connected to the INPUT port and a receiver
connection is on the OUTPUT port. Information received on the INPUT port
is allowed to exit through the OUTPUT port, without further processing,
and no information can spill over to the INPUT port from the OUTPUT port.
This TSF is mapped to FDP_IFC.2 and FDP_IFF.1.
