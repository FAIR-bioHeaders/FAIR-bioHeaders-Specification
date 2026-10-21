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
checklist. The gaps raised in the #29 review — independent appeals with a
deadline, removal/resignation/vacancy rules, and who rules on disputed conflicts —
are drafted, not adopted, in the proposal below.

# Proposal under review (issue #36): appeals, vacancies and conflicts

This is a proposal under review for [issue #36](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/36). It is not adopted and has no effect until David and Adam adopt it and record an effective date. It is written to apply both to the current two-maintainer model and, if the steering-group option is activated, to that group. David and Adam continue to jointly hold schema and release authority; no steering group exists.

## Appeals

A person directly affected by a recorded decision may appeal it. The appeal is heard by someone independent of the group that made the decision: under the current model, by the maintainer who did not take part in the decision; under the steering group, by non-conflicted members who took no part in it. The person appealing asks within fourteen days of the decision being recorded. The reviewer acknowledges the appeal within seven days and records an outcome within thirty days; if more time is needed, the reviewer tells the requester a new date before the thirty days elapse.

The outcome is one of: uphold the decision and state the reasons; overturn it and substitute a new decision; or remand it to the deciding group for a fresh decision that addresses the conflict or error the appeal identified. Decisions that were public get a public outcome; conduct and security appeals follow the private routing in CODE_OF_CONDUCT.md. If no independent reviewer is available — for example, because both maintainers made or are party to the decision — the appeal goes to the independent reviewer appointed under CODE_OF_CONDUCT.md, and the limitation is recorded until that reviewer is in place.

## Resignation, removal and vacancies

Authority is held jointly. A maintainer may resign at any time by written notice to the other maintainer, effective on the date stated in the notice or, if none is stated, when it is given. When a maintainer leaves, the remaining maintainer holds authority alone only until a successor accepts the role. While there is only one maintainer, a change that normally needs a second, independent reviewer waits for one, unless it is an urgent security fix; an urgent fix made under the single maintainer is recorded and reviewed within fourteen days of a second maintainer joining.

A maintainer may be removed for cause: abuse of authority, a serious or repeated breach of CODE_OF_CONDUCT.md or SECURITY.md, or extended failure to take part in decisions. Removal needs a recorded decision with reasons, after the affected maintainer is told the concerns and given at least fourteen days to respond. In the current two-maintainer model, the maintainer who would gain sole authority does not decide the removal: the uninvolved maintainer makes the recorded decision, and when both maintainers are the subject the decision goes to the independent reviewer appointed under CODE_OF_CONDUCT.md.

A vacancy is filled by a public call lasting at least fourteen days. The remaining maintainer, or the independent reviewer appointed under CODE_OF_CONDUCT.md when no maintainer remains, appoints a successor who accepts the role and is recorded in this file. If both maintainers leave at once, the schema and releases are frozen — no new contract changes or releases — until at least one successor accepts. Security fixes may be prepared privately in the meantime but are not published until a maintainer is in place.

## Disputed conflicts of interest

A disputed conflict of interest — a disagreement over whether a person is conflicted in a particular decision — is ruled on by the **conflict arbiter**. Under the current model the conflict arbiter is the maintainer who is not a party to the dispute: currently whichever of David Molik or Adam Wright is not a party. If the conflict arbiter is themselves conflicted, is a party, is one of the two maintainers in the dispute, declines, or does not respond within fourteen days, the ruling passes to the independent reviewer appointed under CODE_OF_CONDUCT.md. The ruling is recorded with reasons, and the person who asked for it is told the outcome.

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
their own changes. If no independent reviewer is available, the group records
that limitation and appoints a reviewer before approval.

## Decisions and releases

Schema proposals state the use case, field semantics, examples, mappings,
compatibility, and effects on tools. Discuss publicly for at least fourteen days,
except urgent security fixes. Seek consensus first; unresolved proposals use a
recorded vote. Quorum is a majority of non-conflicted members, with at least two
participants. Approval needs a majority of participating voters. A tie defers the
proposal for revision. Appeals receive a fresh review by non-conflicted members
who took no part in the decision; if quorum cannot be reached, defer and recruit
an independent temporary reviewer. The proposed appeal deadline and outcomes are
in the issue #36 section above.

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
- [ ] Adopt or revise the proposed appeals, resignation, removal, vacancy and conflict-of-interest rules from issue #36.

Documenting this option does not appoint members or transfer authority.
