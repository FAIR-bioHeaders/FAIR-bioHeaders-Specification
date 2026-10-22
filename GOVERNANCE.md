# Governance

## Current governance

FHR is maintained by David Molik and Adam Wright, who jointly hold authority over
the schema, the specification, the companion tools and releases. Changes are
proposed and discussed in public issues and pull requests, and decisions are
recorded there. Conduct and security reports follow CODE_OF_CONDUCT.md and
SECURITY.md, including the routing used when a report involves a maintainer.

No steering group exists and none is being formed at present. The steering-group
model below is documented for a future transition if the project grows; it has no
effect until David and Adam explicitly adopt it and complete its transition
checklist. The gaps raised in the #29 review — independent appeals and reviewer appointment
with deadlines, resignation/removal/vacancy rules including a sole maintainer, and
who rules on disputed conflicts — are drafted, not adopted, in the proposal below.

# Proposal under review (issue #36): appeals, vacancies and conflicts

This is a proposal under review for [issue #36](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/36). It is not adopted and has no effect until David and Adam adopt it and record an effective date. While unadopted, the current governance text above and CODE_OF_CONDUCT.md control; this section appoints no reviewer or successor, creates no deadline, and changes no repository access. David and Adam continue to jointly hold schema and release authority; no steering group exists.

The appeal and disputed-conflict clauses are drafted for the current two-maintainer model and, if the steering-group option is activated, for that group. The resignation, removal and vacancy clauses are drafted for the current maintainer model, including a sole-maintainer vacancy. Activating the steering group requires the group to adopt equivalent resignation, removal and vacancy clauses first; the transition checklist records that requirement.

**Roles used below.** The repository host is the service that controls repository ownership and access. Its ownership process handles access, ownership and succession; its abuse process handles conduct, harassment, security and abuse reports. This proposal does not assume that the host will accept a request, and a refusal leaves the matter unresolved under project rules. An eligible reviewer is a person with no role in the decision, report or removal under review, no conflict of interest, and written consent to serve. A requestor is the person asking for the appeal, ruling, removal decision or review. A person under review is the maintainer, group member or decision-maker whose conduct or decision is the subject. The gain-sole-authority bar is defined in the removal clauses.

## Independent reviewers and deadlines

When a clause below requires an independent reviewer and no eligible reviewer already holds the role, the requestor opens a call for candidates lasting at least seven days. The call is public unless the matter is a conduct, security or other confidential matter. Any contributor may propose a candidate, including the requestor and the person under review. A candidate must consent in writing and state that they have no involvement in the matter and no conflict of interest. A candidate may not be the requestor, a person under review, or a member of the body that made the decision.

For a confidential matter, the call is made privately to the repository host's abuse process and to eligible reviewers already known to the project. It does not identify the parties or the report, and no public notice is required. The same consent, selection, objection and deadline rules apply.

At the close of the call, the requestor records the names and declarations of the consenting candidates for the participants and, where the matter is not confidential, publishes them. If more than one remains, the requestor draws one by lot; if only one remains, that person is proposed. When a maintainer or group is the requestor and another member is not a party to the matter, that member draws the candidate. If no member is eligible, the requestor publishes the candidate names and applies a recorded random method; the requestor does not choose among them. The names and result are recorded so the selection can be checked. The proposed candidate is not appointed until the objection period below has run and any documented conflict raised during it has been resolved.

Each person under review, and the reporter or appellant if different, may object once, without giving reasons, within seven days of being told the proposed candidate. The reporter or appellant may object even if they are the requestor or proposed the candidate. Any contributor, or in a confidential matter any participant, may raise a documented conflict against the candidate in the same period; the candidate may answer in writing, and the requestor records the answer and any reasons for treating the conflict as resolved. If a candidate declines, an objection is used, or a documented conflict remains unresolved when the period ends, the requestor draws another consenting candidate by the same method.

A candidate is appointed when the objection period has run, no timely objection remains, and the candidate's written consent and conflict declaration are recorded. The appointment is recorded publicly for a non-confidential matter, or in the private conduct or security record for a confidential one, with sensitive details omitted. No candidate is appointed on a nomination alone: the call, any lot, the written declaration and the objection period together are the confirmation. If no candidate is appointed within twenty-one days of the call opening, appointment fails. The requestor records the failure and may escalate the matter to the repository host's ownership or abuse process. The review then does not proceed as a project decision.

An appointed reviewer acknowledges the matter within seven days and records a decision within thirty days of appointment. The reviewer may extend the deadline once, by no more than fourteen days, by telling the requestor and each person under review before the original thirty days expire. If no decision is recorded by the extended deadline, the review ends without a project decision; the requestor records the failure and may escalate to the host process. The failure does not itself change the decision, removal or freeze in effect when the review began; only the host process may change it. A decision recorded after the extended deadline is not a project decision.

## Appeals

A person directly affected by a recorded decision may appeal it within fourteen days of the decision being recorded. Under the current model, the reviewer is the maintainer who did not take part in the decision. Under an active steering group, the reviewer is a non-conflicted member who took no part. If no eligible reviewer is available — for example, because both maintainers made or are party to the decision — the appellant requests an independent reviewer under the clauses above.

The reviewer acknowledges the appeal within seven days and records an outcome within the deadline and extension limit above. The outcome is one of: uphold the decision and state the reasons; overturn it and substitute a new decision; or remand it to the deciding group for a fresh decision that addresses the conflict or error the appeal identified. Decisions that were public get a public outcome; conduct and security appeals follow the private routing in CODE_OF_CONDUCT.md.

If no independent reviewer is appointed by the appointment deadline, or no outcome is recorded by the decision deadline, the appeal ends unresolved: the challenged decision remains in effect, the failure is recorded, and the appellant may escalate to the repository host's ownership or abuse process. Recording the failure does not suspend the decision.

## Resignation, removal and vacancies

### Resignation

Authority is held jointly. A maintainer may resign by written notice to the other maintainer, effective on the date stated in the notice or, if none is stated, when it is given. If no other maintainer is serving, the resignation is given by written public notice in the repository and a written request to the repository host's ownership process to record the vacancy, and takes effect on the date stated or when both are sent. The resignation is recorded in this file by the resigning maintainer or, if they cannot, by the host ownership process. A resignation does not appoint a successor.

When a maintainer leaves, the remaining maintainer holds authority alone only until a successor accepts the role. While there is only one maintainer, a change that normally needs a second, independent reviewer waits for one, unless it is an urgent security fix; an urgent fix made under the single maintainer is recorded and reviewed within fourteen days of a second maintainer joining.

### Removal

A maintainer may be removed for cause: abuse of authority, a serious or repeated breach of CODE_OF_CONDUCT.md or SECURITY.md, or extended failure to take part in decisions. Removal needs a recorded decision with reasons, after the affected maintainer is told the concerns and given at least fourteen days to respond.

The gain-sole-authority bar is this: a maintainer who would become the sole maintainer if a removal took effect may open, notify and administer the case, but may not make or join the final removal decision. The bar applies to the decision, not to initiating the case.

#### Removal of one of two maintainers

The other maintainer opens the case, tells the subject and invites a response, but the gain-sole-authority bar prevents that maintainer from deciding alone. An independent removal reviewer is appointed under the independent-reviewer clauses above at the request of the other maintainer. The subject may object once under that procedure.

The reviewer decides on the recorded evidence, records the outcome and reasons, and must decide within the deadline above. The decision is sent to the repository; the other maintainer records it in this file, or the host ownership process records it if that maintainer cannot or will not.

If no reviewer is appointed by the appointment deadline, or no decision is recorded by the decision deadline, no project decision is made: the other maintainer records the failure and escalates the case to the repository host's ownership or abuse process. The project does not remove a maintainer without a decision by an eligible reviewer. A removal decision takes effect only when it is recorded in this file and the repository host's ownership process gives it effect; a project decision alone does not revoke repository access.

#### Removal of both maintainers

When both maintainers are the subject of a removal case, the person who reported the concern or requested removal opens it, tells each subject the concerns and gives them at least fourteen days to respond, and requests the independent reviewer under the clauses above; each subject may object once. The reviewer decides within the deadline above. The requester records the decision in this file; if they lack access, the repository host's process records it. A removal decision in this case takes effect only when recorded and the repository host's ownership process gives it effect. If no reviewer is appointed by the appointment deadline, or no decision is recorded by the decision deadline, the case goes to the repository host's ownership or abuse process. A reviewer appointed for this case also serves as the independent reviewer under CODE_OF_CONDUCT.md for the same case's conduct matters and as the conflict arbiter for disputes arising from it. If no reviewer is appointed, those functions follow the host escalation, not a remaining maintainer or a subject.

#### Removal of a sole maintainer

When only one maintainer serves, a person directly affected, or a person who reported a conduct or security concern, may request removal in writing to the repository host's abuse or ownership process and, for a non-confidential matter, in the repository. The requester or the host process tells the sole maintainer the concerns and gives them at least fourteen days to respond. An independent removal reviewer is appointed under the clauses above at the request of the requester, who may not be the subject; the subject may object once. The reviewer decides on the recorded evidence and records the outcome and reasons within the deadline above. The requester records the decision in this file; if they lack access, the host process records it.

If no reviewer is appointed by the appointment deadline, or no decision is recorded by the decision deadline, or the maintainer does not give effect to a removal decision, the matter goes to the repository host's ownership or abuse process. The project cannot give effect to a removal of a sole maintainer by itself and cannot revoke repository access; the host ownership process is required. A removal decision alone does not remove the maintainer's access.

#### Vacancies

While a maintainer remains, a vacancy is filled by a public call lasting at least fourteen days. The remaining maintainer appoints a successor who accepts the role and records the appointment in this file. The remaining maintainer may not appoint a person who is the subject of a pending removal or a person under review in that case.

If the remaining maintainer is the subject of a pending removal or a party to a removal case, that maintainer may not fill the vacancy: the public call proceeds, but the appointment is confirmed by an independent reviewer appointed under the clauses above at the request of the person who requested the removal or, if none, any contributor; if no reviewer is appointed, the repository host's process confirms the successor.

If both seats become empty, recovery depends on a successor designated and consenting in advance; the project cannot appoint a successor by itself. Within thirty days of adoption of this proposal, and whenever the record changes, each maintainer records a designated successor and that person's written consent in a designated-successor record in this file, and keeps the record current. A designation or withdrawal takes effect after seven days' public notice in this file by the person making the change, except that a designee may withdraw immediately, with the withdrawal recorded in this file.

If both seats become empty and a designated successor has consented and still consents, the departing maintainers, or the repository host's ownership process if they cannot, invite that person in writing to accept. If they accept within fourteen days, they record their acceptance in this file and the repository host's ownership process transfers the access needed for the role.

Both steps are required: recording acceptance does not by itself grant access, and a host transfer without the recorded acceptance does not make the person a maintainer under this proposal. If the successor has no write access when they accept, the host ownership process records the acceptance together with the transfer. The freeze ends only when both steps are complete. If the host transfer does not complete within thirty days of acceptance, the freeze continues and there is no maintainer authority until it does.

If no designated, consenting successor exists, or the designee declines or does not respond within fourteen days, the schema and releases stay frozen — no new contract changes or releases — and no project decision may be made.

Any contributor may still open a public call to find a volunteer, but authority is transferred only through the repository host's ownership process; where the vacancy arose from a conduct or security matter, the host's abuse process is also available. A volunteer found this way follows the same two steps: recorded acceptance in this file and a host ownership transfer. Until that transfer completes there is no maintainer authority. Security fixes may be prepared privately in the meantime but are not published until a maintainer is in place.

## Disputed conflicts of interest

A disputed conflict of interest — a disagreement over whether a person is conflicted in a particular decision — is ruled on by the **conflict arbiter**. Under the current model the conflict arbiter is the maintainer who is not a party to the dispute: currently whichever of David Molik or Adam Wright is not a party. Under an active steering group, the arbiter is a non-conflicted group member chosen by the group.

If the conflict arbiter is themselves conflicted, is a party, declines, or does not respond within fourteen days, the ruling passes to an independent reviewer appointed under the independent-reviewer clauses above at the request of the person who asked for the ruling. The arbiter's agreement is not required, and an arbiter who declines or is a party may object once at most.

If no reviewer is appointed by the appointment deadline, or no ruling is recorded by the decision deadline, the ruling request goes to the repository host's ownership or abuse process. A maintainer who opens a removal case is a party to that case for this purpose, so a disputed conflict of interest in it goes to the independent removal reviewer; if none is appointed, it follows the host escalation.

The ruling is recorded with reasons, and the person who asked for it is told the outcome.

The proposal in this section remains unadopted and creates no office, reviewer, successor, deadline or access change until David and Adam record its adoption.

# Future option: steering group (not active)

## Goals and options

Keep decisions transparent, make review possible for users and repository
operators, and sustain a small provenance standard without adding unnecessary
process. A two-person maintainer model is simple but has continuity risks. A
formal external foundation is disproportionate at current scale. A small rotating
steering group with public decisions is the recommended successor model.

## Recommended model

Create a steering group of three to five members, including at least one schema
maintainer, one converter maintainer, and one genome-data user or repository
representative. No outside organization is presumed to have accepted a role.
Members serve two-year terms, staggered initially for continuity. Contributors
with demonstrated project participation may nominate themselves or others in a
public nomination period. The existing group selects replacements by majority
vote, records its rationale, and invites objections for fourteen days. A member
may serve two consecutive terms before a one-term break.

Maintainers review and implement changes and administer repositories. The group
approves changes to the metadata contract, compatibility policy, and governance.
Routine documentation and implementation fixes need one independent maintainer
review and passing checks. Reviewers declare conflicts; authors do not approve
their own changes. If no independent reviewer is available, the group appoints
one under the issue #36 procedure before approval; if none is appointed by the
deadline, the change is not approved and the failure is recorded.

## Decisions and releases

Schema proposals state the use case, field semantics, examples, mappings,
compatibility, and effects on tools. Discuss publicly for at least fourteen days,
except urgent security fixes. Seek consensus first; unresolved proposals use a
recorded vote. Quorum is a majority of non-conflicted members, with at least two
participants. Approval needs a majority of participating voters. A tie defers the
proposal for revision. Appeals receive a fresh review by non-conflicted members
who took no part in the decision; if quorum cannot be reached, defer and recruit
an independent temporary reviewer under the issue #36 procedure. The proposed
appointment and appeal deadlines, one-extension limit and outcomes are in the
issue #36 section above.

Release changes are documented in a changelog. Package/release versioning and
schemaVersion are distinct. Additive optional fields may be minor releases;
required-field/type changes need explicit compatibility review and a migration
plan. Deprecations must be documented for at least one release before removal,
unless a security issue makes that impractical. Record emergency decisions and
obtain retrospective group review within fourteen days.

Governance amendments follow the public proposal process and need two-thirds of
non-conflicted group members, with quorum. Review the model annually and publish
a short record of membership and decisions. Participation remains subject to the
code of conduct and its documented private reporting and appeal routing.

## Transition and adoption checklist

- [ ] David and Adam approve or revise this model and record an effective date.
- [ ] Publish nominations and appoint the initial group, confirming consent and roles.
- [ ] Record initial term lengths, voting membership, and contact channels.
- [ ] Hand over repository administration, release credentials, and archival ownership;
      grant only the access needed for each role.
- [ ] Record a first meeting and establish the public decision log.
- [ ] Update CONTRIBUTING and this status banner to distinguish effective rules from drafts.
- [ ] Adopt or revise the proposed appeals, independent-reviewer, resignation, removal, vacancy and conflict-of-interest rules from issue #36, including the sole-maintainer case.
- [ ] Before activating the steering group, adopt equivalent group removal and vacancy rules.

Documenting this option does not appoint members or transfer authority.
