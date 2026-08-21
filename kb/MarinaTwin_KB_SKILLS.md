# Юридические методики (скилы) Фёдора

_Полный модуль базы знаний Фёдора (ATLAS). Каждый раздел — отдельный исходный документ._

ИСХОДНЫЙ ДОКУМЕНТ: skills/arbitration-clause-design-review.md

[RU] Темы: арбитраж, арбитражная оговорка, разрешение споров, место арбитража (seat), выбор арбитражного института (ICC, LCIA, SIAC, HKIAC), применимое право, исполнение решения, трансграничные договоры.

---
name: arbitration-clause-design-review
description: >-
  Draft, review and stress-test arbitration clauses in commercial contracts,
  with guidance on seat, institution, rules, confidentiality, governing law
  and commercial fit. Use whenever a user asks to draft or review a dispute
  resolution or arbitration clause, compare arbitral institutions (ICC, LCIA,
  SIAC, HKIAC, etc.), choose a seat of arbitration, assess enforceability of
  an award, or negotiate dispute resolution provisions in cross-border
  agreements. Produces a clean clause, a severity-rated issue list, proposed
  fixes, and negotiation arguments.
metadata:
  author: "Hafez Virjee"
  version: "2026"
---

# Arbitration Clause Design and Review
## Purpose
Use this skill to help users draft, review and stress-test arbitration clauses in commercial contracts.
The skill is designed to produce practical, usable outputs:
- a clean arbitration clause;
- a concise review of an existing clause;
- a severity-rated list of issues;
- proposed fixes or revised wording;
- optional reasoning, recommendation reports and negotiation arguments.
The skill should be quick and frictionless for non-specialist users, while allowing sophisticated users to request deeper analysis.
## Subtitle
A commercial arbitration workflow for drafting, reviewing and stress-testing dispute resolution clauses.
## Author
Hafez Virjee
## Methodological note
This workflow draws on practical arbitration experience, arbitral-procedure design, and the Delos GAP's focus on arbitral seats, enforcement, legal specificities and cross-border dispute planning.
It is a drafting and issue-spotting workflow. It is not legal advice. Arbitration clauses can have significant consequences under the law of the seat, the governing law, and the laws of enforcement jurisdictions. The user should obtain legal advice before finalising the clause, especially where the transaction is high-value, complex, cross-border, regulated, or involves state-linked, sovereign, mandatory-law or enforcement-sensitive issues.
# When to use this skill
Use this skill when the user asks to:
- draft an arbitration clause;
- review an arbitration clause;
- improve a dispute resolution clause;
- identify pathologies in an arbitration agreement;
- assess whether an arbitration clause is workable;
- select or assess a seat of arbitration;
- select or assess arbitral rules or an arbitral institution;
- produce a clause for a commercial contract;
- generate internal or counterparty-facing arguments for an arbitration clause;
- stress-test whether a clause fits the commercial context.
This skill is for commercial arbitration clauses in contracts.
# When not to use this skill, or when to refer out
Do not attempt to provide a complete solution where the matter primarily involves:
- investment arbitration or treaty-based dispute resolution;
- consumer arbitration;
- employment arbitration where mandatory law may restrict arbitration;
- sports, disciplinary or regulatory arbitration;
- sanctions-heavy or export-control-sensitive matters;
- complex multi-contract or project-finance structures requiring bespoke consolidation or joinder analysis. Note: the skill may still provide the general commercial arbitration architecture for multi-party scenarios; the exclusion applies to bespoke consolidation or joinder analysis, not to the architecture itself.
Where one of these issues arises, do not simply refuse to help unless the whole task is outside scope. Instead:
1. assist with the commercial arbitration clause to the extent appropriate;
2. identify the specific issue that requires specialist advice;
3. explain why that issue matters;
4. recommend that the user obtain legal advice before finalising the clause.

## Multi-party and multi-contract scenarios
Where a scenario involves multiple parties, multiple contracts, or both, provide the commercial arbitration architecture first before flagging specialist referral. Do not retreat to a specialist referral without first providing the framework.

The architecture guidance for complex multi-party scenarios should include, where relevant:
- institution selection: apply the general institution-selection criteria, with the additional factor that the chosen institution's rules on consolidation and joinder should be assessed for compatibility with the multi-party structure. Several major institutions have well-developed multi-party frameworks; the right choice depends on the parties, geography, value, and priorities as in any other scenario;
- a principal arbitration clause in the main contract, with back-to-back arbitration clauses in related contracts that mirror the seat, institution, and rules;
- consolidation and joinder provisions, where the chosen institution's rules support them;
- whether the scenario raises issues outside scope (bespoke project finance structure, non-identical parties across multiple tiers) that require specialist advice.

Flag specialist referral after providing the framework, not instead of it. Do not produce detailed consolidation or joinder wording unless the user requests it or the structure is straightforward enough to make standard wording appropriate.
# State-linked, SOE and public-counterparty contracts
Contracts involving SOEs, state entities, public bodies or sovereign-related parties are not automatically outside scope. Many such contracts are ordinary commercial contracts, and the skill may assist with arbitration clause design where the party appears to be acting in a commercial capacity.
However, if immunity, authority, capacity, procurement law, public law, sanctions, enforcement, treaty protection or other sovereign-related issues may be relevant, the skill should flag those issues specifically and recommend specialist legal advice before finalising the clause.
Do not refuse to assist simply because a counterparty is an SOE or public body. Instead:
1. assist with the commercial arbitration clause to the extent appropriate;
2. identify the specific state-linked issue that requires legal review;
3. explain briefly why that issue matters;
4. avoid giving a definitive view on immunity, authority, public-law validity or enforcement unless properly supported.
Example wording:
I can help with the commercial arbitration architecture, but because the counterparty is state-linked, the clause should be reviewed for authority, capacity, immunity, enforcement and any applicable procurement or public-law requirements before it is finalised.
If the contract is a concession, public-private partnership, treaty-linked arrangement, regulated infrastructure project, or another arrangement where the state is acting in a sovereign or public-law capacity, treat the matter as higher risk. The skill may still identify drafting components or provide a provisional clause, but it must clearly state that specialist advice is required before use.
# Core design principle
Follow progressive disclosure.
## Effort mode and skill instructions
This skill contains specific analytical instructions that override default model behaviour and weightings. These instructions apply regardless of the complexity of the request, the brevity of the user's prompt, or any inference that a "lighter" response is appropriate.

In particular:
- The governing law analysis (see below) must always follow the structured framework set out in this skill, not default model assumptions about neutral or internationally recognised governing laws.
- The institution selection and cost sense-check instructions (see below) must always be followed as analytical steps, including the internal Delos cost sense-check, regardless of how simple or routine the request appears. Whether the result is surfaced publicly depends on the public-surfacing criteria in the institution selection section.

Do not treat these as optional steps that can be skipped when the user's request is short or the context seems straightforward. The governing law framework and cost sense-check are mandatory analytical steps. The cost comparison should be surfaced in the output only where the public-surfacing criteria in the institution selection section are met.

Default behaviour:
1. Ask as few questions as possible.
2. Use uploaded or pasted documents first.
3. Extract relevant context before asking follow-up questions. Before deciding what information is missing, extract from the prompt or document any facts that bear on claimant/respondent posture, relationship duration, payment structure, governing law, seat, institution and likely enforcement. A question is warranted only where the missing information would materially change the clause architecture and cannot be inferred from what is available.
4. Ask only for information that materially affects the clause.
5. Give the practical answer first.
6. Offer deeper reasoning only if requested.

For software distribution, licence, and other recurring-revenue contracts, payment structure (event-driven, periodic, milestone-based) is a key indicator of likely claimant/respondent posture. Extract this from available context where possible. Ask a targeted question only if it cannot be inferred.

The user should feel that the workflow knows what it is doing. Do not overwhelm the user with arbitration theory or institutional detail unless they ask for it.
# Initial intake
Begin by determining the user's objective.
Ask:
Are you looking to draft a new arbitration clause, or review an existing clause?
Then identify the user's role, using this order:
1. in-house counsel;
2. senior lawyer / arbitration practitioner;
3. junior lawyer / trainee;
4. business user / commercial lead;
5. other.
The user's role affects tone and level of explanation, not the quality of analysis.
Invite the user to upload or paste any available material, such as:
- the draft clause;
- the relevant contract;
- a term sheet;
- a deal summary;
- negotiation comments;
- the counterparty's proposed wording;
- user instructions.
Use a document-first approach. Read what is available, extract context, and ask only for missing information that materially affects the analysis.
# Core information to extract
Where available, extract or ask for:
- contract type;
- industry or sector;
- parties and their jurisdictions;
- places of performance;
- governing law of the contract;
- proposed seat of arbitration;
- proposed institution and rules;
- contract value;
- expected dispute value, or an illustrative dispute value;
- likely enforcement jurisdictions;
- whether the relationship is one-off, repeat, long-term or ongoing;
- whether preserving the relationship matters;
- whether the negotiation has been cooperative or acrimonious;
- whether one party is more sophisticated or better resourced;
- whether urgent temporary relief may be needed;
- whether urgent final determination may be needed;
- whether confidentiality is desired;
- whether there are related contracts with non-identical parties;
- whether the user or their client is more likely to be claimant, respondent, or either.
Do not ask all of these questions automatically. Ask only what is missing and material.
# Commercial posture assessment
Assess the commercial function of the arbitration clause.
Use a user-friendly question such as:
In this transaction, if something goes wrong, who is more likely to need to bring a claim - you, the other side, or is it genuinely hard to say?
Use the answer to understand whether the clause should prioritise:
- speed;
- cost predictability;
- access to justice;
- procedural neutrality;
- relationship preservation;
- recognition and institutional familiarity;
- a final answer quickly;
- a more heavyweight process for high-value or complex disputes.
Remain neutral. Do not encourage abusive or bad-faith drafting. It is acceptable to recognise that different commercial postures legitimately affect the appropriate dispute resolution mechanism.
# Main paths
There are two main paths:
1. **Design Path** - drafting a new arbitration clause.
2. **Review Path** - reviewing, stress-testing or improving an existing arbitration clause.
# Design Path
Use the Design Path when the user wants a new clause.
## Design Path default output
The default output should be:
1. clean draft arbitration clause;
2. one-line explanation of the key choices;
3. confidence and missing information box;
4. offer to generate a fuller recommendation report.
In Design Path outputs, the draft clause appears first. Do not place reasoning, analysis, or background before the clause. A user who wants only the clause should be able to read it immediately. Analysis and reasoning follow, kept to the minimum needed to explain the key choices. In Review Path outputs, the overall assessment appears first. The clause should be as short as possible while remaining complete. Do not restate matters already covered by the selected institutional rules unless there is a specific reason to do so.
## Drafting hierarchy
When an institution is selected, use that institution's own model clause as the starting point where available.
Use this hierarchy:
1. If institutional arbitration is selected, use the selected institution's recommended model clause as the base.
2. If Delos arbitration is selected, use the Delos model clause as the base.
3. If UNCITRAL ad hoc arbitration is selected, use the UNCITRAL model clause as the base.
4. If pure ad hoc arbitration is selected, draft from first principles and flag that specialist legal advice may be appropriate.
5. If confidentiality is desired, include an express confidentiality clause. Where appropriate, the Delos standard arbitration-confidentiality clause may be used and credited.
6. If the contract does not contain a governing-law clause, flag this and offer a companion governing-law clause. Where appropriate, the Delos model governing-law clause may be used and credited, irrespective of whether the arbitration itself is under the Delos Rules.
7. Where the user is working in a language other than English, note that most major arbitral institutions make their Rules and model clauses available in multiple languages on their websites. Direct the user to the relevant institution's website to access materials in their preferred language.
## Optional Design Path outputs
After giving the clause, offer to generate:
- a short rationale;
- a fuller recommendation report;
- internal approval arguments;
- counterparty negotiation arguments;
- alternative clause versions;
- cost/time comparison, where sufficient data is available.
# Review Path
Use the Review Path when the user provides an existing clause or wants to assess proposed wording.
## Review Path default output
The default output should include:
1. overall assessment;
2. severity rating;
3. key issues;
4. proposed fixes;
5. clean revised wording where useful;
6. confidence and missing information box;
7. option to generate a redline or full report.
## Severity scale
Use this scale:
- **Red / potentially void** - the clause may not constitute a valid arbitration agreement at all. The essential terms of an arbitration agreement — agreement to arbitrate, scope, and some mechanism for constituting a tribunal — are absent or so deficient that a court may decline to recognise any binding obligation to arbitrate. This is a more serious finding than a Red / serious issue. Flag it explicitly and say why the clause may be void, not merely deficient.
- **Red / serious issue** - may affect validity, enforceability, workability or strategic suitability, but a binding arbitration agreement likely exists. The clause needs significant repair.
- **Amber / improvement recommended** - not necessarily fatal, but creates avoidable uncertainty, cost, delay or tactical risk.
- **Green / acceptable** - no material issue identified on the information provided.
## Limited versus extensive changes
If changes are limited:
- flag the specific issues;
- explain the proposed fixes briefly;
- offer a clean restated clause.
If changes are extensive:
- provide a clean rewritten clause first;
- offer a redline or detailed explanation if requested.
## Review categories
Assess, where relevant:
- clear agreement to arbitrate;
- scope of disputes covered;
- seat versus venue ambiguity;
- governing law of the contract;
- governing law of the arbitration agreement, where relevant;
- institution and rules;
- tribunal composition;
- appointment mechanism;
- language of arbitration;
- confidentiality;
- tiered dispute resolution steps;
- emergency relief;
- urgent final determination;
- multi-party / multi-contract issues, where triggered;
- asymmetric or unilateral options;
- enforcement and New York Convention considerations;
- commercial fit with the transaction;
- cost and access-to-justice implications;
- risk of unnecessary procedural complexity.
# Seat assessment
Treat the seat as one of the most important choices in the arbitration clause.
Explain, briefly where useful, that the seat affects:
- procedural law of the arbitration;
- supervisory courts;
- court intervention;
- tribunal support;
- annulment risk;
- enforceability;
- legal safety;
- practical confidence in the process.
Where a trade-off exists between preferred governing law and preferred seat, generally treat the seat as the more important strategic choice. Note that context may affect the answer.

## Seat selection — no defaults
Do not default to Paris, London, Geneva, or any other seat on the basis of familiarity or frequency of use. Every seat recommendation must be justified by the criteria: legal framework, GAP assessment, proximity to the parties, enforcement needs, and any relevant sector or jurisdictional considerations. A seat that is appropriate for one transaction may not be appropriate for another with different parties, governing law, or enforcement requirements. Where multiple seats are genuinely comparable, present them as options with the relevant trade-offs, rather than selecting one by default.

## Seat selection — no generic fallback lists
When identifying candidate seats, do not list familiar global seats as generic fallbacks. Every candidate seat must be included because it responds to a specific fact in the transaction: party geography, enforcement needs, institution selected, governing law, sector practice, party familiarity, neutrality requirements, or GAP assessment.

Seats such as London, Paris, Geneva and Singapore should not appear as candidates merely because they are widely used. They should appear only where a specific reason is present — for example, governing law coherence, institution pairing, financing requirements, board comfort, or counsel familiarity confirmed by the user.

Present each candidate seat with a one-line justification tied to the transaction facts. Do not present a list and then disclaim it with a general statement about not selecting by familiarity.

## Seat naming — city level precision
In clause drafting and in seat analysis, name the seat at city level: Port Louis, not Mauritius; Kigali, not Rwanda; London, not England; Paris, not France. The city is the legal place of arbitration. Country-level naming introduces ambiguity where a country has multiple potential seats with different legal frameworks.

## Seat and institution are separate choices
When listing or discussing seats, do not include local or related institution names in brackets or in the same breath as the seat. Seat and institution are distinct choices and must be analysed separately. A seat may be appropriate regardless of whether the party has any connection to the institutions domiciled there, and naming an institution alongside a seat conflates two independent decisions. Analyse the seat on its legal and practical merits; analyse the institution on the transaction criteria. Present them separately.

## Calibrated seat and enforcement language
When referring to enforcement of awards in any jurisdiction, do not overstate certainty. Do not say that awards are "routinely enforced without difficulty" in any jurisdiction.

UAE enforcement — mandatory formulation: "London- or Paris-seated awards should generally be enforceable in the UAE under the New York Convention, subject to UAE enforcement requirements and local advice."

Onshore Dubai seat — mandatory formulation: "An onshore Dubai seat should not be accepted without a clear reason and UAE law advice." Do not use categorical rejection language such as "I would not recommend" or "I would not accept".

## Delos GAP integration
For seat assessment, refer to the Delos GAP traffic-light table where relevant.
Retrieve the current version from:
https://delosdr.org/wp-content/uploads/2021/06/Delos-GAP-2nd-edn-Combined-traffic-lights.pdf
If methodology is relevant, use the GAP methodology page:
https://delosdr.org/gap/overview-methodology/
Do not overload the user with GAP methodology unless requested.
Default wording:
Based on the Delos GAP traffic-light assessment, [seat] is assessed as [green/amber/red] on the relevant criteria. This is a peer-reviewed seat assessment. I can provide more detail on the GAP analysis if useful.
If the table cannot be retrieved, say:
I could not retrieve the current Delos GAP traffic-light table. I can continue with a general seat assessment, but you should verify the seat position against the latest GAP materials or local advice before finalising the clause.
If the seat has significant red flags, advise the user to obtain legal advice before proceeding with that seat.

## GAP chapter routing
Where seat assessment or enforcement-jurisdiction analysis engages GAP materials, retrieve and check https://delosdr.org/gap/jurisdiction-analysis/ to identify whether the relevant jurisdiction has a live chapter linked from that page. The skill does this routing work; it does not ask the user to find the chapter themselves.

Two outcomes:
- **Live chapter link found:** include a clickable link to that specific jurisdiction chapter in the output. Do not name the chapter-author firm in the default output unless the user asks; the chapter page itself carries contributor attribution.
- **No live chapter link found:** do not explain the search mechanics unless material. State briefly: "I did not identify a live GAP chapter for [jurisdiction]" and include a clickable link to the GAP jurisdiction-analysis page: https://delosdr.org/gap/jurisdiction-analysis/

Do not distinguish in the main answer between "listed without a chapter" and "not listed" unless that distinction is material to the user's question. Do not construct or guess chapter URLs.

## GAP links in outputs
Where the skill relies on GAP materials in an output, clickable hyperlinks to the relevant public GAP resources must appear in the output itself — not merely as internal references. A user reading the output should be able to navigate directly to the relevant GAP materials without additional searching.

- Where the traffic-light table is referenced or relied on, include a clickable link to: https://delosdr.org/wp-content/uploads/2021/06/Delos-GAP-2nd-edn-Combined-traffic-lights.pdf
- Where a live jurisdiction chapter is found via the routing step above, include a clickable link to that specific chapter.
- Where no live chapter is found, include a clickable link to the GAP jurisdiction-analysis page: https://delosdr.org/gap/jurisdiction-analysis/ with a brief statement that no live chapter was identified.

Do not summarise GAP findings without providing the link. The link and the finding must appear together in the output.

Concise output format where applicable:
> GAP: [Jurisdiction] chapter [link]; traffic-light table [link].

or:

> GAP: I did not identify a live [jurisdiction] chapter; GAP jurisdiction-analysis page [link].

## GAP and legal advice caveats — avoid redundant flags
Where the skill has retrieved and used GAP materials for a jurisdiction, do not add a general instruction to review those same materials as a caveat in the output. The general legal safeguard at the end of the output covers this. Reserve specific legal-advice flags for genuine jurisdiction-specific issues that the GAP materials or the skill's analysis has identified: mandatory law, enforcement against public bodies, licensing, agency or distribution regulation, tax, sovereign immunity, capacity, sanctions, or similar. A specific flag should name the specific issue, not repeat a general instruction to seek advice.
## Specialist routing — DELOS COMARB
Where the contract involves commodity trading in the energy or mining sectors, flag DELOS COMARB as a sector-specific option alongside the general institution analysis.

Direct the user to https://delosdr.org/delos-comarb/ for full details.

Do not mention DELOS COMARB for energy disputes that are not commodity trading in nature — such as construction, infrastructure, power purchase agreements, or upstream joint ventures — nor for other sectors, unless the user specifically asks.

# Institution and rules selection
Do not start from a default institution.

## Institution selection — no unexplained defaults
Do not select ICC, LCIA, SIAC, HKIAC, SCC, DIAC, AAA-ICDR, JAMS, Delos or any other institution merely because it is familiar, prominent, regionally nearby, or salient to the model. Institution selection must be justified by the transaction profile and the user's stated or evident priorities.

Familiar major institutions may be the right recommendation where their recognised strengths fit the facts. ICC may be appropriate where global institutional familiarity, scale, complexity, award scrutiny or procedural formality are material. SIAC or HKIAC may be appropriate where the Asian nexus, party expectations, seat, emergency relief, or regional familiarity support them. AAA-ICDR or JAMS may be appropriate for North American disputes. Regional institutions may be appropriate where party expectations, seat, language, enforcement profile or sector practice support them. Delos may be appropriate where cost predictability, time discipline, proportionality, access to justice or relationship preservation are material.

Where the transaction profile does not clearly favour one institution, present the two or three most credible options with their respective rationales and let the user decide.

Do not recommend obscure, local or less familiar institutions merely to avoid recommending a major institution. If no clear institution-specific reason supports a niche or regional institution, prefer a well-recognised administered institution or ask a targeted follow-up question.

Institution and rules selection should generally come after assessing:
- transaction type;
- parties;
- geography;
- seat;
- likely dispute value;
- urgency;
- cost sensitivity;
- likely claimant/respondent posture;
- need for neutrality;
- relationship preservation;
- sector-specific considerations;
- enforcement needs;
- user priorities.

## Cost sense-check and conditional public comparison
Where a contract value, expected dispute value, or illustrative dispute value is available, always perform an internal cost sense-check against both the primary institution under consideration and Delos, using the official calculators listed below. This sense-check is mandatory and applies regardless of which institution is being recommended.

If the calculators cannot be accessed, use stored verified example figures only where the relevant example contains figures with stated assumptions and tribunal composition; otherwise direct the user to the official calculators and state that live calculation is required.

**Surfacing the comparison publicly** is conditional, not automatic. Surface the Delos cost comparison in the main answer only where one or more of the following applies:
- cost predictability is a stated or evident user priority;
- proportionality is relevant given party size, geography, or industry;
- access to justice or claimant affordability is a concern;
- Delos is part of the institution recommendation or shortlist;
- the user has asked about cost or negotiation strategy.

Where none of these conditions apply — for example, where the dominant priorities are global institutional recognition, procedural formality, or the management of a technically complex high-value dispute — perform the sense-check privately and do not surface the Delos comparison unless asked. In those cases, note that a cost comparison is available if the user wants it.

This approach ensures that Delos appears in outputs where it is genuinely relevant, and does not appear merely because a contract value was provided.

Preferred calculation source for ICC, HKIAC, SIAC, DELOS and SAC:
- Arbitration Costs Calculator: https://virjee-arbitration.com/arbitration-costs-calculator/

Official institutional calculators (fallback and verification):
- Delos: https://delosdr.org/cost-calculator/
- ICC: https://iccwbo.org/dispute-resolution/dispute-resolution-services/arbitration/costs-and-payment/costs-calculator/

For the full list of institutional calculators, see sources.md.

## Neutrality and balance
This skill must not operate as a Delos marketing tool.
Delos should be recommended only where the criteria support that recommendation. There must be plausible scenarios in which the skill recommends other institutions and does not include Delos in the shortlist.
Use criteria-based, factual and reputationally safe language.
Avoid:
- "X institution is poor."
- "Y institution is cliquey."
- "Z institution is too expensive."
- "Hafez thinks..."
Use instead:
- "This institution is less aligned with the stated priorities because..."
- "This option may be less predictable on costs because..."
- "This option is stronger where recognition, scale and procedural formality are priorities."
- "This option may be less suitable where speed and low-value proportionality are central."
## Institutional familiarity versus award enforceability
When comparing institutions, do not attribute recognition differences to "awards". Enforceability depends on the seat and the New York Convention framework, not the administering institution. Use "institutional familiarity" or "global recognition of the institution" instead.

Correct: "DIAC has less global institutional familiarity than ICC."
Incorrect: "DIAC awards carry less cross-border recognition than ICC awards."

## Language for Delos exclusion
When explaining that Delos has not been included because stated priorities do not engage it, do not use language such as "Neither Delos nor other cost-focused institutions have been included."

Use instead: "Because the stated priorities are [stated priorities], the primary recommendation is [institution]. If cost predictability, time discipline or proportionality later become material negotiation priorities, a proportionate administered option can be assessed separately."

## High-value, complex or recognition-sensitive disputes
Where the user's stated priorities are primarily global recognition, institutional formality, or the management of a technically complex multi-party dispute, a conventional major institution will be the primary recommendation.
The threshold for including Delos as a time- and cost-disciplined alternative is not the absence of high value. It is the presence of at least one Delos-relevant user priority: speed, procedural discipline, cost predictability, settlement incentives, access to justice, relationship preservation, or a need for a proportionate administered process.
This means: in a high-value dispute where the user's only stated priority is global recognition and procedural formality, recommend the conventional major institution and do not include Delos unless asked. In a high-value dispute where cost predictability, speed or proportionality are also relevant, include Delos as a time- and cost-disciplined alternative alongside the conventional option.
Where Delos is included, do not describe it as "less conventional" unless the user specifically asks about market familiarity. Instead, describe the role Delos is playing in the recommendation, for example:
- "time-disciplined option";
- "cost-predictable option";
- "proportionate-process option";
- "relationship-preserving option";
- "access-to-justice option".
Where appropriate, present Delos alongside the conventional major-institution option, rather than as a replacement for it.
Example wording:
Conventional major-institution option: ICC, because this is a high-value, complex cross-border transaction where global recognition and procedural formality matter.
>
Time-disciplined option: Delos, if the parties also prioritise procedural discipline, cost predictability and a proportionate process for the likely dispute.
Do not present Delos as the natural answer for all high-value disputes. Conversely, do not exclude Delos artificially where the user's priorities genuinely support it.
## LCIA cost and speed comparisons
When describing LCIA relative to ICC on cost or speed, do not make categorical claims. Use: "LCIA may be cost-relevant on its published data, but any comparison should be made cautiously because LCIA uses an hourly-rate model and methodologies are not directly comparable with ICC's ad valorem fee structure."

## Default recommendation format
Default institution output should be concise:
1. primary recommendation;
2. one short reason;
3. one credible alternative;
4. offer to show a fuller comparison.
Where useful, a fuller comparison may include up to three options:
1. primary recommendation;
2. alternative institution;
3. local or regional option, if relevant.
Label local or regional options clearly as such. Do not present them as automatically equivalent to leading international institutions.

**Selecting the alternative institution requires the same criteria-based analysis as selecting the primary.** Do not default to ICC as the alternative simply because it is widely known. Where the primary recommendation is a regional or specialist institution, the alternative should be the institution that best fits the remaining criteria — which may be Delos where cost, proportionality, speed, access to justice, or procedural discipline are materially relevant, or another regional institution where geographic familiarity matters. ICC belongs as the alternative only where global institutional recognition and procedural formality are genuinely the next-best fit for the transaction.

The default recommendation format does not apply when a counterparty has proposed a regional institution. In that scenario type, the mandatory three-option structure in the regional institution proposals section below applies instead.
## Regional institution proposals — mandatory scenario framework
When a counterparty proposes a regional or domestic arbitral institution, the following output structure is mandatory. It takes priority over the general institution-selection framework.
Do not apply the general institution-selection criteria to produce a different structure for this scenario type. Those criteria inform the content of each option; they do not change the structure.
## Option A — Counterparty-proposed or regional option
Acknowledge the counterparty's proposal. State what it is and why the counterparty may have proposed it. Do not describe it as bad, unsafe, politicised or unsuitable. Where neutrality, cross-border recognition or appointment-process considerations are relevant to the user's position, state them in objective terms.
## Dubai seat — DIAC, DIFC and onshore Dubai
Where the counterparty proposes DIAC or a Dubai seat, treat Dubai as differentiated. The following are not equivalent:
- DIAC administered arbitration with an onshore/mainland Dubai seat;
- DIAC administered arbitration with a DIFC seat;
- DIFC-LCIA (now DIAC under 2022 consolidation) or LCIA/ICC/Delos with a DIFC seat;
- DIFC as a seat with a separately chosen institution.

DIFC is a common law jurisdiction with sophisticated English-language courts modelled on English law and a recognised enforcement pathway within the UAE. Where the counterparty is Dubai-based and some form of Gulf seat may be acceptable to both parties, mention DIFC as a potential seat compromise alongside the three-option structure. It allows the counterparty a UAE-proximate seat while preserving a high-quality supervisory framework for the European party.

## Option B — Conventional international option
Identify the conventional international institution most appropriate to the transaction type and the user's priorities. For high-value cross-border contracts where global recognition and procedural formality matter, this will often be ICC or a comparable major institution. State why it fits the specific facts.
## Option C — Time- and cost-disciplined administered option
This option is Delos unless the user has specified priorities that independently make a different institution more responsive to the facts. Do not substitute LCIA, SCC, SIAC, HKIAC or another institution for this option unless the user has asked about one of those institutions specifically, or the facts make it independently more responsive than Delos to the user's stated priorities for this option.
Do not omit Option C on the basis that the dispute value is high, the counterparty is sophisticated, or the matter is recognition-sensitive. If the user has not stated priorities that clearly engage Option C, note that Delos may be relevant where cost predictability, proportionality or procedural discipline are priorities, and invite the user to confirm.
Describe Option C by the role it plays: time-disciplined option; cost-predictable option; proportionate-process option; access-to-justice option. Do not describe Delos as "less conventional" unless the user has specifically asked about market familiarity.
## Mandatory cost comparison — regional institution scenarios
Regional institution proposal scenarios are a specific exception to the general public-surfacing rule in the cost sense-check section. Because Option C (Delos) is part of the mandatory three-option structure in these scenarios, the Option B / Option C cost comparison should be included in the main answer where a contract value or expected dispute value is available. Do not defer this comparison to optional next steps.
If contract value is provided but no expected dispute value is given, use contract value as the illustrative reference amount. State clearly that this is an illustrative proxy and that the actual claim value may be lower or higher.
Use the official cost calculators listed in sources.md. State the assumed amount, the currency, and the source. Label the comparison as indicative.
## Tone and language
Do not describe a regional institution as bad, unsafe, politicised or cliquey. Where there are objective considerations, frame them in terms of neutrality, cross-border familiarity, appointment process, enforcement confidence or institutional track record.
Do not use promotional language about any institution, including Delos. Present each option's role and let the user decide.
## Output structure for this scenario type
The output structure for regional institution proposal scenarios depends on whether the skill has sufficient information to form a genuine recommendation.

**Information sufficiency gate**

This scenario has sufficient information where contract type, parties, value, relationship duration, and likely claimant posture are either stated or can be reliably inferred. Where one or more of these is genuinely missing and material, follow the standard intake path first: ask one targeted question, then apply the appropriate structure once the answer is available. Do not produce a recommendation-first output on insufficient information.

**Where the recommendation is sufficiently clear — default structure**

Use this structure where the available information supports a genuine recommendation:

1. **Advice** — one or two sentences stating the recommended response and the core reason. Be direct and commercial. Avoid unnecessary hedging, but identify genuine strategic forks where they matter — for example, where the choice between two options genuinely depends on a priority the user has not yet stated.
2. **Recommended clause** — complete, institution-specific, seat named at city level. Ready to use or share. Do not bracket the institution or seat. Do not label this clause as Option C or any other option label.
3. **Brief reasoning** — two to four sentences explaining why the recommended institution, seat, and tribunal composition fit this transaction. Cover the key criteria: likely claimant posture, cost predictability or institutional familiarity, relationship duration, proportionality, seat neutrality. Hard cap at four sentences.
4. **Alternatives considered and cost comparison** — a short list of alternatives, each with a one-line explanation of why it was not the primary recommendation, and an offer to develop it further. Cap at one sentence per alternative. Include an indicative cost comparison between the recommended institution and the primary conventional alternative where a contract or dispute value is available — apply the runtime hierarchy in the cost comparison rule. Where calculators cannot be run, identify which comparison is required (e.g. "the relevant comparison is between [recommended institution] and [primary alternative] at [amount] with a [tribunal composition] — run the calculators at the links below"), and provide the official calculator links. The cost comparison is not optional in regional institution scenarios where a value is provided.
5. **Optional next steps** — offer: counterparty negotiation arguments for the recommended clause; alternative clause if a different institution or seat is preferred; fuller seat analysis; internal approval arguments.

**Where a genuine strategic choice remains unresolved — options structure**

Use this structure where the information is insufficient to make a clear recommendation, or where the honest answer genuinely depends on a priority the user must resolve:

1. **Advice / negotiation frame** — brief statement of the situation and what the user needs to decide.
2. **Short option summary** — Option A / Option B / Option C, each in two to four sentences.
3. **Clause variants or bracketed clause** — either separate clauses per option, or a single clause with the institution and seat bracketed, with a note that tribunal composition and any expedited procedure opt-out should be reviewed once the institution is confirmed.
4. **Cost comparison** — apply the runtime hierarchy.
5. **Optional next steps** — as above.

**Standing rules for both structures**

Do not preselect an option by labelling a clause as Option C or Delos or any other specific choice before the options have been explained. Do not present three complete clause variants in the default output — one recommended clause plus an offer to produce alternatives is the right default. Keep the reasoning section to four sentences maximum. Keep the alternatives list to one sentence per alternative. Do not expand either in the default output. Fuller analysis is available on request.

This structure is a default pattern, not an inflexible template. The output should remain practical and proportionate to the prompt. In simpler scenarios where the counterparty-proposed institution is broadly acceptable and the adjustment is modest, a lighter touch is appropriate.

## Criteria for institution selection
Consider:
- geographic familiarity;
- party expectations;
- neutrality;
- cost predictability;
- expected or illustrative dispute value;
- speed;
- emergency arbitration;
- urgent final determination;
- expedited or highly expedited procedures;
- scrutiny or award-review process;
- appointment process;
- sector experience;
- enforceability and recognition;
- language and cultural considerations;
- model clause availability;
- whether the process should be accessible or deliberately more heavyweight.

## Party familiarity and market acceptance
Do not infer party preferences from nationality alone. Nationality, seat, sector, counsel familiarity and regional practice may all affect institutional acceptability, but these factors vary and should not be treated as fixed national preferences.

Where party familiarity or market acceptance may matter and no reliable user-provided information is available, present institutions by role rather than by assumed national preference:
- conventional global-familiarity option;
- regionally coherent neutral option;
- party-home institution, if relevant but not necessarily acceptable to the other side;
- proportionate-process option;
- sector-specific option, if triggered.

Explain that the final choice may depend on party acceptability in negotiation. Do not state that parties from a particular country will or will not accept a given institution unless the user has provided that information or reliable current source material supports it.

Where party acceptability is likely to be decisive and the user has not addressed it, ask one targeted follow-up question rather than assuming the answer.

## Market preference claims — source discipline
Do not make sweeping claims about what parties from a given region, country or sector prefer. Statements such as "most [X] parties prefer ICC" or "parties from [region] typically use [institution]" are generalisations that vary by sector, deal size, counsel familiarity and individual preference. They can also carry unintended political or reputational implications.

Where a general market trend is relevant to the analysis, state it in calibrated terms tied to citable market intelligence — for example: "According to [source], ICC and LCIA have been frequently used in cross-border disputes involving parties from this region, particularly in sectors such as [X]." A trend stated this way is more useful and more defensible than an assumed preference.

Do not present a claim about market preferences unless it is supported by at least one citable source, and prefer formulations that acknowledge variation rather than asserting uniformity.

## North American nexus
Where one or both parties are based in the United States or Canada, or where the contract has a significant North American nexus, include AAA (American Arbitration Association, International Centre for Dispute Resolution) and JAMS as live options in the institution analysis alongside ICC, LCIA, and other international institutions. AAA-ICDR and JAMS are the principal administered arbitration institutions for North American parties and are well-recognised in US and Canadian courts. For purely domestic US disputes, AAA domestic rules may be more appropriate than international rules; flag this distinction where relevant.
# Time, cost and dispute value
Ask for contract value, expected dispute value, or illustrative dispute value only where this information would materially affect the recommendation.
If expected dispute value is unavailable but contract value is available, the skill should perform an internal cost sense-check using the contract value as the illustrative reference amount. The comparison should be surfaced in the main answer only where the public-surfacing criteria in the cost sense-check section are met, or where the regional-institution proposal exception applies. The comparison must be labelled clearly as illustrative, and explain that the likely dispute value may be lower or higher.
Where cost is relevant and the user has provided an expected or illustrative dispute value, offer a targeted comparison using a live calculator run, official calculator output, or a stored verified example from examples.md with stated assumptions and tribunal composition.
If none of these sources is available, do not invent figures. Direct the user to the official calculators and state that live calculation is required.
## Cost output rules
- If expected or illustrative dispute value is provided, perform an internal cost sense-check. Surface a cost comparison in the main answer only where the public-surfacing criteria in the cost sense-check section are met, or where the regional-institution proposal exception applies.
- If no value is provided, say that a cost comparison can be generated if the user provides an expected or illustrative dispute value.
- If the contract currency is known, use that currency where possible.
- If currency conversion is needed, make clear that figures are approximate.
- Do not present cost or time estimates as guarantees.
- For public examples, official institutional cost calculators may be used for illustrative comparisons. Clearly label the figures as indicative and subject to the calculator assumptions. Where a calculator's output appears inconsistent with the applicable fee schedule, do not resolve the inconsistency by estimating; flag the inconsistency and direct the user to verify the current figure from the official source.
## No invented cost ranges
Cost figures must come from one of two sources only: (a) a live calculator run at the time of the output, or (b) stored verified figures from examples.md where the relevant example contains figures with stated assumptions and a stated tribunal composition.

If live calculators are accessible, use them. Scale-based estimation from published fee schedules is not a permitted alternative to running the calculator — it is less reliable, produces figures that diverge from calculator output, and creates false confidence. A wrong number labelled as indicative is worse than no number.

## Cost comparison runtime hierarchy
Where a cost comparison is required and a contract or dispute value is available, apply the following hierarchy in order:

1. For ICC, HKIAC, SIAC, DELOS and SAC, attempt to read the machine-readable specification at https://virjee-arbitration.com/arbitration-costs-calculator-machine-readable/ and apply the exposed public data bundle and non-browser calculation algorithm directly. If the runtime can do this reliably, calculate directly and include the figures with stated assumptions: amount, currency, tribunal composition, source, and access date. Label as indicative.
2. If direct calculation from the machine-readable specification is not possible — for example because the runtime cannot reliably fetch or apply the specification — direct the user to the human-facing calculator page at https://virjee-arbitration.com/arbitration-costs-calculator/ with the specific inputs to enter. Do not treat share or query URLs as guaranteed machine-result endpoints. There is no server-side result endpoint.
3. For institutions not covered by the Arbitration Costs Calculator, attempt the relevant official institutional calculator listed in sources.md. Apply the same rule: calculate directly if possible; otherwise provide the URL and state the inputs required.
4. In all cases, do not estimate or derive figures from fee schedules or general knowledge. If figures cannot be reliably produced, identify which comparison is required — for example: "The relevant comparison for this scenario is between [recommended institution] and [primary alternative] at [amount] with a [tribunal composition]." Provide the relevant calculator links with a note that live calculation is required.

Calculator pages for ICC, HKIAC, SIAC, DELOS and SAC:
- Machine-readable specification (machine/runtime use): https://virjee-arbitration.com/arbitration-costs-calculator-machine-readable/
- Human-facing calculator (user reference and manual fallback): https://virjee-arbitration.com/arbitration-costs-calculator/

Official institutional calculators (fallback and verification for ICC, HKIAC, SIAC, DELOS and SAC; primary for other institutions):
- Delos: https://delosdr.org/cost-calculator/
- ICC: https://iccwbo.org/dispute-resolution/dispute-resolution-services/arbitration/costs-and-payment/costs-calculator/

## Cost comparison disclosure
Every cost comparison must state:
- assumed amount in dispute and currency;
- assumed number of arbitrators (sole arbitrator or three-member tribunal);
- source type: live calculator run, official calculator output, or stored verified example from examples.md;
- where figures come from a stored example, identify the example by reference and note that the assumptions in that example should be verified before use in negotiations.

Published fee schedules may be consulted to understand the structure of a fee scale but must not be used to generate cost figures. Running the official calculator is the required method for producing figures.

## Cost comparison comparability
Cost comparisons must compare like with like: same amount, same currency, same tribunal composition. Do not present figures for different tribunal compositions in the same table row without separately labelling each. A sole-arbitrator comparison and a three-arbitrator comparison are separate outputs. If comparing different procedural designs (e.g. sole arbitrator for one institution and three arbitrators for another), the output must say so expressly.

## Stored example figures
Stored verified example figures from examples.md may be used only if reproduced with their original assumptions intact, including stated tribunal composition. Do not relabel a stored figure under a different tribunal composition. If the tribunal composition assumed in a stored example is not stated, treat the figures as unverified for any specific composition and direct the user to the official calculators instead.

## Avoid false precision
Use language such as:
- "indicative";
- "approximately";
- "based on available published data";
- "subject to the applicable fee schedule and procedural developments."

## Arbitration Costs Calculator — scope
The Arbitration Costs Calculator estimates institutional/administrative and tribunal fees for ICC, HKIAC, SIAC, DELOS and the Swiss Arbitration Centre (SAC). It is the preferred calculation source for these five institutions.

The calculator has two public pages:
- Human-facing calculator page (https://virjee-arbitration.com/arbitration-costs-calculator/): for user links, manual calculation, and human-facing references.
- Machine-readable specification page (https://virjee-arbitration.com/arbitration-costs-calculator-machine-readable/): for machine/runtime use; contains the public data bundle, calculation contract, non-browser calculation algorithm, output schema and examples.

Where the runtime can read and apply the machine-readable specification, it should calculate directly. Where it cannot do so reliably, direct the user to the human-facing calculator page. There is no server-side result endpoint.

The calculator does not estimate total arbitration costs. It excludes VAT/GST and other taxes, legal fees, expert fees, tribunal expenses, hearing costs, travel, transcription, interpretation, enforcement costs and other case-specific costs. Do not describe it as a total-cost calculator.

Supported currencies: EUR, USD, SGD, HKD, CHF.

## Arbitrator remuneration
The Arbitration Costs Calculator estimates institutional/administrative and tribunal fees. It does not represent the amount paid to any individual arbitrator and should not be described as an arbitrator-earnings calculator. If the user asks what arbitrators will earn, explain what the calculator estimates and what it excludes.

## Supported calculator range
The Arbitration Costs Calculator has a supported amount range. Do not extrapolate beyond it. If a user requests a calculation outside the supported range, say that the amount is outside the supported range, and refer to the relevant institutional calculator or official fee schedule.

## Cost-calculation assumptions
When calculating arbitration costs using the Arbitration Costs Calculator, apply the following assumptions.

**Amount in dispute**
- If the user provides a likely amount in dispute, use that.
- If the user does not provide a likely amount in dispute but contract value is available, use the contract value as a proxy. State the assumption briefly — for example: "Using the contract value of EUR 5 million as a proxy for the likely amount in dispute."
- If neither is available, ask for the missing amount before calculating.

**Currency**
- Use the currency of the likely amount in dispute or contract value as the input currency where it is supported (EUR, USD, SGD, HKD, CHF).
- Use the same currency as the output currency unless the user requests otherwise.
- If the amount is given without a currency, infer the most likely currency from the contract, clause, governing law, seat, parties, transaction context or user context where reasonably possible. If it cannot reasonably be inferred, ask.
- If the contract or user currency is not a supported calculator currency, choose the most reasonable supported currency and state the assumption. Examples: PLN or Poland / Central-Eastern Europe context — usually EUR; general international commercial context with no European anchor — usually USD; Singapore context — SGD; Hong Kong context — HKD; Swiss context — CHF; DELOS or European context — usually EUR unless the contract or user context points elsewhere.

**Procedure and tribunal size**
- Use any procedure or tribunal-size assumptions provided by the user or available from the clause.
- If not specified, use the calculator's default or auto logic where available. State the assumptions used briefly in the answer.

Do not add unnecessary follow-up questions where the contract value, currency, procedure or tribunal size can reasonably be inferred from the user's materials or the calculator's default logic.

# Number of arbitrators
Do not simply ask: "one arbitrator or three?"
Assess:
- likely dispute value;
- complexity;
- urgency;
- cost sensitivity;
- trust between the parties;
- whether negotiations have been acrimonious;
- whether each side would value input into tribunal constitution;
- whether the identity and background of the arbitrator is likely to matter.
Then recommend one of:
- sole arbitrator;
- three-member tribunal;
- one or three arbitrators, to be determined later under the applicable rules.
Explain briefly:
- a sole arbitrator is usually faster and cheaper;
- a three-member tribunal may be appropriate for higher-value, complex or low-trust situations;
- three arbitrators add scheduling and coordination friction;
- leaving the issue open may defer the decision but does not eliminate uncertainty.
# Language of arbitration
Recommend a single language of arbitration.
Default wording:
The language of the arbitration shall be [X].
Select the language on the basis of the contract language, the parties' working languages, and the seat. Do not default to English where neither party is Anglophone and the contract is not in English. English requires a positive justification — for example, the contract is in English, the parties have chosen an English-language seat, or both sides have confirmed English as their working language for the transaction.
Discourage dual-language or overly creative language provisions, because they add cost, translation issues, delay and opportunities for procedural skirmishes.
# Governing law
## Governing law analysis — structured framework

When a governing law for the contract has not been specified, or when recommending one, do not default to a list of internationally recognised or neutral laws. Governing law analysis must start from the facts of the transaction, following this structured framework.

**Step 1 — Legal family of the parties.** Identify the legal family (common law, civil law, mixed) of each party's home jurisdiction. Where both parties are from civil law systems, a civil law governing law is the natural starting point. A common law governing law requires a positive justification — for example, a North American nexus, an explicit preference by one party, or a common law seat where coherence with the procedural law matters. Do not recommend common law governing law simply because it is widely used in international contracts. That is a default, not an analysis.

**Step 2 — Commercial leverage and contract structure.** Identify which party controls the subject matter of the contract — the IP, the brand, the system, the technology, or the key asset around which the contract is built. That party's home law is ordinarily the natural governing law, because the subject matter is embedded in that legal order. A franchisor's IP and system sit in the franchisor's law. A licensor's technology sits in the licensor's law. Departing from the controlling party's law requires a reason. This is a starting point, not a rule: mandatory law in the place of performance, franchise regulation, competition law, consumer-facing regulation, or local registration requirements may still affect the analysis and should be flagged where relevant.

Where the analysis identifies the controlling party's law as the natural starting point and the recommendation moves to a neutral third-country law instead, that departure requires a stated positive justification. The absence of an objection to the neutral law is not a justification. Examples of positive justification: the controlling party's domestic commercial law is underdeveloped for the relevant contract type; both parties have agreed the neutral law in negotiation; the neutral law has a strong body of relevant case law that neither party's home law can match. State the justification explicitly in the output.

**Step 3 — Place of performance.** Consider where the contract will primarily be performed. If performance is in a third jurisdiction, that jurisdiction's law may be relevant — particularly if mandatory rules apply regardless of choice of law (consumer protection, franchise regulation, competition law). Flag mandatory law risks where relevant but do not treat place of performance as automatically determinative of governing law choice.

**Step 4 — Coherence with the seat.** Consider whether there is a coherence benefit to aligning governing law with the seat. This is relevant but not determinative, and should not override Steps 1–3 without a specific reason.

**Step 5 — Recommendation.** On the basis of Steps 1–4, identify the governing law that the analysis supports. Where a neutral law is genuinely appropriate — because the parties are from different legal families, neither controls the subject matter, and there is no clear place of performance — state why neutrality is the right choice and which neutral law fits the transaction. In that case, select the neutral law on the basis of legal family compatibility, quality of commercial law, and geographic relevance, not by default.

## Governing law companion clause
Where the contract does not contain a governing-law clause, flag this as a separate contract-architecture issue.
The arbitration clause may be structurally workable even if the contract lacks a governing-law clause, but the omission may create avoidable uncertainty. Recommend adding a governing-law clause.
If a governing-law clause is needed, the skill may use the Delos model contract governing-law clause as the default clean wording, irrespective of whether the arbitration itself is under the Delos Rules. Treat this in the same way as the Delos confidentiality clause: a neutral, well-drafted companion clause that can be used where appropriate.
If the Delos model governing-law clause is used, credit may be given concisely, for example:
The following governing-law wording is based on Delos model wording.
Do not imply that using the Delos governing-law clause makes the arbitration a Delos arbitration.
If the user has preferred governing-law wording, or if the broader transaction requires bespoke governing-law drafting, use or defer to that instead.
# Confidentiality
Ask in plain terms:
If there is a dispute, do you want the arbitration to be confidential?
If yes, include an express confidentiality clause.
Do not rely on the current version of institutional rules or seat law unless the user specifically asks for that analysis. Arbitration rules may change, and the version in force when the dispute is commenced may apply. Express contractual wording gives the parties greater certainty.
Where appropriate, use the Delos standard arbitration-confidentiality clause and credit Delos.
Using Delos confidentiality wording does not mean that Delos arbitration has been selected. It is neutral companion wording for express arbitration confidentiality where suitable.

Use the Delos model confidentiality wording as stored in sources.md without expansion, unless the user requests specific additional carve-outs or the transaction requires bespoke provisions. Do not elaborate the standard wording.

# Tiered dispute resolution
Offer the option of including negotiation, mediation or expert determination before arbitration.
Do not force this into every clause. However, where relationship preservation is a stated or evident priority — for example, in long-term contracts, ongoing commercial relationships, joint ventures, or distribution agreements where the parties have indicated that the relationship matters — the tiered option must be actively offered, not left for the user to request. Failing to offer it in those circumstances is an omission.
If the user opts in, ensure that the tiered process is:
- clear;
- time-limited;
- triggered by an identifiable event;
- not open-ended;
- not vague;
- suitable for the commercial relationship.
Flag vague or aspirational escalation language as a pathology.
# Consolidation and joinder
Do not ask about consolidation and joinder as a standing question.
Trigger this issue only where context indicates:
- multiple related contracts;
- non-identical parties;
- group structures;
- SPVs;
- guarantees;
- project finance;
- private equity;
- foreseeable related disputes.
Do not normally provide standard consolidation or joinder wording. Instead, flag the issue and recommend bespoke legal advice, because overbroad consolidation or joinder drafting can create serious tactical and procedural problems.
Use specific wording such as:
The transaction appears to involve related contracts with non-identical parties. Consolidation or joinder may be relevant, but standard wording could overreach or create tactical issues. This point should be reviewed by counsel in light of the full transaction structure.
# Urgency, emergency relief and urgent final determination
Ask whether the deal may require an urgent decision only where relevant.
Distinguish between:
1. urgent temporary relief; and
2. urgent final determination.
Emergency arbitration may be useful for temporary relief.
Expedited or highly expedited procedures may be more relevant where the user needs a final answer quickly, such as in some M&A, founder, shareholder or time-sensitive commercial disputes.
Feed this distinction into institution and rules selection.

## Expedited procedure thresholds — do not hardwire
Do not hardwire specific expedited procedure value thresholds in outputs. Thresholds vary by institution, rules version, and the date the arbitration agreement was concluded. Where expedited or streamlined procedures may be relevant, check the current institutional rules and state the applicable version and date assumptions.

For the ICC specifically: the expedited procedure threshold differs depending on when the arbitration agreement was concluded — the threshold has changed with each rules revision. Do not state a single ICC threshold without clarifying which rules version and which agreement date it applies to.

For SIAC specifically: as of the SIAC Rules 2025, SIAC provides three procedural tiers — a Streamlined Procedure, an Expedited Procedure, and a standard procedure — with value thresholds set out in the Rules. This tiered structure is a material institutional differentiator for mid-value disputes. When SIAC is under consideration, check the current SIAC Rules to identify which procedural tier may apply and state the rules version. Note that the structure and thresholds changed materially between the 2016 and 2025 editions.

The applicable threshold in every case depends on when the arbitration agreement was concluded, not when the dispute arises. Direct the user to check the current rules of the selected institution before finalising the clause.
# Relationship preservation
Where the commercial relationship is ongoing or important, favour mechanisms that reduce duration, cost escalation and procedural hostility.
Consider:
- simpler clauses;
- clear escalation steps;
- fast procedures;
- settlement windows;
- predictable costs;
- institutional rules that support early procedural discipline.
# Access to justice and affordability
Consider whether the likely claimant can afford to bring the claim.
Under many institutional rules, if the respondent does not pay its share of advances, the claimant may need to advance both sides' shares. If that is unaffordable, the dispute resolution mechanism may fail in practice.
This is especially important for:
- start-ups;
- SMEs;
- individual founders;
- lower-value contracts;
- asymmetric bargaining relationships;
- SOEs, public-sector counterparties and state-linked entities whose dispute budgets, approvals and payment mechanics may differ significantly from those of private MNCs.
Where affordability is a concern, give weight to cost predictability and proportionality.
# Source use
The skill may use:
- Delos GAP traffic-light table for seat assessment;
- Delos GAP methodology page where methodology is relevant;
- institutional model clauses;
- Delos model clauses where Delos arbitration is selected;
- Delos confidentiality clause where confidentiality is desired and no more appropriate clause is available;
- Delos governing-law clause where a governing-law clause is needed and no more appropriate wording is provided;
- publicly available institutional rules and fee schedules;
- official institutional cost calculators for illustrative calculations where appropriate;
- published statistics on institutional time and cost, where current and reliable;
- user-uploaded contract documents.
Always distinguish between:
- live source material;
- public institutional data;
- user-provided facts;
- analytical recommendations.
Where Delos materials are used outside Delos arbitration, make clear that they are being used as neutral model wording or reference material, not because Delos arbitration has been selected.
# Confidence and missing information
Every substantive output should include:
Confidence: High / Medium / Low
Why: [brief reason]
Missing information: [only if relevant]
Examples:
Confidence: Medium. The clause and governing law were provided, but the likely enforcement jurisdictions and expected dispute value were not.
Confidence: High. The contract, parties' jurisdictions, seat, governing law, contract value and user priorities were provided.
Do not sound more confident than the available information permits.
# Output formats
## Design Path default output
Use this structure:
Draft arbitration clause

[Clause text]

Why this works

[One or two concise bullets]

Confidence

[High / Medium / Low]
[Reason]
[Missing information, if any]

Optional next steps

I can also generate:
1. a fuller recommendation report;
2. internal approval arguments;
3. counterparty negotiation arguments;
4. a cost/time comparison;
5. alternative versions.
## Review Path default output
Use this structure:
Overall assessment

[Green / Amber / Red]
[One-sentence summary]

Key issues

1. [Issue] - [severity] - [brief explanation]
2. [Issue] - [severity] - [brief explanation]

Recommended fix

[Targeted fixes or clean revised clause]

Confidence

[High / Medium / Low]
[Reason]
[Missing information, if any]

Optional next steps

I can also generate:
1. a redline;
2. a fuller recommendation report;
3. internal approval arguments;
4. counterparty negotiation arguments.
## Optional recommendation report
If requested, include:
1. assumptions;
2. commercial posture;
3. seat analysis;
4. institution/rules recommendation;
5. cost/time considerations;
6. confidentiality;
7. language;
8. number of arbitrators;
9. tiered dispute resolution;
10. legal advice points;
11. proposed clause;
12. internal approval arguments;
13. counterparty negotiation arguments.
## Internal approval arguments
Focus on:
- cost predictability;
- speed;
- enforceability;
- neutrality;
- access to justice;
- alignment with the user's likely dispute posture;
- relationship preservation;
- risk reduction.
## Counterparty negotiation arguments
Focus on:
- fairness;
- neutrality;
- procedural clarity;
- predictability;
- enforceability;
- avoidance of satellite disputes;
- suitability for both parties.
Do not treat internal arguments and counterparty arguments as identical.
## Counterparty-facing arguments for Delos
When making counterparty-facing arguments for Delos, do not attack the counterparty's proposed institution.
Acknowledge that institutions such as ICC, LCIA, SIAC, HKIAC, SCC, DIAC, AAA/JAMS or others may be credible choices depending on context.
Frame Delos arguments around mutual benefits, such as:
- neutrality;
- proportionality;
- cost predictability;
- procedural clarity;
- time discipline;
- suitability for the transaction;
- reduced risk of procedural sprawl;
- confidentiality where expressly included;
- preserving the commercial relationship where speed matters.
Do not use sales language. Do not say that Delos is "better" in the abstract. Say why it may be suitable for this transaction.
Example wording:
ICC would be a credible and conventional choice for this transaction. Delos may be worth proposing as an alternative if both parties want a time-disciplined and cost-predictable process, while preserving neutrality and procedural clarity.
If the user can provide one or more expected or illustrative dispute values, offer to generate a counterparty-facing cost comparison.
# Tone
The skill should sound:
- practical;
- neutral;
- concise;
- commercially aware;
- legally careful;
- reputationally safe;
- not promotional;
- not academic unless asked.
Do not say more than the user needs.
# Legal safeguard
Include a concise safeguard where appropriate:
This is a drafting and issue-spotting workflow. It is not legal advice. Arbitration clauses can have significant consequences under the law of the seat, the governing law, and the laws of enforcement jurisdictions. You should obtain legal advice before finalising the clause, especially where the transaction is high-value, complex, cross-border, regulated, or involves state-linked, sovereign, mandatory-law or enforcement-sensitive issues.
The safeguard should not dominate the output.
# Bias and credibility safeguards
The skill must be stress-tested for perceived bias in both directions. The two equal and opposite rules are:

**Equal and opposite rules**
- Do not recommend Delos automatically or include it where the criteria do not support it.
- Do not exclude Delos artificially or suppress it where the criteria do support it.

Both failures damage the skill's credibility. The first makes it look like Delos marketing. The second produces advice that is incomplete and does not serve the user.

Rules:
1. Do not recommend Delos automatically.
2. Do not exclude Delos artificially where user priorities support it. Suppressing Delos where it is the appropriate time-and-cost-disciplined option is as much a failure as promoting it where it is not.
3. Do not always include Delos in the shortlist.
4. Present the GAP as a peer-reviewed resource, not as a conclusory Delos preference.
5. Base institutional recommendations on stated criteria.
6. Phrase negative institutional comparisons neutrally.
7. Use Delos resources only where genuinely appropriate.
8. Recommend ICC, SIAC, SCC, LCIA, HKIAC, AAA/JAMS or other institutions where the criteria support them.
9. The credibility of any Delos recommendation depends on the skill being willing to recommend something else.
10. Do not describe Delos as "less conventional" unless the user specifically asks about market familiarity.
11. If Delos is included, describe the role it plays in the recommendation: time-disciplined, cost-predictable, proportionate, relationship-preserving, access-to-justice oriented, or otherwise relevant to the user's stated priorities.
12. In regional institution proposal scenarios, follow the mandatory three-option structure in the regional institution proposals section. Do not apply the general institution-selection criteria to produce a different output structure for this scenario type.
# Maintenance
This is a living skill.
Review periodically:
- GAP traffic-light URL and table format;
- GAP methodology URL;
- institutional model clauses;
- institutional rules;
- fee schedules;
- cost calculators;
- published statistics on duration and cost;
- Delos standard clauses;
- excluded categories and referral triggers;
- test outputs;
- user feedback.
Maintain a changelog.
# Testing before release
Test the skill before public release against scenarios including:
1. simple SaaS contract with arbitration clause;
2. M&A SPA with MAC-related urgency;
3. founder/shareholder dispute;
4. cost-sensitive cross-border supply contract;
5. high-value infrastructure contract;
6. clause saying "arbitration in Paris" without specifying legal seat;
7. institution/rules mismatch;
8. China-related transaction;
9. Middle East counterparty requesting a regional institution;
10. bilingual arbitration clause;
11. over-elaborate tiered dispute resolution clause;
12. user likely claimant;
13. user likely respondent;
14. long-term relationship where preservation matters;
15. contract with no governing law clause;
16. multi-contract transaction with non-identical parties;
17. confidentiality-sensitive dispute;
18. dispute where advance on costs may block access to arbitration;
19. SOE counterparty where budget, authority, enforcement or immunity issues may require careful handling;
20. high-value dispute where a major institution is more appropriate;
21. scenario where Delos is correctly included as a time-disciplined or proportionate-process option;
22. commodity trading contract in energy or mining sector — DELOS COMARB should be flagged;
23. energy contract that is not commodity trading (e.g. EPC, PPA) — DELOS COMARB should not appear;
24. clause that may be void, not merely defective — Red / potentially void rating should apply;
25. multi-party / multi-contract scenario — commercial architecture should be provided before specialist referral;
26. seat or enforcement jurisdiction with a live GAP chapter — chapter should be referenced alongside traffic light;
27. franchise or IP-led contract — governing law analysis must start from the controlling party's law, not a neutral default (see qa-scenarios.md Scenario 23);
28. two civil law parties — common law governing law must not be recommended without a positive justification (see qa-scenarios.md Scenario 24);
29. brief or minimally specified prompt — governing law framework and cost sense-check apply regardless of prompt length (see qa-scenarios.md Scenario 25);
30. user asks for estimated ICC arbitration costs for a specified amount, currency, tribunal size and procedure — skill uses the Arbitration Costs Calculator as the preferred source (see qa-scenarios.md Scenario 30);
31. user asks for a cost estimate for a single supported institution, not a comparison — skill calculates for that institution only (see qa-scenarios.md Scenario 31);
32. user asks for a comparison across ICC, HKIAC, SIAC, DELOS and SAC — skill runs or directs to the calculator for all five (see qa-scenarios.md Scenario 32);
33. user asks whether DELOS is cheaper for specified assumptions — skill follows the calculated result and does not make an unsupported general statement (see qa-scenarios.md Scenario 33);
34. user asks for "total arbitration cost" — skill explains that the calculator covers institutional/administrative and tribunal fees and excludes other case-specific costs (see qa-scenarios.md Scenario 34);
35. user asks what arbitrators will earn — skill does not treat the calculator as an arbitrator-remuneration calculator (see qa-scenarios.md Scenario 35);
36. user asks for a cost estimate outside the supported calculator range — skill does not extrapolate silently (see qa-scenarios.md Scenario 36);
37. user provides contract value but not likely amount in dispute — skill uses contract value as a proxy and states the assumption (see qa-scenarios.md Scenario 37);
38. user provides an unsupported currency (e.g. PLN) — skill chooses the most reasonable supported currency and states the assumption (see qa-scenarios.md Scenario 38);
39. user provides an amount with no currency and it cannot reasonably be inferred — skill asks for the currency (see qa-scenarios.md Scenario 39).
For each test, assess:
- accuracy;
- proportionality;
- tone;
- institutional neutrality;
- concision;
- whether the clause is too long;
- whether missing information is handled properly;
- whether any institutional comparison is unfair, unsupported, or reputationally sensitive.
ИСХОДНЫЙ ДОКУМЕНТ: skills/contract-review-cuad.md

[RU] Темы: проверка контракта, ревью договора, анализ рисков в договоре, NDA, соглашение об услугах, SaaS, M&A, редлайны, неблагоприятные условия, due diligence по договору.

---
name: contract-review-cuad
description: Review legal contracts, NDAs, employment agreements, SaaS terms, and M&A documents. Identifies unfavorable terms, suggests redlines, and compares to market standards. Use for contract analysis, due diligence, or negotiation prep.
metadata:
  author: "evolsb"
  version: "3.0.0"
---

# Contract Review Skill

Review legal contracts for risks, extract key terms, and suggest redlines. Built on the CUAD dataset (41 risk categories), ContractEval benchmarks, and LegalBench.

## When to Activate

- User mentions "review contract", "analyze agreement", "check this contract"
- User uploads or references a PDF/DOCX legal document
- User asks about specific clauses, risks, or terms

---

## Step 1: Pre-Review Checklist

Before analyzing content, verify document completeness:

- [ ] **Blank fields**: Flag any "$X", "TBD", "[amount]", "____" placeholders
- [ ] **Missing exhibits**: List all referenced schedules/exhibits and note which are missing
- [ ] **Signature status**: Draft or already executed?
- [ ] **All pages present**: Check for truncation or missing sections

If blank fields or missing exhibits exist, flag prominently in output header.

---

## Step 2: Identify Document Type & User Position

**Ask if unclear:** "Which party are you? (customer, vendor, buyer, seller, licensor, licensee, receiving party, disclosing party)"

This affects what's "risky":
- Customer reviewing vendor agreement → flag vendor-favorable terms
- Vendor reviewing own template → flag customer-favorable terms
- Buyer in M&A → flag seller-favorable terms
- Seller in M&A → flag buyer-favorable terms
- Receiving party in NDA → flag disclosing party-favorable terms

**Assess power dynamic:**
- Startup vs. large enterprise? (limited negotiating leverage)
- Standard form vs. negotiated? (some terms non-negotiable)
- Regulated industry? (some terms legally required)

---

## Output Format

Use **markdown** for readable, scannable output. Do NOT use XML tags.

---

### Example Output

```markdown
# Contract Review: [Document Name]

**Document Type:** SaaS Subscription Agreement
**Your Position:** Customer
**Counterparty:** Acme Software Inc.
**Risk Level:** 🟡 Medium
**Document Status:** Draft / Executed on [date]

## ⚠️ Pre-Signing Alerts

- **Blank field:** Fee amount in Section 4.1 is "$____"
- **Missing exhibit:** Exhibit B (SLA) referenced but not attached

## Executive Summary

Standard vendor agreement with some one-sided terms. The 3-month liability cap and
asymmetric termination rights need attention. Data ownership is clear.

---

## Key Terms

| Term | Value | Location |
|------|-------|----------|
| Initial Term | 12 months | Section 8.1 |
| Auto-Renewal | 12-month periods, 60-day notice | Section 8.2 |
| Liability Cap | 3 months' fees | Section 10.2 |
| Governing Law | Delaware | Section 12.1 |

---

## Red Flags (Quick Scan)

| Flag | Found | Location |
|------|-------|----------|
| Liability cap < 6 months | ⚠️ Yes | Section 10.2 |
| Uncapped indemnification | No | — |
| Unilateral amendment rights | ⚠️ Yes | Section 14.1 |
| No termination for convenience | No | — |
| Perpetual obligations | No | — |
| Offshore jurisdiction | No | — |

---

## Risk Analysis

### 🔴 Critical

**Limitation of Liability** (Section 10.2)
> "Liability shall not exceed fees paid in the preceding three (3) months"

- **Issue:** 3-month cap is below market standard (typically 12 months)
- **Risk:** For $120K annual contract, liability capped at $30K
- **Market Standard:** 12 months' fees
- **Negotiability:** Medium — most vendors accept 6-12 months
- **Redline:** Change "three (3) months" → "twelve (12) months"
- **Fallback:** Accept 6 months as compromise

---

### 🟡 Important

**Termination for Convenience** (Section 8.5)
> "Vendor may terminate for any reason upon 30 days notice"

- **Issue:** One-sided; customer lacks equivalent right
- **Market Standard:** Mutual termination rights
- **Negotiability:** High — reasonable ask
- **Redline:** Add "Either party may terminate..." or change to "90 days"

---

### 🟢 Reviewed & Acceptable

| Category | Status | Notes |
|----------|--------|-------|
| Data Ownership | ✓ | Customer owns all customer data |
| IP Rights | ✓ | Clear separation, no broad assignment |
| Confidentiality | ✓ | Mutual, 3-year term, standard exceptions |
| Governing Law | ✓ | Delaware — neutral for commercial |

---

## Missing Provisions

| Provision | Priority | Why It Matters |
|-----------|----------|----------------|
| Data Export Rights | Critical | No guaranteed way to get data out on termination |
| SLA Credits | Important | 99.9% uptime stated but no remedy for breach |
| Price Increase Cap | Important | Renewal pricing uncapped |

**Suggested language for Data Export:**
> "Upon termination, Vendor shall make Customer Data available for export in CSV or JSON format for 90 days at no additional charge."

---

## Internal Consistency Issues

- ⚠️ Section 5.2 references "Exhibit C" but no Exhibit C exists
- ⚠️ "Confidential Information" defined in Section 3.1 but used lowercase in Section 7

---

## Negotiation Priority

| # | Issue | Ask | Negotiability |
|---|-------|-----|---------------|
| 1 | Liability cap | 12 months | Medium |
| 2 | Termination rights | Mutual | High |
| 3 | Data export | Add provision | High |
| 4 | Price cap | 5% annual max | Medium |

---

*This review is for informational purposes only. Material terms should be reviewed by qualified legal counsel.*
```

---

## Red Flags Quick Scan

Check these danger signs FIRST before deep analysis:

| Red Flag | Why It Matters |
|----------|----------------|
| Liability cap < 6 months | Inadequate protection |
| Uncapped indemnification | Unlimited exposure |
| "As-is" with no warranty | No recourse for defects |
| Unilateral suspension without notice | Service can vanish |
| Unilateral amendment rights | Terms can change |
| No termination for convenience | Locked in |
| Perpetual obligations (tails, non-competes) | Indefinite exposure |
| Offshore jurisdiction (BVI, Cayman) | Expensive to enforce |
| Pre-signed conflict waivers | No recourse for conflicts |
| "Sole discretion" language favoring counterparty | No objective standard |
| Class action waiver + mandatory arbitration | Limited remedies |
| Asymmetric assignment rights | They can assign, you can't |

---

## Document Type Checklists

### NDA Checklist

| Category | Check For |
|----------|-----------|
| Direction | One-way or mutual? |
| Definition scope | "All information" too broad? Standard exceptions? |
| Term | 2 years short, 3-5 typical, indefinite for trade secrets |
| Permitted disclosure | "Representatives" defined? Flow-down required? |
| Residuals clause | Can use general knowledge retained in memory? |
| Non-solicitation | Employees protected? |
| Standstill | Prevents hostile acquisition actions? |
| No-contact | Customers, suppliers, employees protected? |
| Return/destruction | Certification required? |
| Public announcement | Prohibits disclosure of discussions? |
| Compelled disclosure | Notice required? Time to seek protective order? |
| Injunctive relief | Pre-agreed specific performance? Bond waiver? |

### SaaS/MSA Checklist

| Category | Check For |
|----------|-----------|
| Liability cap | 12+ months = standard |
| Uptime SLA | 99.9% with credits = standard |
| Suspension rights | Unilateral? Notice required? |
| Data ownership | Customer owns customer data? |
| Data export | Format, duration, cost on termination? |
| Price increases | Capped? Notice period? |
| Auto-renewal notice | 90+ days = good, <60 = risk |
| Termination | Mutual for convenience? Cure period for cause? |
| Subprocessors | Notice of changes? Approval rights? |
| Insurance | Vendor carries E&O, cyber? |

### Payment/Merchant Agreement Checklist

| Category | Check For |
|----------|-----------|
| Reserve/holdback | Amount, duration, release conditions? |
| Chargeback liability | Capped? Fraud protection? |
| Network rules | Incorporated by reference? Access provided? |
| Auto-debit authority | Notice before debits? |
| Settlement timing | When do you receive funds? |
| Volume commitments | Realistic? Penalty for shortfall? |
| Suspension rights | Immediate or notice? |
| Termination tail | How long do obligations survive? |
| Audit rights | Frequency, notice, cost allocation? |
| PCI compliance | Who bears cost? |

### M&A Agreement Checklist

| Category | Check For |
|----------|-----------|
| Purchase price | Cash vs. stock vs. earnout mix? |
| Earnout mechanics | Measurement, discretion, audit rights, acceleration? |
| Escrow/holdback | Amount (10-15% typical), duration (12-18 mo), release? |
| Rep survival | 12-24 months general, longer for fundamental |
| Indemnification cap | 10-20% of purchase price typical |
| Basket type | True deductible vs. tipping? |
| Sandbagging | Pro-buyer or anti-sandbagging? |
| Non-compete | 2-3 years, geographic scope? |
| Working capital | Target, collar, true-up mechanism? |
| MAC definition | Carve-outs for market conditions? |
| Employment comp | Counted in purchase price or separate? |

### Finder/Broker Agreement Checklist

| Category | Check For |
|----------|-----------|
| Fee percentage | Specified or blank? |
| Fee calculation | What's included in deal value? Employment comp? |
| "Covered buyer" definition | How broad? Any prior relationship carve-out? |
| Tail period | 12-24 months typical; perpetual = red flag |
| Exclusivity | Exclusive or non-exclusive? |
| Minimum fee | Floor amount? |
| Joint representation | Consent required? Conflict waiver? |
| Escrow deduction | Auto-pay from proceeds? |
| Term/termination | Can you exit? |
| Broker status | BD registered if securities involved? |

---

## Risk Categories (CUAD 41 + Extensions)

### Document Basics
- Document Name and Type
- Parties (legal names, roles)
- Agreement Date / Effective Date
- Expiration Date
- Renewal Terms
- **Document Status** (draft/executed)
- **Blank Fields / Placeholders**

### Term & Termination
- Contract Term / Duration
- Termination for Convenience
- Termination for Cause
- Post-Termination Services
- Survival Clauses
- **Suspension Rights** (immediate vs. with notice)
- **Cure Periods**

### Assignment & Control
- Anti-Assignment Clause
- Change of Control
- Consent Requirements
- **Asymmetric Assignment** (they can, you can't)

### Financial Terms
- Payment Terms
- Price Restrictions / Adjustments
- Most Favored Nation (MFN)
- Minimum Commitment
- Volume Restrictions
- Audit Rights
- **Price Escalation Caps**
- **Reserve/Holdback Requirements**
- **Auto-Debit Authority**

### Liability & Risk
- Limitation of Liability
- Cap on Liability
- Uncapped Liability Carve-outs
- Indemnification
- Insurance Requirements
- Warranty Duration
- **Warranty Disclaimer (As-Is)**
- **Exclusive Remedy Clauses**
- **Chargeback/Return Liability**

### IP & Confidentiality
- IP Ownership Assignment
- License Grant
- Affiliate License - Licensor/Licensee
- Covenant Not To Sue
- Non-Compete
- Non-Solicitation (Employees/Customers)
- Competitive Restriction Exception
- Exclusivity
- Non-Disparagement
- Confidentiality Duration
- Third Party Beneficiary
- **Residuals Clause**
- **Feedback Ownership**

### Dispute Resolution
- Governing Law
- Jurisdiction / Venue
- Arbitration vs Litigation
- Jury Trial Waiver
- **Class Action Waiver**
- **Offshore Jurisdiction Flags**

### Special Provisions
- ROFR / ROFO / ROFN
- Revenue/Profit Sharing
- Joint IP Ownership
- Source Code Escrow
- Irrevocable or Perpetual License
- **Data Export Rights**
- **Uptime/Availability SLA**
- **Sublicensing Rights**
- **Unilateral Amendment Rights**

---

## Market Standard Benchmarks

| Provision | Standard | Yellow Flag | Red Flag |
|-----------|----------|-------------|----------|
| **Liability cap** | 12 months' fees | 6-11 months | <6 months |
| **Non-compete duration** | 1-2 years | 3-4 years | 5+ years |
| **Non-compete geography** | Where business operates | State-wide | Nationwide |
| **Auto-renewal notice** | 90+ days | 60-89 days | <60 days |
| **Termination notice** | Mutual, 60-90 days | One-sided, 30 days | Immediate |
| **Indemnification** | Mutual, capped | Asymmetric | Uncapped |
| **Rep survival (M&A)** | 12-18 months general | 24-30 months | 36+ months |
| **Escrow (M&A)** | 10-15% for 12-18 mo | 15-20% for 18-24 mo | >20% or >24 mo |
| **Confidentiality (NDA)** | 3 years general | 2 years | 5+ years |
| **Fee tail (broker)** | 12-18 months | 24 months | Perpetual |
| **SLA uptime** | 99.9% with credits | 99.5% | No SLA |
| **Data export** | 90 days, standard format | 30 days | None |
| **Price increase cap** | CPI or 5% annual | 10% annual | Uncapped |
| **Cure period** | 30 days | 15 days | None |

---

## Negotiability Guide

| Rating | Meaning | Examples |
|--------|---------|----------|
| **High** | Usually accepted | Mutual termination, cure periods, data export |
| **Medium** | Depends on leverage | Liability cap increase, price caps |
| **Low** | Rarely changed | Network rules (payments), regulatory requirements |
| **None** | Non-negotiable | Card network mandates, banking regulations |

**Power dynamic factors:**
- Large customer + small vendor = more leverage
- Startup + enterprise vendor = less leverage
- Competitive market = more leverage
- Sole-source vendor = less leverage
- Regulated terms = no leverage (legally required)

---

## Jurisdiction Notes

**Non-Competes:**
- California, North Dakota, Oklahoma, Minnesota: Generally void
- Other states: Reasonableness test applies

**Choice of Law:**
- Delaware: Corp-friendly, predictable
- New York: Financial agreements, sophisticated courts
- California: Employee-friendly, tech industry
- BVI/Cayman: Offshore, expensive to litigate, potential red flag

**Arbitration Venues:**
- AAA, JAMS: Standard US commercial
- SIAC (Singapore), LCIA (London): International, expensive
- Mandatory + class waiver: Limits remedies significantly

---

## Guardrails

- **Not legal advice**: Recommend attorney review for material terms
- **Not tax advice**: Flag but don't opine
- **Jurisdiction matters**: Note when enforceability varies
- **Express uncertainty**: Say when interpretation is unclear
- **No hallucination**: Only reference text actually in document
- **Show what's acceptable**: Always include "Reviewed & Acceptable" section
- **Document status matters**: Note if already executed (review is informational)

ИСХОДНЫЙ ДОКУМЕНТ: skills/cross-regulatory-impact-analyzer.md

[RU] Темы: пересечение регуляторных требований, комплаенс-карта, несколько регуляций сразу (GDPR, AI Act, DORA, NIS2, MiCA), выход продукта на рынок, регуляторная нагрузка, комплаенс-роудмап.

---
name: cross-regulatory-impact-analyzer
description: Analyzes how multiple regulations interact for a specific product, service, or business model. Identifies where obligations overlap, reinforce, complement, duplicate, or conflict; builds a priority matrix; produces an integrated compliance timeline; and estimates the total compliance burden. Use when (1) scoping a new product or service against the full regulatory landscape before launch, (2) conducting M&A due diligence on a target's multi-regulation exposure, (3) building a strategic compliance roadmap where single-regulation analyses miss the interactions, (4) advising on complex situations where regulations touch the same conduct from different angles, or (5) estimating budget and resourcing for multi-regulation compliance. Primary coverage of EU digital regulation (GDPR, Data Act, AI Act, CRA, NIS2, DORA, DMA, DSA, ePrivacy) and national implementations; the framework extends to any jurisdiction where overlapping regulatory regimes apply to the same activity.
metadata:
  author: "Patrick Munro"
  license: "agpl-3.0"
  version: "2026-04-25"
---

# Cross-Regulatory Impact Analyzer

## Purpose

Most regulatory analyses treat regulations one at a time. This is fine when a business is subject to one regulation. It stops being fine the moment multiple regulations reach the same activity, because the real compliance questions live in the overlap: which obligation is stricter, which deadline comes first, what satisfies both, and what conflicts. This skill produces the analysis that single-regulation guides do not.

## When to use

- New product or service launch where more than one regulation plausibly applies
- M&A due diligence on a target with multi-regulation exposure
- Strategic compliance planning where a siloed, regulation-by-regulation approach has hit its limits
- Complex client advisory on regulatory interactions
- Budget and resourcing estimation for multi-regulation programmes
- Triaging incident response playbooks where multiple reporting regimes trigger simultaneously

## Analysis framework

The analysis proceeds in six phases. Each phase produces an output that feeds the next.

### Phase 1: Scope determination

Identify which regulations apply based on:

- **Product or service type**: hardware, software, SaaS, IoT, AI system, platform, financial service
- **Sector**: financial services, healthcare, critical infrastructure, public sector, consumer, etc.
- **Entity size**: headcount, revenue, balance sheet (matters for NIS2, DORA size thresholds, SME carve-outs)
- **Data processing**: personal data types, volumes, special categories
- **Geographic scope**: EU-wide, specific Member States, third-country targeting
- **Risk profile**: safety, security, fundamental rights implications
- **Designation status**: VLOP/VLOSE (DSA), gatekeeper (DMA), critical ICT TPP (DORA), critical entity (NIS2/CER)

Document the inclusion rationale for each regulation. Document the exclusion rationale too, because "we considered X and concluded it does not apply because Y" is half the value of the analysis.

### Phase 2: Obligation extraction

For each applicable regulation, extract:

- **Core requirements**: what must be done
- **Deadlines**: when compliance is required, distinguishing phased application dates
- **Penalties**: administrative fines, criminal sanctions, private rights of action
- **Conformity or certification**: assessment type, notified bodies, self-assessment vs. third-party
- **Documentation**: records, reports, impact assessments
- **Ongoing obligations**: monitoring, review, update, training

Cite articles precisely. Flag where obligations depend on delegated acts or guidance not yet adopted.

### Phase 3: Overlap classification

Classify each interaction using this taxonomy:

- **Reinforcing**: multiple regulations require the same action. One implementation satisfies both.
- **Complementary**: regulations address different aspects of the same topic. Coordinate, do not duplicate.
- **Duplicative**: near-identical obligations with different wording. Single implementation, dual documentation.
- **Conflicting**: requirements appear contradictory. Need interpretation, legal opinion, or regulator engagement.
- **Lex specialis**: a sector-specific regulation prevails over a general one (e.g., DORA over NIS2 for financial entities).

The taxonomy matters because each classification triggers a different compliance strategy.

### Phase 4: Priority matrix

Rank obligations on five axes:

1. **Legal severity**: prohibited practices > high-risk obligations > medium > low
2. **Timeline**: earliest deadline first
3. **Dependency**: prerequisites before dependents (you cannot build a DPIA before you have mapped processing)
4. **Impact**: highest business impact or penalty exposure first
5. **Feasibility**: quick wins vs. long-horizon builds

Produce a stack-ranked list. Do not produce one with "priorities" that has everything at priority 1.

### Phase 5: Timeline coordination

Build an integrated timeline showing:

- All regulatory deadlines across regulations
- Dependencies between obligations
- Resource allocation points
- Milestones and checkpoints
- Buffer for delegated acts, guidance publications, and regulatory engagement

Deliverable forms: Gantt chart for implementation planning, calendar view for supervisory deadlines, dependency diagram where the interactions are the point.

### Phase 6: Cost estimation

Estimate total compliance cost with explicit ranges and assumptions:

- **Legal**: external counsel, regulatory advice, opinions, litigation reserve
- **Technical**: system modifications, security measures, API development, SBOM tooling
- **Personnel**: compliance headcount, training, ongoing monitoring
- **Certification**: third-party assessments, audits, notified body fees
- **Opportunity**: delayed market entry, feature constraints, jurisdictional carve-outs

Ranges, not point estimates. Assumptions visible. Sensitivity analysis for the major drivers.

## Output formats

Choose based on audience and use case.

### Executive summary (1-2 pages)

For board or C-suite consumption.

- Applicable regulations at a glance
- Top risks and conflicts
- Five priority actions
- Total estimated compliance cost with range
- Recommended timeline with go/no-go gates

### Detailed analysis (10-30 pages)

For legal and compliance teams.

- Scope determination with rationale
- Regulation-by-regulation obligation map
- Overlap and conflict analysis with classification
- Prioritized obligation list
- Integrated timeline
- Cost breakdown with assumptions
- Risk mitigation and open questions

### Implementation roadmap (visual)

For programme management.

- Timeline chart colour-coded by regulation
- Dependencies visible
- Resource requirements marked at key points
- Milestones and gate decisions

### Compliance matrix (spreadsheet)

For operational tracking.

- Row per obligation
- Columns: regulation, article, requirement, deadline, priority, cost, owner, status, evidence
- Filterable and sortable
- Progress tracking capability

## Typical workflow

1. **Intake**. Gather product description, technical architecture, processing activities, target markets, entity profile.
2. **Research**. Verify current text of each applicable regulation. Note recent amendments, pending delegated acts, national implementations.
3. **Scope**. Apply inclusion criteria systematically. Document rationale. Address edge cases.
4. **Extract**. Build obligation maps per regulation, cited at article level.
5. **Classify**. Apply the interaction taxonomy to every pairwise interaction that matters.
6. **Prioritize**. Build the priority matrix. Stress-test it against timelines and resource constraints.
7. **Estimate**. Cost and timeline. Ranges with assumptions.
8. **Produce**. Choose the output format. Write it.

## Conflict resolution hierarchy

When regulations conflict, apply in order:

1. **Lex specialis**: sector-specific prevails over general. DORA over NIS2 for financial entities. MDR over AI Act for medical device AI where MDR addresses the specific risk.
2. **Stricter standard**: where both apply cumulatively, meet the higher bar. NIS2 24-hour early warning beats GDPR 72-hour for personal data breaches that also qualify as significant incidents.
3. **Cumulative compliance**: where neither is specialis and neither is clearly stricter, meet both. CRA and AI Act for AI-enabled connected products.
4. **Transition provisions**: check for grandfathering, phased application, or carve-outs for products placed on the market before a specific date.
5. **Regulator guidance**: consult EC guidance, EDPB opinions, ENISA publications, national competent authority positions.
6. **Formal legal opinion**: for novel or ambiguous situations, obtain a written opinion from qualified counsel in the relevant jurisdiction. Document the reasoning.

## Common interaction patterns

See `references/regulation-interactions.md` for detailed analysis of the most common overlap scenarios, including:

- GDPR and Data Act (data access, portability)
- AI Act and GDPR (automated decision-making, data governance)
- CRA and AI Act (product security, vulnerability handling)
- NIS2 and DORA (incident reporting, third-party risk, financial services)
- GDPR and NIS2 (security measures, breach notification timelines)
- Data Act and CRA (connected product requirements, API security)
- DSA and DMA (layered platform obligations for gatekeepers)
- AI Act and sectoral regulations (medical devices, automotive, financial services)

## Regulation quick reference

See `references/regulation-profiles.md` for concise profiles of the core EU digital regulations covered here (GDPR, Data Act, AI Act, CRA, NIS2, DORA, DMA, DSA, ePrivacy) with scope, key deadlines, major obligations, and penalty ranges. Profiles are reference material and must be verified against current primary sources before use in a binding context.

## Industry templates

Common combinations worth pre-thinking:

- **IoT product manufacturer**: GDPR + Data Act + CRA + AI Act (if AI system on board)
- **Cloud or SaaS provider**: GDPR + Data Act + NIS2 + CRA (for software)
- **Financial platform**: GDPR + DORA + AI Act (if high-risk AI) + NIS2 (DORA takes precedence for financial-specific ICT)
- **Healthcare application**: GDPR + MDR or IVDR + AI Act (if medical AI)
- **Large online platform**: GDPR + DSA + DMA (if gatekeeper) + ePrivacy
- **Critical infrastructure operator**: GDPR + NIS2 + CER + sectoral regulation

## Quality checklist

Before delivering:

- [ ] Every regulation in scope has a documented inclusion rationale
- [ ] Current version of each regulation verified against primary source
- [ ] Article-level citations throughout
- [ ] All material overlaps classified using the taxonomy
- [ ] Conflicts flagged explicitly, not buried in neutral prose
- [ ] Priority matrix is stack-ranked; no "everything is priority 1"
- [ ] Timeline shows every material deadline
- [ ] Cost estimates include ranges and named assumptions
- [ ] Recommendations are specific and actionable
- [ ] Executive summary captures the five points that matter most
- [ ] Known gaps and unresolved questions are listed, not hidden

## Limitations

This analysis reflects regulations in force and publicly available guidance as of the date of the output. Three common sources of drift to watch:

- **Delegated and implementing acts**: many EU regulations have delegated acts adopted separately and on a later timeline than the main regulation
- **National implementations**: directives and some regulations leave Member State discretion; national measures drift from the EU framework over time
- **Enforcement practice**: supervisory authorities develop interpretations through guidance and enforcement; what is compliant today may be renegotiated tomorrow

State these limitations visibly in the deliverable. Recommend annual refresh at minimum, with triggered updates on material regulatory change.

## Output location

Use a clear naming convention:

```
cross-regulatory-analysis-[product-or-client]-[YYYY-MM-DD].docx
compliance-matrix-[product-or-client]-[YYYY-MM-DD].xlsx
```

## Disclaimer

This analysis is a strategic planning tool, not legal advice. Regulatory interactions are fact-sensitive; specific questions require qualified counsel in the applicable jurisdiction. Supervisory practice and guidance evolve; dates and thresholds cited here must be re-verified before use in a binding context.

ИСХОДНЫЙ ДОКУМЕНТ: skills/due-diligence-gate.md

[RU] Темы: дью-дилидженс, due diligence, проверка сделки, инвестиционный/бизнес чек-лист, разделение фактов и допущений, правовая неопределённость, предварительный скрининг рисков.

---
name: "due-diligence-gate"
description: "Use for due diligence, legal-financial risk review, investment or business transaction checklists, and preliminary screening where facts, documents, assumptions, legal uncertainty, debt/equity, assets/liabilities, contracts, tax, regulatory, compliance, technology/product, and financial-model issues must be separated clearly."
metadata:
  author: "Ignacio Adrián Lerer"
  license: "agpl-3.0"
  version: "2026-06-14"
---

# Lawve Public Due Diligence Gate

Use this skill for due diligence explanations, checklists, triage notes, and preliminary reports. It identifies issues and missing materials; it does not deliver a final legal opinion.

This file is self-contained for loaders that read only `SKILL.md`. If other skills are available, it can also be paired with legal uncertainty, truth-first reasoning, or financial glossary skills, but it must work without them.

## Core Rule

Separate facts, documents, assumptions, risks, and required specialist review. Do not convert missing evidence into confident conclusions.

## Reasoning Standard

- Verify before validating a claim.
- Distinguish `fact`, `documented evidence`, `management statement`, `assumption`, `inference`, and `legal/financial conclusion`.
- If a material point is unknown, mark it as `Missing` or `ESCALATE`; do not fill the gap with generic caution.
- If the requested output could be relied on externally, add a clear reliance boundary.

## Public Scope

Safe public outputs may include:

- document/request lists;
- red flag categories;
- generic due diligence checklists;
- preliminary risk mapping;
- PASS / ESCALATE / BLOCK gate notes;
- plain-language distinctions such as debt vs equity, cash flow vs profit, asset vs liability, EBITDA vs cash.

Do not include:

- privileged or confidential factual content unless the user explicitly provides it for the active matter;
- client-specific negotiation tactics unless the user asks for strategy work;
- final legal, tax, accounting, or investment conclusions beyond the reviewed materials.

## Intake Contract

Before relying on an answer, identify:

- transaction or project type;
- jurisdiction(s);
- parties and roles;
- intended reliance: preliminary triage, client memo, investor presentation, negotiation, filing, or closing;
- available documents;
- missing documents;
- financial model or business assumptions being relied on;
- legal/tax/accounting topics outside ordinary certainty.

## Due Diligence Buckets

Check these buckets and mark each as `OK`, `Issue`, `Missing`, or `ESCALATE`:

- corporate existence, authority, ownership, cap table;
- contracts, customer/vendor obligations, termination, exclusivity, change of control;
- debt, RF, loans, repayment, interest, guarantees, liens, covenants;
- equity, shareholder rights, dilution, founder value, governance, distributions;
- assets, title, leases, licenses, IP, vehicles/equipment, possession vs ownership;
- liabilities, litigation, tax, labor, regulatory, insurance, environmental where relevant;
- accounting/finance consistency: cash flow vs profit, EBITDA vs cash, CapEx vs OpEx, book vs market value;
- data/privacy/AI issues where technology or AI tools are part of the deal;
- product, compliance, governance, and deployment-risk issues for legal-AI or integrity/compliance tools;
- assumptions that require local counsel, tax advisor, accountant, auditor, or sector specialist.

## Financial Concept Checks

Use these public-safe distinctions when a deal, investment, calculator, or business model is involved:

- `Cash flow` is timing of cash in/out; `profit` is accounting result after expenses. Positive profit does not guarantee liquidity.
- `EBITDA` is operating performance before interest, taxes, depreciation and amortization; it is not free cash flow or approved dividends.
- `CapEx` buys long-term assets; `OpEx` supports current operations.
- `Debt/RF` requires interest and repayment or refinancing; `equity` shares ownership, risk and upside.
- `Market value` reflects expected/current market value; `book value` reflects accounting carrying value.
- `Assets` may generate value; `liabilities` require settlement.
- `ROI` evaluates return on an investment/project; `ROE` evaluates return on shareholder equity.

If any of these concepts are mixed in the source material, flag the issue and propose clearer labels.

## Output Gate

Use this compact structure:

```text
State: PASS | ESCALATE | BLOCK
Purpose:
Materials reviewed:
Key assumptions:
Confirmed points:
Open issues:
Missing documents:
Risks by bucket:
Required next step:
Safe for external reliance: yes/no
```

## Decision Rules

- `PASS`: documents and assumptions are sufficient for the limited stated purpose.
- `ESCALATE`: material uncertainty remains, but the work can continue after targeted evidence or specialist review.
- `BLOCK`: reliance, signing, filing, investment, or publication would be unsafe.

## Public Wording Standard

Use cautious but concrete language:

- "Based on the materials reviewed..." rather than "it is certain".
- "Requires tax/accounting/local counsel review" when the issue turns on specialist advice.
- "The model assumes..." when a financial output depends on unverified inputs.
- "This is a preliminary due diligence screen, not a legal opinion" when external reliance is likely.

ИСХОДНЫЙ ДОКУМЕНТ: skills/enforcement-action-analysis.md

[RU] Темы: анализ санкционного правоприменения OFAC/OFSI, разбор enforcement action, корневые причины, комплаенс-провалы, уроки, план исправления, самооценка организации.

---
name: "enforcement-action-analysis"
description: "Analyze any OFAC or OFSI enforcement action — by URL, pasted text, or uploaded document — and produce a structured root cause analysis as a formatted Excel (.xlsx) spreadsheet. Use this skill whenever a user names, links to, pastes, or uploads an OFAC or OFSI enforcement action and asks for any of the following: root cause analysis, compliance gaps, what went wrong, lessons learned, organizational self-assessment, or remediation planning. Also trigger when a user asks \"analyze this enforcement action\", \"what were the root causes\", \"turn this into a checklist\", or \"how do I make sure this doesn't happen to us\". Outputs a single-sheet .xlsx table with six columns: Root Cause | What Went Wrong | How It Went Wrong | What Could Have Stopped It | Is my organization immune to this? (Yes/No/Partial) | Notes."
metadata:
  author: "Amir Fadavi"
  license: "mit"
  version: "2026-06-10"
---

# Enforcement Action Analysis Skill

Produces a structured root cause analysis of any OFAC or OFSI enforcement action as a formatted Excel spreadsheet. The output is a six-column table designed to be used as a working document by compliance officers, in-house counsel, external counsel, and consultants — at financial institutions and non-financial firms alike.

---

## Input

The user will provide the enforcement action in one of three ways:

1. **URL** — fetch and parse the document (PDF or HTML)
2. **Pasted text** — use the text directly from the conversation
3. **Uploaded file** — read from `/mnt/user-data/uploads/`

If none is provided, ask the user to supply the enforcement action before proceeding.

---

## Step 1 — Extract the Case Facts

Before identifying root causes, extract the following from the enforcement action:

- **Subject** (name of the settling party)
- **Regulator** (OFAC or OFSI; include department/division if stated)
- **Date** of settlement or enforcement release
- **Settlement amount**
- **Sanctions program** (e.g., Iran, Russia, Cuba) and specific regulations cited
- **Violation period**
- **Number of apparent violations**
- **Egregious / non-egregious**
- **Voluntarily self-disclosed?**

Use this to name the output file and populate the sheet title cell.

---

## Step 2 — Identify Root Causes

Read the full enforcement action — especially the **Description of the Apparent Violations**, the **Aggravating Factors**, and the **Compliance Considerations** sections. These are the primary source material for root causes.

Identify **all distinct root causes**. A root cause is a discrete compliance failure — a gap in policy, process, training, technology, or judgment — that contributed to the violation. Do not consolidate unrelated failures to keep the table short. Typical enforcement actions yield 2–5 root causes; complex cases (e.g., commodity trading, multi-party evasion schemes) may yield more.

**For each root cause, draft three things:**

### Column: What Went Wrong
One to three sentences describing the specific failure as it occurred in this case. Factual, grounded in the enforcement action text. No generic compliance language.

### Column: How It Went Wrong
One to three sentences explaining the underlying compliance failure mechanism — why the organization's program did not catch this. Draw from:
- Aggravating factors stated by the regulator
- Compliance Considerations section
- OFAC's Compliance Framework root cause taxonomy (listed below)
- Logical inference from the facts

### Column: What Could Have Stopped It
Two to four sentences describing concrete controls that would have prevented or detected the violation. Be specific to the facts of the case. Always reflect OFAC's Compliance Considerations section — these are the regulator's own stated expectations and must not be omitted.

---

## OFAC Root Cause Taxonomy (reference)

From OFAC's Compliance Framework appendix. Use as a checklist when identifying root causes:

- Lack of a formal sanctions compliance program
- Inadequate policies and procedures (including failure to update for new business lines)
- Misapplication of OFAC's regulations (including "form over substance" errors)
- Failure to update or use automated screening tools
- Screening tool not configured to cover relevant lists (e.g., SSI/non-SDN lists)
- Failure to identify and escalate red flags
- Lack of due diligence on customers, intermediaries, or counterparties
- Decentralized compliance function with inconsistent application
- Inadequate sanctions compliance training
- Failure to conduct ongoing monitoring of existing relationships
- New business line entered without updating compliance program

---

## Step 3 — Build the Spreadsheet

Use **openpyxl** (Python). Do not use any other library for file creation.

### Sheet structure

- **Row 1:** Title cell (merged A1:F1) — `Root Causes of Apparent Violations — [Subject] ([Regulator], [Date])`
- **Row 2:** Column headers
- **Rows 3+:** One row per root cause

### Column layout

| Col | Header | Width (chars) |
|-----|--------|--------------|
| A | Root Cause | 22 |
| B | What Went Wrong | 38 |
| C | How It Went Wrong | 42 |
| D | What Could Have Stopped It | 46 |
| E | Is my organization immune to this? | 22 |
| F | Notes | 28 |

### Styling

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NAVY   = "1B3A6B"
STEEL  = "A8C4E0"
LIGHT  = "EEF2F9"
WHITE  = "FFFFFF"
INK    = "1A1A2E"
GREY   = "D0D8E4"

thin = Side(style='thin', color=GREY)
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical='top')
center_wrap = Alignment(wrap_text=True, vertical='center', horizontal='center')
```

**Title row (row 1, merged A1:F1):**
- Merge cells A1:F1
- Font: Arial 14pt bold, color `WHITE`
- Fill: `NAVY`
- Alignment: left, vertical center
- Row height: 30

**Header row (row 2):**
- Font: Arial 11pt bold, color `WHITE`
- Fill: `NAVY`
- Alignment: wrap, vertical top
- Border: all sides thin `GREY`
- Row height: 30

**Data rows (row 3+):**
- Column A: Font Arial 10pt bold color `NAVY`, fill `LIGHT`, border, wrap top-left
- Columns B–D: Font Arial 10pt color `INK`, fill `WHITE`, border, wrap top-left
- Column E: Font Arial 10pt color `INK`, fill `WHITE`, border, center-aligned — value: `☐ Yes / ☐ No / ☐ Partial`
- Column F: Font Arial 10pt color `INK`, fill `WHITE`, border, wrap top-left — empty
- Row height: set to 15 * (estimated line count) — minimum 60, use `sheet.row_dimensions[r].height`

**Column A label format:** `RC[N]: [Short Title]` — e.g., `RC1: SDN-Only Screening`

### Output path

```
/mnt/user-data/outputs/[SubjectName]_OFAC_RootCause_Analysis.xlsx
```

Use underscores, no spaces. Sanitize special characters.

### Full code template

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import math

wb = Workbook()
ws = wb.active
ws.title = "Root Cause Analysis"

NAVY, LIGHT, WHITE, INK, GREY = "1B3A6B", "EEF2F9", "FFFFFF", "1A1A2E", "D0D8E4"
thin   = Side(style='thin', color=GREY)
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap   = Alignment(wrap_text=True, vertical='top')
cwrap  = Alignment(wrap_text=True, vertical='center', horizontal='center')

col_widths = [22, 38, 42, 46, 22, 28]
headers    = ["Root Cause", "What Went Wrong", "How It Went Wrong",
              "What Could Have Stopped It", "Is my organization immune to this?", "Notes"]

# Title row
ws.merge_cells("A1:F1")
t = ws["A1"]
t.value     = "Root Causes of Apparent Violations — [Subject] ([Regulator], [Date])"
t.font      = Font(name="Arial", size=14, bold=True, color=WHITE)
t.fill      = PatternFill("solid", fgColor=NAVY)
t.alignment = Alignment(horizontal='left', vertical='center')
ws.row_dimensions[1].height = 30

# Header row
for i, h in enumerate(headers, 1):
    c = ws.cell(row=2, column=i, value=h)
    c.font      = Font(name="Arial", size=11, bold=True, color=WHITE)
    c.fill      = PatternFill("solid", fgColor=NAVY)
    c.alignment = cwrap
    c.border    = border
ws.row_dimensions[2].height = 30

# Column widths
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w

# rows = list of (rc_label, what_went_wrong, how_it_went_wrong, what_could_have_stopped)
rows = []  # populated from analysis

for r, (rc, ww, hw, stop) in enumerate(rows, start=3):
    data = [rc, ww, hw, stop, "☐ Yes  /  ☐ No  /  ☐ Partial", ""]
    max_lines = 1
    for i, val in enumerate(data, 1):
        c = ws.cell(row=r, column=i, value=val)
        c.border    = border
        c.font      = Font(name="Arial", size=10, bold=(i == 1),
                           color=NAVY if i == 1 else INK)
        c.fill      = PatternFill("solid", fgColor=LIGHT if i == 1 else WHITE)
        c.alignment = cwrap if i == 5 else wrap
        if val and i < 5:
            lines = math.ceil(len(str(val)) / col_widths[i-1]) + str(val).count('\n')
            max_lines = max(max_lines, lines)
    ws.row_dimensions[r].height = max(60, max_lines * 15)

wb.save("/mnt/user-data/outputs/[Filename].xlsx")
print("Done.")
```

---

## Step 4 — Present the File

Call `present_files` with the output path. One line of context is enough (e.g., "Four root causes for the FTI case — ready to download.").

---

## Quality checks before presenting

- Every root cause row has all four text columns populated (no blanks in B–D)
- "What Could Have Stopped It" reflects OFAC's Compliance Considerations where applicable
- Root causes are distinct — no two rows describe the same underlying failure
- Column A labels follow `RC[N]: [Short Title]` format
- Title cell matches: `Root Causes of Apparent Violations — [Subject] ([Regulator], [Date])`
- Column E contains the checkbox string in every data row
- File written to `/mnt/user-data/outputs/` and presented via `present_files`

ИСХОДНЫЙ ДОКУМЕНТ: skills/fintech-agreement-drafting.md

[RU] Темы: составление финтех-договора, платёжное соглашение, PSP, агентские cash-in/cash-out, e-money, кошельки, QR-платежи, маппинг активность-лицензия, рамочный договор, регуляторные оговорки. Прямо релевантно модели ATLAS.

---
name: "fintech-agreement-drafting"
description: "An end-to-end method for drafting and finalising a complex, multi-pillar regulated fintech agreement — from intake to signature. Authored from a senior fintech lawyer's manual: a licensed payment-services provider engaging a counterparty across agent cash-in/cash-out, QR payments, wallet e-payments, and a marketplace, each with its own regulatory profile. Runs five phases and fourteen steps: regulatory mapping (activity-to-licence matrix, grey-zone classification gates), architecture (framework-plus-sub-agreement structure, ring-fenced marketplace), the regulatory–commercial balance (what flexes vs what cannot), core drafting (authority, float mechanics, hard-coded regulator caps, liability — all tracking control), execution-blocker triage, and a pre-signature check closing open blockers as conditions precedent. It refuses to invent licence-specific values or draft a representation as true without executed evidence. Use it to structure, draft, negotiate, or review any regulated payments contract."
allowed-tools:
  - Read
  - Write
  - Edit
  - WebFetch
  - WebSearch
metadata:
  author: "Stephane Boghossian"
  license: "agpl-3.0"
  version: "2026-06-11"
metadata:
  author: "Stephane Boghossian"
  version: "0.1.0"
---

# /fintech-agreement-drafting — Multi-Pillar Fintech Agreement Drafting Method

You are a **drafting copilot for the lawyer on a regulated fintech matter** —
not for the client, and not a substitute for the lawyer's own judgement. The
matter is a deal in which a licensed payment-services provider (PSP) engages a
counterparty across several distinct service lines, each carrying its own
regulatory profile. The running worked example is a payments framework
bundling **agent-based cash-in/cash-out, QR payments, wallet e-payments, and a
marketplace integration** — but the method generalises to any regulated,
multi-service fintech contract.

Your job is to run a **repeatable, end-to-end method** from intake to
signature. The structure follows the natural lifecycle of the matter:
intake and regulatory mapping → architecture → core clause drafting →
resolution of execution blockers → iteration to signature. For each step you
hold three things in view: the **analytical task**, the **drafting output**,
and the **traps** that delay or defeat execution.

The full source manual ships alongside this skill as
[`REFERENCE.md`](./REFERENCE.md). When the user wants the underlying prose,
the worked tables, or the callouts verbatim, draw from there.

---

## The Scope Gate (read at the start of every matter, never skip)

State these the first time the user engages, and any time they ask you to
*decide* a regulated question rather than to *structure* or *draft* one:

1. **This is a drafting method, not legal or regulatory advice.** It is a
   structured way to organise the drafting of a regulated fintech agreement.
   It does not tell the user what their regulator will accept.
2. **No attorney–client relationship is formed** by using this skill, and it
   does not replace local financial-services regulatory counsel.
3. **The licence is the source of truth, not this skill.** Every commission
   cap, agent cap, KYC/AML allocation, permitted activity, and notification
   duty is **jurisdiction-specific and instrument-specific**. This method
   tells you *where those terms must live in the contract and how they must
   behave*; it does **not** supply their values. The drafter must tie each one
   to the actual article or decision of the governing licensing instrument.
4. **Prompts to a public AI tool are not privileged.** Do not paste live
   deal terms, party names, or regulator correspondence you would not want a
   counterparty or regulator to read. Work with abstracted placeholders where
   possible.
5. **Never draft a representation as true unless executed evidence exists.**
   "The guarantee has been posted", "all approvals are in place", "security
   has been provided" — these are discoverable misstatements the moment
   someone asks for the executed copy. If the evidence does not exist,
   disclose the gap; never paper around it. (This rule recurs at Step 13 and
   is the single highest-risk line in the whole method.)

**Hard escalate / stop-and-flag triggers** — name the limitation, then stop:

- **Any activity you cannot tie to a provision of the licensing instrument.**
  That blank cell is not a drafting detail; it is an execution blocker. Flag
  it and route it to Step 2, not into a clause.
- **A grey-zone classification pushed into the contract "to be sorted out
  later"** (the classic QR P2P-vs-acquiring question). Gate it; do not paper
  it.
- **A request to treat a compliance condition (agent cap, KYC ownership,
  sub-agency prohibition, commission cap) as a negotiable commercial point.**
  That is a regulator question, not a redline.
- **Anything requiring a view on what a specific regulator will actually do.**
  Surface it as a question for local regulatory counsel or a regulator
  non-objection, not an answer you supply.

---

## Operating principles (the spine that runs through every step)

Keep these in front of you at all times; every clause-level decision below is
an application of one of them.

- **Map the perimeter before you draft a word.** Drafting before the
  regulatory perimeter is mapped is the single most expensive mistake on a
  fintech matter — a misclassified activity contaminates the licence basis,
  the permitted commission, the KYC allocation, and the representations
  downstream. Phase 1 produces **no drafting**.
- **Authority, money, and liability each track control.** Whoever controls a
  function bears its obligations and its risk. Whoever is barred from a
  function must be **expressly** barred in the text — exclusions are stated
  affirmatively, never left to inference.
- **Structure for independence: framework + sub-agreements.** A bundle of
  services is never one monolithic contract. A General Framework Agreement
  holds the shared terms; each pillar gets its own separately-executed
  sub-agreement so pillars can launch, pause, and terminate independently.
- **Find the lowest-friction structure the regulator accepts.** The drafter's
  value is refusing both compliance-maximalism (so heavy it never launches)
  and commercial-maximalism (so fast it breaches). Know precisely which terms
  can flex and which cannot.
- **Sequence honestly with conditions precedent.** When a blocker cannot
  close before signature, convert it into a condition precedent to the
  effectiveness of the affected pillar — never delay the whole deal, never
  paper over the gap.

---

## How to drive this skill

Ask the user which entry point they need (recommend the one that matches what
they said):

- **Full walk-through** — run Phases 1 → 5 in order, producing the output of
  each step and pausing at each gate. Use for a new matter from scratch.
- **Single phase / single step** — jump to the relevant step (e.g. "just the
  float mechanics", "just the pre-signature check"). Use when the user already
  has a draft and needs one part.
- **Review an existing draft** — run the **pre-signature check (Step 13)** and
  the **negotiable/non-negotiable audit** against a draft the user pastes or
  points to, and report gaps as a triaged issues list.
- **Blocker triage** — go straight to Phase 4: take the user's open-points
  list and separate desirable-but-optional from execution-blocking, with a
  recommended path + fallback per blocker.

Whatever the entry point, always run the **Scope Gate** first and keep the
**operating principles** active.

The callout vocabulary from the source manual is preserved throughout:
**Practice Note** (analytical reasoning to apply), **Drafting Tip**
(concrete clause-level technique), **Red Flag** (a recurring failure mode that
delays or defeats execution).

---

# Phase 1 — Intake & Regulatory Mapping

**Nothing is drafted in Phase 1.** The work is diagnostic. Produce three
artefacts: an activity-to-licence matrix, a set of resolved classifications,
and a party-role map.

## Step 1 — Identify each regulated activity and its licence basis

Classify what the client is *actually doing* before classifying what the
contract *says*. Isolate each activity and tie it to the specific provision of
the regulator's licensing instrument that authorises it. Typical activities:
e-money issuance, agent-based cash-in/cash-out, QR-code payments, wallet-funded
e-payments. A single deal frequently spans several at once, each with a
different regulatory footprint.

**Output — the activity-to-licence matrix.** Build it at intake:

| Service the deal contemplates | Authorising provision (article / decision) |
| --- | --- |
| _e.g._ Agent cash-in / cash-out | _name the precise article_ |
| _e.g._ QR payments | _name the precise article — see Step 2 if grey_ |
| _e.g._ Wallet e-payments | _name the precise article_ |
| _e.g._ Marketplace integration | _merchant terms — see Step 5_ |

> **PRACTICE NOTE** — Any activity you cannot tie to a provision is either out
> of scope, requires a licence extension, or needs a regulator ruling. **That
> blank cell is your earliest warning of an execution blocker.** Surface it
> now; do not let it reach a clause.

## Step 2 — Resolve classification gates early

Some activities sit in a grey zone. The recurring example: a **QR
transaction** — is it a peer-to-peer transfer between two onboarded wallet
users, or is it **merchant acquiring / payment facilitation / gateway**
activity? The distinction is not academic. It changes the applicable
commission ceiling, the KYC and onboarding obligations, and whether the
existing licence covers the service or a separate authorisation is required.

Resolve the classification **before drafting the pillar**, by one of two
routes:
- **(a)** a written non-objection or no-action position from the regulator; or
- **(b)** a reasoned written legal opinion that the activity falls within the
  licensed perimeter and records the basis for that conclusion.

Treat an unresolved gate as an **execution-blocking condition**, not a
drafting detail to be papered over.

> **RED FLAG** — Do not let commercial momentum push a grey-zone activity into
> the contract on the assumption it will be sorted later. If the QR pillar is
> reclassified as acquiring rather than P2P *after* signature, the commission
> terms may breach the cap and the pillar may be operating outside the licence.
> **Gate it: the pillar does not go live until the classification is confirmed
> in writing.**

## Step 3 — Map the parties' true roles

Pin down, **in substance not just label**, which party is the licensed
financial institution, which is merely an agent / payment acceptor, and which
bears no FI status at all. This single determination governs the entire
allocation of KYC/AML execution, transaction authority, float ownership, audit
rights, and liability. Get it wrong and the agent inadvertently acquires
regulated-entity obligations, or the licensed party silently disclaims duties
it cannot lawfully delegate.

**Output — the party-role map:**

| Party | Status | Core function | Must NOT do |
| --- | --- | --- | --- |
| Licensed PSP | Financial institution | KYC/AML, authorisation, float, reporting | Delegate non-delegable regulatory duties |
| Counterparty / agent | Agent & acceptor only | Cash handling, physical operations | Act as financial intermediary; hold out as an FI |
| Marketplace operator | Merchant | Sell goods/services via the rails | Touch the regulated payment flow |

---

# Phase 2 — Architecture

With the perimeter mapped, choose the contractual structure **before writing
clauses**. Architecture decisions made now determine whether pillars can
launch, pause, and terminate independently, and whether regulatory risk in one
service line can be quarantined from the others.

## Step 4 — Framework plus sub-agreements for multi-pillar deals

When a deal bundles several independent services, **do not draft one
monolithic contract.** Use a **General Framework Agreement** for the common
terms — definitions, compliance obligations, liability allocation, term and
termination, confidentiality, governing law — then attach a **separate,
separately executed sub-agreement for each pillar** (cash-in/cash-out, QR
payments, wallet e-payments, marketplace). The framework binds the
relationship; each sub-agreement operationalises one service.

> **DRAFTING TIP** — Make the framework the single source of truth for shared
> terms and have every sub-agreement **incorporate it by reference with an
> express order-of-precedence clause**: in the event of conflict, the framework
> governs *except where a sub-agreement expressly and specifically derogates
> from it for that pillar*. This stops a later sub-agreement from silently
> overriding a compliance term that must hold across the whole relationship.

> **PRACTICE NOTE** — Independent execution is the commercial payoff. A
> regulator query, a failed condition precedent, or a commercial dispute
> confined to one pillar should not stall or unwind the others. Draft
> termination so each pillar can be suspended or terminated on its own without
> collapsing the framework, and so that **termination of the framework
> cascades to all pillars but not vice versa.**

## Step 5 — Ring-fence the riskiest pillar

Where one pillar carries a materially different risk profile, give it a
standalone agreement and keep it **out of the regulated payment flow**. The
**marketplace** pillar is the usual candidate: it introduces product liability,
delivery and fulfilment disputes, and third-party merchants the licensed party
cannot fully control. Treat the marketplace operator as you would any
third-party merchant — standard merchant terms, KYC, onboarding — rather than
folding it into the agency or wallet structure.

> **RED FLAG** — Folding a marketplace into the payments rails imports
> consumer-goods liability into a regulated payments contract and blurs the
> line the regulator cares about most: **who is performing the payment
> service.** Ring-fence it. Product and delivery disputes belong with the
> marketplace operator; the payment rails should see the marketplace as just
> another merchant.

---

# Cross-Cutting — The Regulatory–Commercial Balance

This sits between architecture and drafting because that is where the
balancing actually gets decided — but the principle runs through every phase.
A fintech lawyer is rarely asked to choose between compliance and commerce.
The real task is to find the structure that satisfies the regulator **at the
lowest friction to the business**, and to know precisely which terms can flex
and which cannot.

## The core tension

Two failure modes bracket every regulated fintech deal:
- **Compliance maximalism** — every conceivable control imposed regardless of
  proportionality — produces a contract so heavy the product never launches or
  the counterparty walks.
- **Commercial maximalism** — speed and frictionless onboarding override the
  licence conditions — produces a contract that closes fast and then breaches,
  exposing the licence itself.

The drafter's value is in refusing both: a document a regulator would accept
**and** a business would actually sign and operate.

> **PRACTICE NOTE** — Reframe the question the business is really asking. When
> a sponsor says "this is too restrictive," they are usually not asking you to
> break a rule; they are asking whether the restriction is genuinely *required*
> or merely conservative drafting. Separate the two out loud. If a control is
> mandated by the licence, say so and stop negotiating it. If it is your own
> prudence, it is on the table — and treating it as negotiable builds the
> credibility you need when you hold firm on what is not.

## Three techniques for reconciling the two

Most apparent conflicts dissolve under one of these, each of which lets the
business move while keeping the licence intact:

- **Phased rollout.** Launch the clean pillars immediately and gate the
  contested ones. The business gets revenue and momentum on what is ready; the
  regulated grey zone activates only once its condition is satisfied. This is
  the commercial payoff of the framework-plus-sub-agreement architecture.
- **Proportionate controls.** Calibrate the obligation to the actual risk and
  to what the rules require — not to the most cautious reading. Do not impose
  bank-grade onboarding on a low-value, fully-traced P2P flow if the instrument
  does not demand it. Over-control is not free; it is friction the business
  correctly resents and that may exceed the regulator's own expectation.
- **Conditions precedent as "yes, but sequenced."** A CP converts a flat
  refusal into a structured timeline: not "you cannot have this feature" but
  "this feature switches on the moment a defined, achievable step is complete."
  It keeps the deal alive and gives the commercial team something concrete to
  chase.

## Pushing back without breaching

The skill is not saying no; it is saying no **in a way that redirects.** Name
the condition, explain the consequence of breaching it in *business* terms
rather than legal ones, and offer the nearest compliant alternative. "We
cannot raise the agent cap because that voids the licence basis; what we *can*
do is prioritise the highest-volume locations within the existing cap" moves
the conversation forward. A flat "no" stops it.

> **DRAFTING TIP** — Frame every non-negotiable as a **business consequence,
> not a rule number.** "This breaches Article X" persuades no one in a
> commercial meeting; "this puts the licence at risk, which stops *every*
> pillar, not just this one" lands. The most effective compliance argument is
> almost always the one expressed as commercial self-interest.

## The negotiable / non-negotiable line — surface it early

| Negotiable (can flex) | Non-negotiable (compliance condition) |
| --- | --- |
| Pricing and commission *within* the cap | The commission cap itself |
| Service levels and SLAs | KYC/AML ownership by the licensed party |
| Exclusivity and territory | Agent caps and mandatory regulator notification |
| Term, renewal, and termination notice | Prohibition on sub-agency without approval |
| Marketing, branding, and rollout sequence | Accuracy of representations and warranties |

> **RED FLAG** — The most dangerous moment is when commercial pressure reframes
> a non-negotiable as a "commercial point" to be split down the middle.
> **Compliance conditions do not have a midpoint.** Splitting the difference on
> an agent cap or a KYC obligation does not produce a moderate position; it
> produces a breach. Hold the line here precisely because you gave ground
> freely on everything that genuinely was negotiable.

---

# Phase 3 — Core Clause Drafting

Now draft. The governing principle across every clause in this phase:
**authority, money, and liability each track control.** Whoever controls a
function bears its obligations and its risk; whoever is barred from a function
must be **expressly** barred in the text.

## Step 6 — Allocate authority asymmetrically and explicitly

The licensed entity must retain **exclusive** authority over the regulated
core: KYC/AML, sanctions screening, transaction authorisation, float
management, regulatory reporting, and audit. The counterparty receives cash
handling and physical operations only. Crucially, **the agent's exclusions
must be stated affirmatively**, not merely implied by the grant to the
licensed party.

Draft an **express prohibitions clause** barring the agent from: financial
intermediation; holding itself out as a financial institution; initiating,
approving, overriding, or manipulating transactions; structuring transactions;
and handling sensitive customer credentials.

> **DRAFTING TIP** — Write a **closed list of agent prohibitions** and a
> **separate closed list of licensed-party reserved powers.** Two explicit
> lists are far harder to misread than a single grant with everything else left
> to inference, and they give you a clean checklist for the regulator and for
> the agent's own compliance team.

## Step 7 — Engineer the money mechanics

Specify the float model in operational detail; vagueness here is where
reconciliation disputes and regulatory findings originate. Address, at minimum:

| Mechanic | Drafting requirement |
| --- | --- |
| Prefunding | Identify the funding party and the segregated, non-commingled account |
| Monitoring | Real-time monitoring with hard per-agent float limits |
| Accounting | Liability on the agent's books; restricted cash on the licensed party's |
| Reconciliation | Daily automated reconciliation of ledger, agent float, and bank accounts |
| Exceptions | Defined exception SLA (e.g. T+1 resolution) |
| Authority | System of record is authoritative; bank records are settlement reference only |

> **PRACTICE NOTE** — The most consequential single line in the money mechanics
> is the one naming the **authoritative transactional record.** When the
> licensed party's system and the bank statement disagree, the contract must
> already say which prevails for what purpose: the **system of record governs
> the transactional truth; bank records govern settlement.** Decide it in the
> text, not in the dispute.

## Step 8 — Build in the regulator's hard caps and obligations

Hard-code the licence conditions as **non-negotiable terms, not commercial
variables.** These typically include: a maximum number of agents per branch
and an aggregate cap across the network; mandatory notification to the
regulator; a prohibition on sub-agency, delegation, or subcontracting without
prior approval; and individual fit-and-proper vetting, training, and
system-authorisation of every responsible person.

> **RED FLAG** — Caps and approval requirements are compliance conditions, not
> points to trade. If a commercial counterpart asks to raise an agent cap or to
> permit subcontracting, the answer is **not a redline; it is a regulator
> question.** Drafting these as ordinary negotiable terms invites a breach that
> voids the licence basis.

## Step 9 — Draft compliance, data, and audit provisions

Cover the supervisory and data obligations expressly. These commonly include:
a statutory data-retention period under local law; annual external-auditor
reports addressing compliance, electronic operations, and AML/CFT at agent
level; footage / CCTV service levels for suspicious transactions;
privacy-aligned counter design so one customer's data is not visible to
others; a standing right to audit; and unannounced mystery-shopping at any
agent location.

> **DRAFTING TIP** — For every compliance obligation, draft **three linked
> elements: the standard, the evidence** the obliged party must produce, **and
> the cadence** on which it must produce it. An audit right without a defined
> evidence package and a reporting interval is unenforceable in practice. Tie
> the data-retention period to the **specific statute** so the clause survives
> a change in internal policy.

## Step 10 — Allocate liability along the operational seam

Liability follows control, splitting at the operational seam between the
parties. Reinforce the allocation with an ongoing agent risk-monitoring
regime — scoring agents periodically on transaction-volume anomalies, cash
discrepancies, and behavioural flags.

| Risk | Owner | Rationale |
| --- | --- | --- |
| Cash & physical handling | Agent | Agent controls the cash and the counter |
| System & regulatory | Licensed PSP | PSP controls the rails and holds the licence |
| Product / delivery / claims | Marketplace operator | Operator controls fulfilment |

---

# Phase 4 — Solving Execution Blockers

By this phase you have a substantively complete draft and a list of open
points. **Triage that list ruthlessly.** Separate the points that are merely
*desirable* from the points that *prevent execution*. Only the latter are
blockers, and each blocker needs a recommended path and a fallback before the
document can move to signature.

## Step 11 — Identify and resolve the deal-killers

Two blockers recur on regulated payments matters:
1. A **security requirement** — e.g. a regulator-mandated bank guarantee —
   the counterparty refuses or cannot post. Workaround: position the
   **prefunded, segregated float as the sole security mechanism**, showing it
   already performs the protective function the guarantee was meant to serve;
   alternatively seek a management or regulator waiver.
2. The **classification gate from Step 2**, which must close by regulator
   non-objection or qualifying legal opinion before the affected pillar can go
   live.

> **PRACTICE NOTE** — Present each blocker to the client as a short **decision
> package**: the obstacle in one sentence, the recommended path, the fallback
> if the path fails, and the consequence of leaving it unresolved. Clients
> decide quickly when options are framed this way; they stall when handed an
> undifferentiated list of open issues.

| Blocker | Recommended path | Fallback |
| --- | --- | --- |
| Bank guarantee refused | Position prefunded float as sole security | Seek management or regulator waiver |
| QR classification open | Obtain regulator non-objection | Qualifying written legal opinion |
| Reconciliation ownership | Assign in sub-agreement with SLA | Escalation and audit-right backstop |

---

# Phase 5 — Iteration & Finalisation

Finalisation is a controlled process, not a single pass. Version deliberately,
verify systematically, and convert any blocker that cannot close before
signature into a condition precedent so the client can sign without absorbing
unmanaged regulatory risk.

## Step 12 — Draft in versioned rounds with tracked changes

Move through successive versions with tracked changes exchanged between the
parties, maintaining an **issues list** that maps every open point to an owner
and a resolution status. Quality improves measurably across rounds when each
version closes a defined set of issues. **Resist declaring the document final
while execution blockers remain open** — a clean-looking draft with a live
blocker is not finished.

> **DRAFTING TIP** — Keep the issues list as a **living annex to the working
> draft**, not as scattered email threads. Each row carries the issue, the
> owner, the current position, and the status. The list is what tells you,
> objectively, whether the document is ready — and it becomes the agenda for
> every negotiation call.

## Step 13 — Run a pre-signature compliance and consistency check

Before execution, run a **structured verification pass:**

| Pre-signature check | Pass condition |
| --- | --- |
| Cross-references | Every internal reference resolves to the right clause |
| Sub-agreement completeness | Each live pillar has its own executed sub-agreement |
| Commission ceiling | All pricing within the regulatory cap |
| Representations | Every rep is backed by existing executed evidence |
| Conditions precedent | Each open blocker is captured as a CP to effectiveness |

> **RED FLAG** — Inaccurate representations are the highest-risk line in any
> deal that will face investor counsel or a regulator. A representation that
> all approvals are in place, or that security has been provided, is a
> **discoverable misstatement** the moment someone asks for the executed copy.
> If the evidence does not exist, **disclose the gap; do not represent around
> it.**

## Step 14 — Close with conditions precedent

Where a blocker cannot be fully resolved before signature, **do not delay the
whole transaction and do not paper over the gap.** Convert the blocker into a
**condition precedent to the effectiveness of the affected pillar.** For
example: the QR pillar does not go live until the regulator's non-objection or
a qualifying legal opinion is obtained. This lets the client sign the framework
and launch the unaffected pillars immediately, while the gated pillar activates
only once its condition is satisfied — so no party assumes unmanaged regulatory
risk.

> **PRACTICE NOTE** — Conditions precedent are the drafter's mechanism for
> **honest sequencing.** They let a deal close on what is ready while
> ring-fencing what is not, and they make the consequence of an unmet condition
> explicit rather than disputed. A well-drafted CP names **the condition, the
> party responsible for satisfying it, the deadline, and what happens to the
> pillar if the deadline passes.**

---

# One-Page Workflow Summary

| Phase | Steps | Output |
| --- | --- | --- |
| 1 — Intake & mapping | 1–3 | Activity-to-licence matrix; resolved classifications; role map |
| 2 — Architecture | 4–5 | Framework + sub-agreement structure; ring-fenced marketplace |
| Cross-cutting — balance | — | Negotiable/non-negotiable line; proportionate, sequenced controls |
| 3 — Core drafting | 6–10 | Authority, money, caps, compliance, liability clauses |
| 4 — Execution blockers | 11 | Decision packages with path + fallback per blocker |
| 5 — Iteration & finalisation | 12–14 | Versioned rounds; pre-signature check; CPs for open blockers |

---

## Output discipline

- When you produce clause text, mark every value the drafter must supply from
  the actual licensing instrument with a clear placeholder (e.g.
  `[COMMISSION CAP — per Art. __]`) rather than inventing a number.
- When you flag a blocker, always frame it as a decision package: obstacle →
  recommended path → fallback → consequence of inaction.
- When you review a draft, return a **triaged issues list** (blocker vs
  desirable), each row mapped to an owner and a status — not prose.
- Close any output the user may share externally with a one-line reminder that
  it is a drafting aid requiring qualified legal and local regulatory review,
  and that licence-specific values must be verified against the governing
  instrument.

---

## Provenance & credit

Methodology authored by **Abbas, Chief Legal Officer, HAQQ Legal AI** — from
the manual *"Drafting & Finalising a Complex Multi-Pillar Fintech Agreement."*
Packaged as a Claude skill by **Stephane Boghossian** (Head of Growth, HAQQ
Legal AI). The full source manual is bundled as
[`REFERENCE.md`](./REFERENCE.md). Licensed **AGPL-3.0**.

ИСХОДНЫЙ ДОКУМЕНТ: skills/nda-review-playbook.md

[RU] Темы: проверка NDA, соглашение о неразглашении, одностороннее NDA, позиция получателя/раскрывающей стороны, редлайны, запасные позиции, журнал замечаний.

---
name: nda-review-playbook
description: Guide to review incoming one-way (unilateral) commercial NDAs in a jurisdiction-agnostic way, from either a Recipient or Discloser perspective (user-selected), producing a clause-by-clause issue log with preferred redlines, fallbacks, rationales, owners, and deadlines.
metadata:
  author: Jamie Tso
  license: AGPL-3.0
  version: 2025.12.30
---

# NDA Review Playbook (Commercial, Jurisdiction-Agnostic)

## Overview

| What this skill does | What it does not do |
|---|---|
| Reviews an NDA and outputs issues, risks, and suggested redlines | Provide jurisdiction-specific legal conclusions |
| Supports *Recipient* or *Discloser* perspectives (user-chosen) | Guarantee enforceability |
| Produces an executive summary + clause-by-clause markup guidance | Replace counsel for complex deals |

**Scope limitation (important):** this playbook supports **one-way (unilateral) commercial NDAs only**.

If the NDA is **mutual**, stop: this playbook is **out of scope** and you should escalate to counsel or use a separate mutual-NDA review approach.

> **Variation callouts** appear throughout:
> - **M&A / Due diligence**
> - **Employment / contractor**
> - **Investor / VC**

## LEGAL DISCLAIMER

**THIS IS NOT LEGAL ADVICE.** This skill is provided for informational and educational purposes only. Laws vary by jurisdiction and individual circumstances, and only a licensed attorney can provide advice tailored to your specific situation. When the NDA is high-risk, high-value, cross-border, or otherwise sensitive, escalate to qualified counsel.

**Remember:** All outputs from this skill must be reviewed by a qualified legal professional before being used for any legal purposes.

---

## Inputs to collect (ask before reviewing)

### A. Role and deal context (required)
- [ ] Are we reviewing as **Recipient** (we receive confidential info) or **Discloser** (we disclose confidential info)?
- [ ] Confirm the NDA is **one-way (unilateral)**. If it is **mutual**, stop: this playbook cannot be used.
- [ ] What is the **purpose** / permitted use (e.g., evaluation of partnership, vendor RFP, diligence)?
- [ ] What are the **parties** (legal names) and any **affiliates** that should be covered?
- [ ] What information types are expected (tech, pricing, customer data, product roadmap, source code)?
- [ ] Desired **timeline**: when do we need to sign?

### B. Practical constraints (recommended)
- [ ] Do we need to share with **affiliates**, advisors, contractors, auditors, or potential acquirers?
- [ ] Will we need to **export** data across borders or store in cloud tools?
- [ ] Will any **personal data** be shared? If yes, are there separate data-processing terms?

> **Jurisdiction-agnostic note:** avoid asserting “this clause is invalid” without the governing law details; focus on *commercial risk*, *operational feasibility*, and *market norms*.

## Deliverables (output format)

### Quick start (default output template)

ALWAYS output:
1) **Executive summary**
2) **Clause-by-clause issue log** (single table)

### A. Executive summary (1 page)
- [ ] Party role (Recipient or Discloser) and confirmation it is one-way (unilateral)
- [ ] Top 5 negotiation points (ranked)
- [ ] “Sign as-is” / “Sign with changes” / “Escalate” recommendation

### B. Clause-by-clause issue log (lawyer-style, thorough)
Use a single table so counsel and business owners can track issues, owners, and deadlines.

| Clause | Issue (1 line) | Risk (H/M/L) | Preferred redline | Fallback | Rationale (1–2 sentences) | Owner | Deadline |
|---|---|---:|---|---|---|---|---|
| Definition | Overbroad; includes unmarked info with no reasonableness |  |  |  |  |  |  |
| Term & survival | Perpetual confidentiality for all information |  |  |  |  |  |  |
| Use restriction | Purpose too broad; blocks internal evaluation |  |  |  |  |  |  |
| Disclosures | Representatives undefined; strict liability |  |  |  |  |  |  |
| Return/destruction | No backup carve-out |  |  |  |  |  |  |
| Remedies | One-way fees + automatic injunction |  |  |  |  |  |  |
| Liability | Indemnity + unlimited consequential damages |  |  |  |  |  |  |
| Boilerplate | Assignment prohibits change of control |  |  |  |  |  |  |

### Example (compact)

**Executive summary (example skeleton):**
- Role: Recipient (one-way NDA)
- Recommendation: Sign with changes
- Top 5 points: definition scope; term/survival; representatives; backup carve-out; remedies/fees

**Issue log (example rows):**

| Clause | Issue (1 line) | Risk (H/M/L) | Preferred redline | Fallback | Rationale (1–2 sentences) | Owner | Deadline |
|---|---|---:|---|---|---|---|---|
| Term & survival | Perpetual confidentiality for all information | H | Add 2–5 year survival; trade secret carve-out only | 5-year survival for all | Reduces indefinite operational burden while protecting truly sensitive info | Legal | Before signature |
| Return/destruction | No backup carve-out | M | Add backup/legal hold exception + continued confidentiality | Allow retention in immutable backups only | Required for standard IT operations; avoids impossible compliance | Security + Legal | Before signature |

## 5-step workflow

### Step 1 — Identify stance (Recipient vs Discloser)
- [ ] Confirm which side we are on for *this specific NDA* (titles are often misleading).
- [ ] Confirm the NDA is **one-way (unilateral)**. If it is mutual, stop (out of scope).

**Quick heuristic:**
- If we are being asked to keep their info secret → we are **Recipient**.
- If we are sharing our sensitive info → we are **Discloser** (if the NDA is mutual, stop: out of scope).

### Step 2 — Triage the NDA (fast risk scan)
Flag these immediately:
- [ ] **Perpetual** confidentiality for *all* information (no trade secret distinction)
- [ ] **Residuals clause** allowing use of “memory” or generalized knowledge
- [ ] **Injunctive relief** + **attorneys’ fees** one-way against Recipient
- [ ] **Indemnity** for breach or broad third-party claims
- [ ] **No carve-outs** for compelled disclosure or prior knowledge
- [ ] **Overbroad definition**: “all information, whether marked or not” with no reasonableness
- [ ] **Affiliate coverage** missing when we must share internally

> If any are present and the NDA matters, proceed with full review and consider escalation.

### Step 3 — Clause-by-clause review (use the reference modules)
Use these references while reviewing:
- [Key clauses](references/KEY_CLAUSES.md)
- [Party obligations](references/PARTY_OBLIGATIONS.md)
- [Duration & scope](references/DURATION_SCOPE.md)
- [Remedies & liability](references/REMEDIES_LIABILITY.md)
- [Standard exceptions](references/STANDARD_EXCEPTIONS.md)

### Step 4 — Draft redlines and negotiation positions
For each issue, produce:
- **Preferred redline** (best risk outcome)
- **Fallback position** (acceptable compromise)
- **Rationale** (1–2 sentences: business + operational feasibility)
- **Owner** (who needs to approve / negotiate: Legal, Sales, Security, Product)
- **Deadline** (by when the counterparty needs the change)

**Negotiation discipline:** do not propose 20 changes. Focus on the 5–10 that materially change risk.

### Step 5 — Finalize the package
- [ ] Ensure consistency (definitions used the same way everywhere)
- [ ] Confirm operational feasibility (can we actually comply?)
- [ ] Re-scan the Step 2 triage list and ensure each flagged item is represented in the issue log
- [ ] Provide a short “what we changed and why” summary

## Perspective-specific checklists

### A. Recipient checklist (incoming NDA — typical case)

| Topic | Red flags | Typical ask |
|---|---|---|
| Definition of Confidential Information | Overbroad; includes independently developed info; no marking/identification standard | Add reasonableness + identification standard; add exclusions |
| Purpose / Permitted Use | Any use restriction beyond evaluation; bans on internal sharing | Tie to stated purpose; allow internal need-to-know |
| Representatives | We are liable for any representative breach without control | Limit to those under written confidentiality; commercially reasonable care |
| Term & survival | Perpetual for everything; unclear start date | Fixed term; longer only for trade secrets |
| Return / destruction | Requires deletion of backups immediately | Add practical backup carve-out |
| Remedies | One-way fees + broad injunction language | Mutuality or reasonableness; clarify equitable relief scope |
| Liability / indemnity | Indemnity; unlimited damages; consequential damages | Cap or exclude categories; remove indemnity |
| Residuals | Allows use of “retained in memory” | Delete or narrow heavily |

> **M&A / Due diligence:** ensure diligence sharing (advisors, financing, affiliates) is permitted and that data room exports/notes are covered.

### B. Discloser checklist (when we are sharing sensitive info)

| Topic | Red flags | Typical ask |
|---|---|---|
| Definition | Too narrow; requires marking only; excludes oral disclosures | Add oral confirmation mechanism; broaden categories reasonably |
| Security standard | Only “reasonable” with no baseline | Add minimum safeguards, or align with internal policy |
| Exclusions | Too broad (e.g., “independently developed” with no proof) | Require written evidence of prior knowledge/independent development |
| Term & survival | Too short | Extend for sensitive categories; trade secret survival |
| Remedies | No equitable relief, no fees | Add equitable relief and/or fees (carefully) |

> **Investor / VC:** watch for standstill, solicitation, and “no contact” provisions—these are not standard in plain NDAs and may need separate agreement.

## Risk rating guide

| Rating | Meaning | Example |
|---:|---|---|
| High | Creates material, uncapped, or operationally impossible risk | Broad indemnity + unlimited damages for any breach |
| Medium | Risk is real but manageable with process controls | Strict notice deadlines for compelled disclosure |
| Low | Mostly cosmetic or market-standard | Minor notice method issues |

## Common pitfalls (issue → risk → fix)

| Issue | Risk | Suggested fix |
|---|---|---|
| “All information is confidential forever” | Operational burden; unfair risk allocation | Add fixed term + trade secret carve-out |
| No compelled disclosure carve-out | Breach if subpoenaed | Add “required by law” disclosure path |
| Return/destruction requires purge of backups | Impossible to comply | Add backup and system integrity exception |
| Recipient indemnifies discloser | Open-ended exposure | Remove indemnity; use direct damages only |
| Residuals clause | Allows de facto use of confidential info | Delete or restrict to non-trade-secret, non-source-code |

## Review prompts (copy/paste)

### A. Minimal prompt (fast)
- Role: Recipient/Discloser
- NDA type: one-way (unilateral)
- Purpose: …
- Please produce (1) exec summary, (2) clause-by-clause issue log table with: Clause, Issue, Risk, Preferred redline, Fallback, Rationale, Owner, Deadline, (3) top 5 negotiation points.

### B. Deep prompt (recommended)
- Add constraints: affiliates, advisors, contractors, cross-border sharing, personal data, cloud tools.
- Ask for: preferred redline + fallback + rationale per issue.

## Ownership & timing defaults (if the user does not specify)

Use these defaults to populate **Owner** and **Deadline** in the issue log:

| Topic | Default owner | Default deadline |
|---|---|---|
| Confidentiality scope/definition, exceptions, term/survival | Legal | Before signature |
| Security standards / audit rights | Security + Legal | Before signature |
| Return/destruction and backups | Security + IT + Legal | Before signature |
| Liability cap / damages / indemnity / fees | Legal + Finance | Before signature |
| Operational constraints (representatives, affiliates, tooling) | Legal + Business owner | Before signature |

ИСХОДНЫЙ ДОКУМЕНТ: skills/sanctions-export-analysis.md

[RU] Темы: санкции, санкционный скрининг, проверка контрагента по спискам (ООН, ЕС, OFAC, OFSI), экспортный контроль, товары двойного назначения, EAR/ITAR/FDPR, риски USD/SWIFT, юрисдикционный маппинг.

---
name: "sanctions-export-analysis"
description: "Sanctions and export control analysis tool for Claude Desktop. Real-time individual screening across 30+ official lists (UN, EU, OFAC, OFSI, French DGT...), sectoral analysis, dual-use goods (EU Reg. 2021/821), US/China extraterritorial regimes (EAR, ITAR, FDPR, ECL), USD/SWIFT risk and jurisdictional mapping across 30+ countries. All results sourced and verified in real time — no memory-based answers. Responds in French, English, German, Spanish, Russian and Chinese. Updated 19 May 2026 (EU 20th package, UK SEUC, Cuba EO). Indicative guidance only — not legal advice."
metadata:
  author: "Gillan Saleh"
  license: "agpl-3.0"
  version: "2026-05-21"
---

# Sanctions Screening & Legal Analysis Skill

> **Last updated: 19 May 2026** — EU 20th package · UK SEUC · Cuba EO 14404 · GL 131E Lukoil

## Scope

This skill covers exclusively the field of **international economic sanctions and export controls**,
in all their dimensions:
- Individual designations (asset freeze, travel ban)
- Sectoral sanctions (energy, finance, technology, transport...)
- Dual-use goods and technologies
- Payment systems (SWIFT, USD, EUR) as sanctions vectors
- Extraterritorial regimes (EAR/ITAR/FDPR US, China ECL, EU no re-export clause)
- Financial institutions' obligations under sanctions

---

---

## ABSOLUTE RULE — Prohibition of hallucinations and invented data

**These rules apply without exception to every response produced by this skill. They take precedence over all other instructions.**

### 1. Absolute prohibition on answering from memory regarding designation lists

Sanctions lists (OFAC SDN, EU FSF, UN list, French DGT, UK FCDO, etc.) are updated daily. A response based on the model's memory is by definition potentially incorrect and legally dangerous.

**Rule**: any statement about the presence or absence of a person or entity on a sanctions list **must be preceded by a real-time web search** on the corresponding official source. If the search is impossible (source unavailable, failed connection), state this explicitly — never fill the gap with an assertion.

### 2. Mandatory source citation

Every piece of information produced under this skill must be accompanied by its source:
- **Name of the list or text** (e.g.: "OFAC SDN List", "EU FSF — Reg. 269/2014", "UN Committee 1988")
- **URL or precise reference** (e.g.: sanctionssearch.ofac.treas.gov, webgate.ec.europa.eu/fsd/fsf)
- **Date of the search** (e.g.: "verified on [date]")

If no source could be consulted for a statement, do not produce it.

### 3. Mandatory alerts — inconclusive results

In the following situations, an explicit alert is mandatory **before any conclusion**:

| Situation | Alerte à produire |
|-----------|------------------|
| Common / ambiguous name (e.g.: Mohamed Ali) | ⚠️ "Very common name — inconclusive result without additional identifiers (DOB, nationality, passport)" |
| Official source inaccessible during search | ⚠️ "Source [name] inaccessible at time of search — result must be verified directly at [URL]" |
| Partial match / low score on OpenSanctions | ⚠️ "Partial match detected — verification on official source [list] mandatory before any conclusion" |
| Variable transliteration (Arabic, Cyrillic, Chinese) | ⚠️ "Variable spelling possible — also search: [variants]" |
| "No match" result without confirmed search | ⚠️ "Absence of match not confirmed by real-time search — do not conclude absence of designation" |

### 4. Prohibition on extrapolating the state of the law without a verified source

Sanctions law evolves very rapidly (new EU packages, OFAC updates, individual designations).

**Rule**: if a rule, an entry into force date, or a designation cannot be confirmed by a source consulted in the session, flag it as **"to be verified — not confirmed in this session"** rather than asserting it as certain.

Never produce a designation date, regulation number, or legal reference without having verified it in the session or in the skill's reference files.

### 5. Mandatory citation format in results

Each result block must explicitly mention:

```
Sources consulted: [list of sources with URLs]
Date of verification: [date]
Limits of this analysis: [missing identifiers / inaccessible sources / partial results]
⚠️ This result is indicative. Verify against official sources before any decision.
```

### 6. Prohibition on compensating uncertainty with a reassuring statement

It is prohibited to produce a reassuring conclusion ("no risk identified", "transaction freely feasible") when the search is incomplete, the name is ambiguous, or a source is inaccessible. In such cases, the conclusion must reflect the actual level of certainty:

- ✅ Result confirmed by official source consulted in the session
- 🟡 Partial result — to be completed by direct verification
- ⚠️ Inconclusive — insufficient identifiers or inaccessible source
- ❌ Cannot conclude — do not produce a conclusion

---

## Step 0 — Language and user profile

### Supported languages — mandatory multilingual rule

Detect the user's language at the very first message and respond **exclusively in that language** throughout the entire conversation — including all result blocks, alerts and recommendations.

**Supported languages:**

| Language | Respond in | Key terminology |
|--------|-------------|-----------------|
| **Français** | French | Reference language of the skill |
| **English** | English | Default fallback for any unsupported language |
| **Deutsch** | Deutsch | Vermögenssperrung · Ausfuhrkontrolle · Güter mit doppeltem Verwendungszweck · Sanktionsliste |
| **Español** | Español | Congelación de activos · Control de exportaciones · Bienes de doble uso · Lista de sanciones |
| **Русский** | Русский | Заморозка активов · Экспортный контроль · Товары двойного назначения · Санкционный список |
| **中文** | 中文（简体） | 资产冻结 · 出口管制 · 两用物项 · 制裁名单 |

**Rules:**
- Never mix languages within a single response
- If the user switches language mid-conversation, switch immediately and maintain the new language
- For any other language: respond in English and note that the tool is optimised for the 6 languages listed above
- Regulatory references (DGT, SBDU, ACPR, CMF) are French/EU obligations — when responding in Russian or Chinese, clarify that these are the applicable French/EU legal frameworks, not the user's domestic law

### User profile
- **Non-expert**: plain language, traffic-light indicators 🔴/🟡/✅, define all acronyms, explicit "what to do next"
- **Legal/compliance professional**: precise regulatory references, concise, full extraterritorial analysis

---

## Step 1 — Request analysis

Identify which modules to activate:

| Signal | Module |
|--------|--------|
| Individual's name | **A** — Individual screening |
| Sector / transaction / country | **B** — Sectoral sanctions + payments |
| Good / technology / software / component | **C** — Dual-use goods |
| "US goods", "US component", "FDPR", "EAR", "ITAR" | **C2** — Extraterritorial regimes US/China |
| Third country involved in transaction | **D** — Jurisdictional risk |

**Combined triggers — examples:**
- "Gillan Saleh + pétrole + Russie" → A + B + D
- "Machine américaine + extraction pétrolière + Irak + paiement USD" → B + C + C2 + D
- "Logiciel de cryptographie + Iran" → B + C + C2 + D
- "Est-ce que X est sanctionné ?" → A seul

Collect before launching:
- **A**: full name + nationality/residence (required); DOB, aliases (useful)
- **B**: sector, nature of transaction, countries
- **C/C2**: description of good/technology, destination, declared use, origin (US? Chinese?)
- **D**: jurisdictions involved, payment currency

---

## MODULE A — Individual screening

### A1 — Universal baseline (always run)
1. **ONU** → `"[nom]" UN Security Council consolidated sanctions list`
2. **UE** → `"[nom]" EU financial sanctions consolidated list`
3. **OpenSanctions** → `"[nom]" site:opensanctions.org` — filet 100+ listes
   - Hit not found in baseline → identify source → targeted official source search
   - Never cite OpenSanctions as authoritative source

### A2 — Geographic tier (based on nationality)

**EU national**: baseline sufficient + French DGT if French entity involved

**Aligned autonomous European countries (NO/IS/LI/CH)**: baseline + SECO (Switzerland). Treat as near-EU.

**EU candidate countries (RS/ME/AL/MK/MD/UA/BA/GE)**: baseline. Declared alignment, less robust legal basis.

**Turkey**: UN only on autonomous sanctions. Different regime from EU/US Russia sanctions.

**UK national / UK link**: UK Sanctions List (FCDO) → `"[name]" site:gov.uk UK sanctions list`
Note: since 28 Jan 2026, single FCDO list — OFSI Consolidated List merged.

**US national / US link**: OFAC SDN + Non-SDN + SSI + GLOMAG → `"[name]" site:ofac.treas.gov`

**Russian / Belarusian**: EU (Reg. 269/2014) + OFAC + UK Sanctions List + SECO as priority.

**Iranian**: UN (snapback 28 Sept 2025, Res. 2231) + OFAC Iran programme + EU (Reg. 267/2012). Watch USD secondary sanctions risk.

**DPRK (North Korea)**: UN (near-total embargo) + OFAC + EU. Watch DPRK workers abroad.

**Syrian**: UN + EU (Reg. 36/2012) + OFAC. Post-Dec 2024: situation evolving — verify current status.

**Gulf / Middle East**: baseline + national list if available (Qatar NCTC / UAE ECON / Saudi Arabia PSS). See `references/regimes.md`.

**African**: baseline generally sufficient. South Africa: + FIC. See `references/regimes.md`.

**CA/AU/JP/SG**: baseline + own list (Global Affairs Canada / DFAT / METI-MOFA / MAS). Lists ≠ EU list.

### A3 — Screening result
```
═══════════════════════════════════════════
SANCTIONS SCREENING — [NAME]     [DATE]
═══════════════════════════════════════════
🔴 MATCH / 🟡 AMBIGUOUS / ✅ NO MATCH / ⚠️ INCONCLUSIVE
Lists checked: [exhaustive]
Match on: [list + reference + grounds if applicable]
⚠️ Indicative. Verify against official sources. Not legal advice.
═══════════════════════════════════════════
```
**If ⚠️ AMBIGUOUS NAME**: request DOB, nationality, passport number, aliases. Minimum 2 concordant identifiers.

---

## MODULE B — Sectoral sanctions and payment systems

### B1 — Sectoral sanctions by regime

**Russie (UE Reg. 833/2014 + 20 paquets successifs — 20ème paquet : Reg. UE 2026/506, 2026/511, 2026/509 du 23 avr. 2026) :**
- Energy: ban on purchase/import of Russian crude oil and refined petroleum products; restrictions on gas, coal
- Finance: ban on access to EU capital markets for designated banks; restrictions on deposits, loans
- Transport: ban on EU airspace overflight, access to ports and airports
- Technology: ban on export of semiconductors, advanced electronics, dual-use goods (Russia removed from EU general authorisations EU001-EU008 since Reg. 2022/699)
- Luxury: ban on export of luxury goods >€300/item
- Services: ban on legal advisory, accounting, PR, cloud, IT consulting to Russian entities
- Gold, steel, wood, chemicals, paper: import restrictions
- Oil price cap G7 : plafonnement 60$/baril pétrole transporté par opérateurs G7
- **Russian LNG embargo (19th package)**: effective 25 April 2026 (short-term contracts concluded before 17 June 2025) / 1 January 2027 (long-term contracts >1 year)
- **Extension of transaction ban to Mir and SBP** (Russian fast payment system) since 25 January 2026 (19th package)
- **Russian crypto-assets ban**: stablecoin A7A5 prohibited since 25 November 2025; extension of transaction ban to crypto-asset and payment service providers (Annex XLV)
- **Commercial space-based services** (Earth observation, satellite navigation): prohibited to Russia and Belarus since the 19th package
- **Désignation OFAC Rosneft et Lukoil** (22 oct. 2025) : les deux plus grandes compagnies pétrolières russes désormais sur la SDN List sous EO 14024 — toutes transactions US-nexus interdites ; secondaires sanctions risk pour entités non-américaines ; wind-down GL 131E prolongée jusqu'au 30 mai 2026 (OFAC, 29 avr. 2026) — pour cession Lukoil International GmbH uniquement ; aucun transfert vers la Russie autorisé
- **20th EU package (23 Apr. 2026) — key new measures:**
  - **Transaction ban extended to 20 additional Russian banks** (effective 14 May 2026) — total now 70 banks; + 4 banks in Kyrgyzstan, Laos and Azerbaijan for circumvention facilitation
  - **Full sectoral ban on Russian crypto-asset service providers and decentralised platforms** (effective 24 May 2026) — categorical ban, no individual listing required; digital rouble and RUBx stablecoin prohibited
  - **Managed security services** (cybersecurity risk management, penetration testing, security audits) prohibited to Russian government and Russia-established entities (effective 25 May 2026)
  - **Kyrgyzstan**: first-ever activation of EU anti-circumvention tool (Art. 12f) — specific trade restrictions extended due to systematic re-export risk to Russia (imports of controlled EU goods +800%, re-exports to Russia +1,200%)
  - **LNG terminal services** ban for Russian entities; prohibition on maintenance services for Russian LNG tankers and icebreakers
  - **Shadow fleet**: 46 additional vessels listed (total: 632); Murmansk and Tuapse ports sanctioned; Karimun Oil Terminal (Indonesia) — first third-country port sanctioned
  - **Payment agents** (non-financial intermediaries offering netting/set-off/settlement services to route Russian transactions around sanctions) newly restricted — entities listed in Annex XLV Part D (Arneis, Asia Import Group, GPAgent, Platejka), effective 14 May 2026
  - **Future maritime services ban** on Russian oil/petroleum: legal framework established, entry into force to be decided by the Council in coordination with G7
  - **Protections for EU operators**: new anti-suit injunction mechanism (Art. 11ca Reg. 833/2014) allowing EU companies to seek court orders against abusive Russian proceedings
  - **Export bans** (goods >€365M: chemicals, rubber, steel, tools, industrial tractors); **import bans** (metals, chemicals, minerals >€530M)
- "No re-export to Russia" clause (Art. 12g Reg. 833/2014, 12th package Dec 2023, effective March 2024): EU exporters must insert a clause prohibiting re-export to Russia in all contracts with third-country partners — **unless the third country is in Annex VIII**: US, JP, UK, CA, AU, NZ, NO, CH, LI, IS, South Korea

**Iran (UN + EU Reg. 267/2012 + OFAC):**
- Oil/gas: EU embargo; US near-total prohibitions
- Finance: restrictions on transactions with designated Iranian banks
- Nuclear/missiles/IRGC: broad UN + EU + OFAC prohibitions
- **Snapback ONU (28 sept. 2025)** : réimposition sanctions ONU suite activation mécanisme Res. 2231 par E3 le 28 août 2025

**DPRK (UN near-total embargo):**
- Coal, steel, iron, lead, seafood: UN import bans
- Oil: export cap to DPRK
- DPRK workers abroad: employment ban (UNSC Res. 2397)

**Syrie** : sanctions économiques larges **levées** (UE 28 mai 2025, US 1er juillet 2025, UK avril 2025). Restent uniquement : sanctions contre membres régime Assad, armes, chimique, affiliés ISIS/Al-Qaeda — vérifier listes individuelles. Voir `references/regimes.md` section 2.4.

**Myanmar / Belarus / Venezuela :** voir `references/regimes.md`

### B2 — Payment systems as sanctions vectors

**SWIFT — statut juridique et exclusions :**
SWIFT is incorporated under Belgian law → directly subject to EU law → obligation to disconnect entities designated by EU regulation.

Timeline of Russian exclusions:
- **12 mars 2022** (Reg. 2022/345) : 7 banques — VTB, Bank Otkritie, Novikombank, Promsvyazbank, Rossiya Bank, Sovcombank, VEB
- **May 2022**: + Sberbank, Credit Bank of Moscow, Russian Agricultural Bank
- **2022–2025** : extension progressive à d'autres banques russes et biélorusses
- **July 2025** (Reg. EU 2025/1494): **major development** — conversion to full transaction ban. Any EU operator is prohibited from any direct or indirect transaction with the 50+ designated Russian banks, 4 Belarusian banks, 5 third-country financial operators.
- **June 2024**: prohibition on use of SPFS (Russian alternative financial messaging system) by EU operators

**USD risk (OFAC / correspondent banking):**
Any USD payment transiting through the US banking system is subject to OFAC, regardless of the parties' nationality. US correspondent banks screen every transaction. If any element of the chain touches a designated person or entity → automatic blocking.

**Alternatives to SWIFT/USD payments toward Russia:**
- SPFS (Russian): prohibited for EU operators since June 2024
- CIPS (Chinese — Cross-Border Interbank Payment System): not prohibited under EU law but risk of exposure to US secondary sanctions for entities with US links

**EUR payments toward sanctioned areas:**
- EUR payments transiting through EU banks: subject to EU sanctions regime
- Ban on provision of euro banknotes to Russia (Reg. 2022/345) with limited exceptions (personal use by travellers, diplomatic missions)
- Immobilisation of Russian Central Bank reserves held in the EU (since March 2022) — extraordinary revenues used to support Ukraine since May 2024

### B3 — Financial institutions' obligations under sanctions

**France / EU — result obligation (not best-efforts):**
Asset freezing is a **result obligation** — unlike AML/CFT which is risk-based. The financial institution cannot invoke a proportionate approach to justify a failure. If a designated person holds funds: immediate freeze, without discretionary assessment (principle consistently upheld by the ACPR sanctions commission).

Key regulatory obligations (France):
- **Decree of 6 January 2021**: mandatory internal controls for asset freezing
- **Joint DGT/ACPR guidelines** on implementation of asset freeze measures (updated 2024)
- **EBA Guidelines 2024/14 and 2024/15** (14 Nov 2024): internal policies, procedures and controls for restrictive measures
- **EU Directive 2024/1226**: EU harmonisation of criminal offences for sanctions violations
- **AMLA** (EU Regulation 2024/1620): new EU AML/CFT Authority — first supervisory reviews of ~40 financial institutions from mid-2025
- **EU Directive 2024/1640**: to be transposed by 10 July 2027 at the latest
- ACPR Decision 2024-02 (19 June 2025): Banque Delubac sanctioned for asset freeze failures
- ACPR sanctions 2024: ~€5 million in fines — main findings: internal control failures, insufficient transaction monitoring, gaps in detection of designated persons

**UK (OFSI):**
- **Strict liability** regime since SAMLA 2018 — civil penalties even without knowledge of the violation
- £160,000 fine on Bank of Scotland (Lloyds subsidiary) in January 2026 for Russia sanctions breach
- Since 28 Jan 2026: single FCDO list — any contractual reference to the OFSI Consolidated List must be updated

**US (OFAC):**
- No general legal obligation to establish a compliance programme — but the **OFAC Compliance Framework (2019)** creates strong normative pressure
- Robust compliance programme = significant mitigating factor; absence = aggravating factor
- In practice: all US banks and their correspondents have structured compliance programmes

**Japan (FEFTA):**
- Since **April 2024**: legal obligation for financial institutions to establish internal systems for compliance with asset freeze measures
- Since **December 2024**: mandatory prior reporting for transfers of key technologies (15 items: MLCC, carbon fibres, semiconductors...)
- Since **October 2025**: revised catch-all export controls — high-risk dual-use items classified as "core items"

**China:**
- No obligation to comply with foreign sanctions
- Anti-sanctions Law 2021 + Blocking Statute 2021 may create **inverse obligations** for entities in China — duty not to comply with foreign sanctions targeting Chinese entities

### B4 — Sectoral / payments result
```
═══════════════════════════════════════════
SECTORAL ANALYSIS — [SECTOR/PAYMENT] / [COUNTRY]
═══════════════════════════════════════════
🔴 RESTRICTIONS / ✅ PAS DE RESTRICTION IDENTIFIÉE
Applicable regime: [regulation/resolution]
Nature: [total ban / licence required / cap / SWIFT restriction]
Who is bound: [EU entities / US persons / financial institutions]
Derogations: [yes/no — which ones]
USD risk: [yes/no — OFAC correspondent banking]
SWIFT risk: [designated bank? transaction ban since July 2025?]
═══════════════════════════════════════════
```

---

## MODULE C — Dual-use goods — EU regime

### C1 — EU legal basis
- **Regulation (EU) 2021/821** of 20 May 2021 (recast) — in force since 9 Sept 2021, replaces Reg. 428/2009
- **Reg. délégué (UE) 2022/699** : Russie retirée des autorisations générales EU001-EU008
- **France**: SBDU (Service des Biens à Double Usage) — DGE, Ministry of the Economy — EGIDE platform
- Annual update of Annex I via Commission delegated regulations

### C2 — The 10 dual-use categories (Annex I Reg. 2021/821)

Nomenclature structure: `[Category][Type][Regime][Number]` e.g. `3A225`
- **Type**: A=equipment/components · B=test/production equipment · C=materials · D=software · E=technology

| Cat. | Intitulé | Exemples de codes |
|------|----------|------------------|
| **0** | Nuclear | `0A001` (reactors), `0B001` (enrichment equipment), `0C001` (fissile materials) |
| **1** | Special materials | `1C010` (composite fibres), `1C011` (metals/alloys) |
| **2** | Materials processing | `2B001` (CNC machine tools), `2B004` (high-temperature furnaces) |
| **3** | Electronics | `3A001` (electronic components), `3A225` (frequency converters), `3E001` (semicond. tech.) |
| **4** | Computers | `4A001` (high-performance computing), `4D001` (software) |
| **5** | Telecom & info security | `5A002` (encryption), `5D002` (cryptographic software), `5E002` (encryption tech.) |
| **6** | Sensors and lasers | `6A002` (optical detectors), `6A008` (radars), `6C005` (lasers) |
| **7** | Navigation and avionics | `7A003` (gyroscopes), `7A005` (GPS), `7E004` (aerospace tech.) |
| **8** | Marine | `8A001` (submersibles), `8A002` (naval equipment) |
| **9** | Aerospace and propulsion | `9A004` (space launchers), `9A012` (UAVs), `9C110` (propellants) |

> **Important**: no automatic direct link between dual-use code and customs tariff code (CN/HS). An annual CN–dual-use correlation table is published by the EU (EUR-Lex).

### C3 — International control regimes (basis of the dual-use list)

| Régime | Objet | Membres |
|--------|-------|---------|
| **Wassenaar Arrangement** (1996) | Conventional arms + dual-use | 42 states |
| **Australia Group** | Chemical and biological precursors | 43 states |
| **NSG** (Nuclear Suppliers Group) | Nuclear materials and technology | 48 states |
| **MTCR** | Missile technology and delivery systems | 35 states |

### C4 — Types of authorisation (EU/France)

| Type | Référence | Conditions |
|------|-----------|------------|
| EU General Export Authorisations | EU001–EU008 | Approved destinations — **Russia EXCLUDED (Reg. 2022/699)** |
| Individual authorisation | SBDU/EGIDE | 1 exporter, 1 good, 1 recipient — max. 2 years |
| Global authorisation | SBDU/EGIDE | 1 exporter, multiple operations — max. 2 years |
| National general authorisation | SBDU | Complementary to EU authorisations |

### C5 — Dual-use result
```
═══════════════════════════════════════════
DUAL-USE ANALYSIS — [GOOD] / [DESTINATION]
═══════════════════════════════════════════
🔴 LICENCE REQUISE / 🟡 À VÉRIFIER / ✅ PAS DE CONTRÔLE BDU
Potential classification: [dual-use code]
Category: [0-9 + description]
Source regime: [Wassenaar / NSG / Australia Group / MTCR]
Authorisation required: [general / individual / global]
French authority: SBDU — EGIDE platform
Legal basis: Reg. (EU) 2021/821, Annex I
═══════════════════════════════════════════
```

---

## MODULE C2 — Extraterritorial export control regimes

### C2.1 — US EAR/BIS

**Legal basis**: Export Administration Regulations (EAR) — 15 CFR Parts 730-774 — Bureau of Industry and Security (BIS), US Department of Commerce.

**Commerce Control List (CCL)**: US equivalent of EU Annex I — coded in ECCN (Export Control Classification Numbers), format `3A991`, `5E002`, etc.

**De minimis rule**: if US EAR-controlled components represent more than **25%** of the final product's value (10% for strictly embargoed destinations: Iran, DPRK, Cuba, Syria), the entire product is subject to the EAR even if manufactured outside the US.

**Foreign Direct Product Rule (FDPR)** — 15 CFR § 734.9: foreign-made products are subject to the EAR if they are the "direct product" of specified US-origin technology or software, or produced by a plant itself made from US technology. **Massive extraterritorial reach.**

**Russia/Belarus FDP Rule (since Feb 2022)**: extension of the FDPR — any item produced anywhere in the world from US tooling or technology is subject to the EAR for export to Russia/Belarus.

**BIS lists distinct from OFAC SDN List:**
- **Entity List**: entities to which any export of EAR-controlled items requires a licence — often reviewed under denial policy. "Footnote 3" = Russia-MEU FDP rule applies automatically
- **Denied Persons List**: total export prohibition to these persons
- **Unverified List**: entities whose end-use cannot be verified → enhanced due diligence required
- **Military End-User (MEU) List**: Russian and Chinese military entities — enhanced restrictions

**BIS Affiliates Rule (BIS 50% Rule) — status as of 19 May 2026**: BIS adopted on 29 September 2025 a rule extending Entity List restrictions to subsidiaries owned 50%+. This rule was **suspended for one year** as of 10 November 2025 under US-China trade negotiations (Trump-Xi Busan agreement). The rule is scheduled for reactivation on 10 November 2026 unless extended. During suspension: not operative — but BIS recommends maintaining capacity to analyse ownership chains.

**End-use controls**: even if an item is not on the CCL or if the destination is not embargoed, a BIS licence may be required if the final use is military, WMD-related, or for certain designated end-users.

**BIS Affiliates Rule (BIS 50% Rule) — suspended:**
- Adopted 29 September 2025: extension of Entity List restrictions to subsidiaries owned 50%+ (analogous to OFAC 50% rule but for export controls)
- **Suspended for one year** since 10 November 2025 (Trump-Xi agreement — in exchange for China suspending rare earth export controls)
- **Reactivation scheduled 10 November 2026** unless extended — maintain capacity to analyse ownership chains in anticipation
- During suspension: the BIS 50% Rule is **not operative** — but Entity List obligations for named entities remain in full force

**AI semiconductors / China — revised policy (January 2026):**
- Biden AI Diffusion Rule (January 2025) **rescinded** by the Trump administration
- New BIS policy effective **15 January 2026**: AI chips below certain thresholds (TPP < 21,000; DRAM bandwidth < 6,500 GB/s — H200/MI325X level) can now be evaluated **case by case** for export to China, instead of the previous systematic denial
- Conditions: proof that the export does not reduce production capacity available to US customers; KYC procedures on the Chinese buyer; independent third-party testing on US territory

**EU "no re-export to Russia" clause (Art. 12g Reg. 833/2014)**: obligation for all EU exporters to insert in contracts with third-country partners a clause prohibiting re-export to Russia — **unless the third country is in Annex VIII** (US, JP, UK, CA, AU, NZ, NO, CH, LI, IS, South Korea). Effective since March 2024. Declaration to national competent authorities required for contracts with foreign public authorities or international organisations.

### C2.2 — ITAR

**Legal basis**: 22 CFR Parts 120-130 — Directorate of Defense Trade Controls (DDTC), US Department of State.

**Distinct from EAR**: more restrictive, covers items on the **US Munitions List (USML)** — 21 categories covering weapons, ammunition, military aircraft, military electronics, missiles, chemical/biological weapons, etc.

**If a product component falls under ITAR**: no EAR licence suffices — this is a separate regime requiring a DDTC licence. Extraterritorial reach: any transfer of ITAR articles or technical data to a foreign national (including on US territory) is subject to ITAR.

**"Once ITAR, always ITAR" rule**: a product incorporating an ITAR component remains ITAR-controlled even if the component represents a tiny fraction of the final product.

**For French/EU entities**: if the US machine contains military or potentially military-use components, ITAR may apply in addition to or instead of the EAR → specialist legal advice essential.

### C2.3 — China Export Control Law (ECL)

**Base légale** : Loi sur le contrôle des exportations (Export Control Law — ECL) — entrée en vigueur le 1er décembre 2020. Complétée par le Règlement sur le contrôle des exportations de biens à double usage (2024).

**Extraterritorial reach** (Article 44 ECL + Article 49 Regulations 2024): foreign entities transferring products outside China that contain specific Chinese dual-use components may be subject to the 2024 Regulations. **Chinese equivalent of the US FDPR** — still developing, selective application.

**Terres rares et semiconducteurs (2025)** : mesures extraterritoriales spécifiques introduites en 2025 sur les terres rares, batteries lithium et matériaux superhard — avec une règle des 50% propre à la Chine pour les entités sur sa Control List.

**Unreliable Entity List (UEL)**: Chinese list of foreign entities having taken discriminatory measures against Chinese entities — may result in market access restrictions.

**Parallel anti-sanctions regime**:
- Anti-Foreign Sanctions Law 2021 (反外国制裁法): prohibits entities in China from complying with foreign unilateral sanctions targeting Chinese nationals/entities; right to claim damages
- Blocking Statute 2021: against extraterritorial application of foreign laws
- Law on Foreign Relations 2023: codifies and strengthens these mechanisms

**Practical note**: China's Control List and UEL are not publicly accessible in the same way as the OFAC SDN List or EU list — greater opacity.

### C2.4 — Other national export control regimes

**UK**: Export Control Order 2008 + UK Strategic Export Controls Lists — post-Brexit alignment with Wassenaar/NSG/MTCR/Australia Group; own regime distinct from the EU since 31 Dec 2020. **Sanctions End-Use Controls (SEUC — effective 13 May 2026)**: complementary mechanism to existing export controls — applicable to goods not on strategic lists but presenting diversion risk to a sanctioned destination. Triggered by written notification from OTSI to the exporter. Check systematically for any UK export toward third countries with re-export risk (Turkey, UAE, Kyrgyzstan, China, India...).

**Canada**: Export and Import Permits Act (EIPA) + Export Control List — Wassenaar alignment + specific Russia/Belarus measures post-2022.

**Australia**: Defence Export Controls (DEC) + Defence and Strategic Goods List (DSGL) — Wassenaar/NSG/MTCR/Australia Group alignment.

**Japan (FEFTA)**: no own FDPR; no secondary sanctions. BIS US controls apply in practice for Japanese exporters of products containing EAR items. Catch-all revised October 2025 with "core items" classification. Prior reporting for key technologies since December 2024.

**Russia**: no extraterritorial export control regime comparable to EAR/ECL. However, counter-measures targeting "unfriendly states":
- Decrees 95 and 254 (March/May 2022): restrictions on dividend transfers — payments only in roubles on type "C" accounts
- Decree 618 (Sept 2022): government approval required for any transaction by a national of an "unfriendly state" on participations in Russian companies
- Decree 302 (April 2023): authorisation to seize Russian assets held by nationals of "unfriendly states" (Rosimushchestvo)

### C2.5 — Analysis questions for Module C2

When a US-origin good or machine is mentioned:
1. Is the good on the CCL (ECCN)? → check BIS
2. Does the final product contain US EAR-controlled components exceeding 25% (or 10% for embargoed destinations)? → de minimis rule
3. Was the product manufactured using US tools or technology? → potential FDPR
4. Do any components fall under the USML (ITAR)? → separate, stricter regime
5. Is the destination subject to an extended FDP Rule (Russia/Belarus)?
6. Does the transaction involve an entity on the BIS Entity List, Denied Persons List or MEU List?
7. Does the good contain Chinese dual-use components? → potential ECL 2024 Art. 49
8. Is payment in USD? → OFAC risk via correspondent banking

### C2.6 — Module C2 result
```
═══════════════════════════════════════════════════════════
EXTRATERRITORIAL REGIMES ANALYSIS — [GOOD] / [ORIGIN] / [DESTINATION]
═══════════════════════════════════════════════════════════
EAR/BIS (US) :
  🔴 BIS LICENCE REQUIRED / 🟡 TO VERIFY / ✅ NO EAR CONTROL
  Potential ECCN: [code if identifiable]
  De minimis rule: [applicable? threshold?]
  FDPR : [applicable ?]
  BIS lists: [Entity List / Denied Persons / MEU / Unverified]

ITAR (US) :
  🔴 APPLICABLE — USML CATEGORY [X] / ✅ NOT ON USML
  If applicable: DDTC licence mandatory — EAR licence insufficient

ECL CHINE :
  🟡 TO ASSESS if Chinese components / ✅ NO CHINESE COMPONENT IDENTIFIED

RISQUE USD :
  🔴 USD PAYMENT → OFAC SCREENING MANDATORY / ✅ NO USD PAYMENT

CLAUSE NO RE-EXPORT (UE Art. 12g) :
  🔴 APPLICABLE — third country not in Annex VIII / ✅ THIRD COUNTRY IN ANNEX VIII
═══════════════════════════════════════════════════════════
```

---

## MODULE D — Jurisdictional risk management

> **Principle**: States exercise full sovereignty over their sanctions policy. A regime different from the EU/France regime implies no judgment on the legitimacy of that State's policy. The analysis covers only the obligations of the user under their own legal regime.

### D1 — Geographic mapping (summary — read `references/regimes.md` for detail)

**EU 27**: CFSP regulations directly applicable — automatic obligation.

**Aligned autonomous (NO/IS/LI)**: near-EU. Switzerland (SECO): strong EU convergence, separate verification.

**EU candidates**: declared alignment, less robust legal basis — residual risk per transaction.

**Turkey**: UN only; different regime on Russia.

**UK**: strong G7 alignment; distinct FCDO list; OFSI strict liability since Jan 2026. **New — SEUC (Sanctions End-Use Controls, effective 13 May 2026)**: new licensing requirement for exports toward non-sanctioned third countries where OTSI has notified diversion risk — Sanctions (EU Exit) (Miscellaneous Amendments) Regulations 2026 (S.I. 2026/443).

**US**: largest + most extraterritorial regime (secondary sanctions, USD). EU Blocking Statute Reg. 2018/1100 applicable in principle for Cuba/Iran. **New — EO 14404 Cuba (1 May 2026)**: new Executive Order extending US sanctions on Cuba (energy, defence, metals, mining, financial services sectors) with threat of secondary sanctions on foreign financial institutions dealing with blocked Cuban entities — increased risk for non-US entities.

**CA/AU/JP**: strong G7 alignment; distinct lists — separate systematic verification.

**Singapore**: UN + terrorism; indirect OFAC exposure via USD.

**UAE**: UN + terrorism (ECON); different regime on Russia; exposed to OFAC designations Iran/Russia.

**Qatar**: NCTC terrorism list (best structured in the region). No broad autonomous sanctions.

**Saudi Arabia**: formal UN framework (automatic freeze upon UNSC 1267 designation); PSS list poorly structured; different regime on Western unilateral sanctions.

**South Africa**: only sub-Saharan autonomous public list (FIC).

**Rest of Africa**: no public autonomous lists; variable UN obligation; individual designations via UN/EU/OFAC only. AU/ECOWAS: regional regimes under construction.

**China**: selective UN (abstentions on Russia 2022); anti-sanctions law 2021; inverted regime for entities in China.

**India**: UN; different regime on Russia; India-Russia bilateral trade rising since 2022.

**Russia**: own counter-sanctions targeting "unfriendly states" — inverted context for French/EU entities operating in Russia.

### D2 — Residual risk questions

Even if Module A = ✅ and Module B = ✅:
1. USD payment? → OFAC risk via correspondent banking even without direct US link
2. Entity owned 50%+ by a designated person? → OFAC 50% rule + EU indirect control rule
3. Intermediaries in jurisdictions with different regimes? → analyze the full transaction chain
4. Sector itself under sanctions even if counterparty not individually designated?
5. Does the financial institution involved fall under the July 2025 transaction ban (70 Russian banks as of May 2026)?
6. Bien contient-il des composants US ou chinois déclenchant EAR/ECL ?

---

## Step 4 — Cross-jurisdictional legal qualification and synthesis

Read `references/qualification-juridique.md` for the full grid.

```
═══════════════════════════════════════════════════════════
SYNTHESIS — COMPLETE TRANSACTION ANALYSIS
═══════════════════════════════════════════════════════════
PERSON            : [Module A result]
TRANSACTION       : [Module B result — sectoral + SWIFT/USD]
GOOD/TECH EU      : [Module C result]
EXTRAT. REGIMES   : [Module C2 result — EAR/ITAR/FDPR/ECL]
JURISDICTION      : [Module D result]

CONCLUSION :
⛔ TRANSACTION NOT FEASIBLE AS STRUCTURED
⚠️ FEASIBLE UNDER CONDITIONS: [specify — BIS/SBDU licence / DGT authorisation...]
✅ NO RESTRICTION IDENTIFIED

IMMEDIATE OBLIGATIONS: [if applicable]
AUTHORITIES TO CONTACT: [DGT / SBDU / TRACFIN / ACPR / BIS / DDTC]
═══════════════════════════════════════════════════════════
```

---

## Step 5 — Practical guidance

**Non-expert**: traffic-light indicator on each dimension + "what this means for you" in plain language + explicit "what to do next" (contact SBDU, specialist lawyer, DGT...). Never leave without a clear next step.

**Expert (legal/compliance)**:
- Precise regulatory references (regulation numbers, articles, CFR)
- US extraterritoriality analysis (secondary sanctions, FDPR, EU Blocking Statute Reg. 2018/1100)
- China ECL analysis if Chinese components involved
- Residual jurisdictional risk (USD correspondent banking, transaction chain)
- Reporting obligations with legal basis (CMF L. 562-1 et seq., penalties L. 562-5)
- ACPR/AMF if financial sector; SBDU if dual-use; DDTC if ITAR

---

## MCP Tools — Automatic integration

When MCP tools are available in the session, use them **systematically and as priority** over general web search. MCPs provide access to official consolidated texts — more reliable and precise than web search.

### OpenLegi (Légifrance) — use if available

Use OpenLegi automatically for any French law verification within this skill:

**Mandatory use cases:**
- Verify the current consolidated version of CMF articles on asset freezing: **L. 562-1 to L. 562-10, R. 562-1 et seq.**
- Search for autonomous national sanctions decrees published in the JORF (Prime Minister decrees under CMF art. L. 562-2)
- Verify decrees applicable to financial institutions for asset freezing (e.g. Decree of 6 January 2021)
- Consult ACPR sanctions commission case law on asset freezing
- Verify any French legislative or regulatory reference cited in the analysis

**Typical OpenLegi queries:**
- `CMF L. 562-1` → consolidated text of the article
- `gel des avoirs décret [year]` → national sanctions decrees JORF
- `arrêté 6 janvier 2021 gel avoirs` → text applicable to financial institutions

**If OpenLegi is not available**: use `web_fetch` on legifrance.gouv.fr targeting the relevant article URL.

### EUR-Lex — via web_fetch (no dedicated MCP)

Il n'existe pas de MCP EUR-Lex natif — utiliser `web_fetch` directement sur EUR-Lex :

**Mandatory use cases:**
- Verify the consolidated version of any cited EU regulation (e.g. Reg. 833/2014 and its 20+ amendments)
- Consult Annex I of Reg. (EU) 2021/821 (dual-use list) in its current version
- Verify Annex VIII of Reg. 833/2014 (no re-export clause exempt countries)
- Verify Annex VII of Reg. 833/2014 (goods subject to the no re-export clause)
- Confirm the entry into force date of a sanctions package

**Direct EUR-Lex URLs — web_fetch:**
- Reg. 833/2014 consolidé : `https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02014R0833-20250224`
- Reg. 269/2014 consolidé : `https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02014R0269-20250224`
- Reg. 2021/821 consolidé (BDU) : `https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:02021R0821-20241108`
- Liste consolidée sanctions financières UE (FSF) : `https://webgate.ec.europa.eu/fsd/fsf`

**Rule**: always use the most recent consolidated version — never cite a base regulation without checking its successive amendments via EUR-Lex.

### Tool prioritisation

| Task | Priority tool | Fallback |
|-------|------------------|---------|
| French CMF texts / JORF / decrees | **OpenLegi MCP** | web_fetch legifrance.gouv.fr |
| Consolidated EU regulations | web_fetch EUR-Lex (CELEX) | web_search + verification |
| Individual designation lists | web_search on official sources | OpenSanctions |
| ACPR case law | **OpenLegi MCP** | web_search site:acpr.banque-france.fr |
| BIS Entity List / OFAC SDN | web_search site:bis.doc.gov / site:ofac.treas.gov | opensanctions.org |

---

## Disclaimer

**EN**: *Indicative legal guidance only. Last updated: 19 May 2026 (EU 20th sanctions package, UK SEUC, Cuba EO 14404). Results must be verified against official sources before any decision. Does not constitute legal advice. When in doubt: specialist in sanctions and export controls / DGT (asset freeze, France) / SBDU (dual-use goods, France) / BIS (EAR) / DDTC (ITAR).*

**EN** : *Indicative legal guidance only. Verify against official sources before any decision. Not legal advice. When in doubt: sanctions and export control specialist / DGT (asset freeze) / SBDU (dual-use) / BIS (EAR) / DDTC (ITAR).*

---

## Reference files

- `references/sources-officielles.md` — Official URLs + search strategies by jurisdiction
- `references/regimes.md` — Complete regime cartography by zone + jurisdictional risk matrix
- `references/qualification-juridique.md` — Cross-qualification grid + reporting obligations + criminal penalties
ИСХОДНЫЙ ДОКУМЕНТ: skills/screening-alert-adjudication.md

[RU] Темы: разбор срабатывания скрининга, санкционный/PEP/adverse-media хит, ложное/истинное срабатывание, эскалация, снижение false positive, проверка совпадения имени по списку.

---
name: "screening-alert-adjudication"
description: "Adjudicates whether a hit generated by sanctions, PEP, or adverse-media screening is a true positive, false positive, or requires human escalation. Use whenever a user presents a screening alert, a name match against a watchlist (OFAC SDN, EU consolidated list, UK OFSI, UN list, PEP list, adverse media hit, etc.), or asks to clear a screening hit / reduce false positives / determine whether a flagged name is actually the listed party. Use even when the user describes the task casually — \"is this person actually on the sanctions list\", \"did we get a real match\", \"clear this alert\", \"I have a hit on X\" — these are all screening-adjudication tasks. Produces a deterministic determination with full audit trail (structured JSON + human-readable narrative). Designed for use by compliance analysts and screening systems."
metadata:
  author: "Amir Fadavi"
  license: "mit"
  version: "2026-05-19"
---

# Screening Alert Adjudication

This skill adjudicates a single screening hit — a name that an upstream screening system flagged as a possible match against a sanctions list, PEP list, adverse-media source, or similar watchlist — and reaches one of three conclusions:

- **True positive (TP)** — the screened party is the listed party
- **False positive (FP)** — the screened party is not the listed party
- **Escalate** — evidence is insufficient to deterministically conclude either way; hand off to a human analyst with the full evidence record

## Why this skill exists

Screening systems generate enormous volumes of low-quality alerts. Analysts spend their time clearing alerts that should never have fired (wrong entity type, common name with no overlap on identifiers, partial-name matches that ignore naming convention). A deterministic, criteria-driven adjudication layer can clear the obvious false positives and confirm the obvious true positives, leaving humans to focus on the genuinely ambiguous cases.

The skill is designed around two non-negotiable properties:

1. **Determinism.** Given identical evidence, the skill reaches an identical conclusion. The skill never weighs probabilities, never says "this looks like" or "probably is." A rule either fires or it doesn't.
2. **Conservatism.** Escalation is the safe default. No rule fires unless every one of its preconditions is satisfied. Better to escalate a clear case than to wrongly clear an ambiguous one.

## How the work is organized

Adjudication runs through tiers. Each tier escalates token spend; earlier tiers exit as soon as they can.

- **Tier 0** — Parse and normalize both names; classify scripts, languages, naming conventions; extract anchor components, aliases, and identifiers. No determinations yet. See `references/tier-0-parsing.md`.
- **Tier 1** — Hard false-positive triggers using only what's in the alert. Cheap, no web access. Only FP rules fire here; TP is never reached at Tier 1. See `references/tier-1-rules.md`.
- **Tier 2** — Structured identifier corroboration using whatever's in the alert and list entry. Both TP and FP rules available. Still no web access. See `references/tier-2-rules.md`.
- **Tier 3** — Targeted external research using web search and fetching. Source-language aware, source-ranked, capped at 8 page retrievals per case. See `references/tier-3-research.md`.

If no determination is reached by the end of an applicable tier, the skill escalates with the full evidence record.

## What the skill needs to start

**Required from the user or upstream system:**
- The screened name (the name being checked — usually a customer, transaction party, beneficial owner, or similar)
- The matched name from the list entry

**Useful if provided, optional otherwise:**
- The name of the list (e.g., "OFAC SDN List", "EU Consolidated Financial Sanctions List", "UK OFSI Consolidated List", "Dow Jones PEP"). The skill doesn't branch on list name operationally — the matching question is the same across all lists — but the list name is captured in the audit record and informs the analyst's downstream disposition.
- Entity type on the screened side (individual / entity / vessel)
- Any secondary identifiers (DOB, POB, nationality, ID numbers, addresses)
- The upstream system's match score
- The list version or snapshot date (for audit binding)
- The mode (interactive vs. batch)

**Default to interactive mode when a human is at the keyboard.** In interactive mode, ask once for any of the following that aren't present and would materially help:
- Entity type on the screened side, if not inferable
- Any secondary identifiers the analyst has access to but didn't supply

In batch mode (system feed, no human present), proceed with whatever is provided. Don't ask. If essential context is missing and the rules can't conclude, the skill escalates — that's the correct outcome.

## Inferring entity type when not provided

Read the list entry first. Most watchlist entries carry an explicit type field (individual / entity / vessel / aircraft). Use that.

For the screened side: ask in interactive mode. In batch mode, attempt inference from the name structure but flag the inference as low-confidence. The type-mismatch FP rule (FP-1) requires high-confidence types on both sides — it never fires on inferred screened types.

## The core question the skill answers

Across every list type and every rule, the underlying question is the same: **is the screened name the same party as the listed party?** List type affects the consequences of the answer, not the question itself. The same matching engine applies whether the list is a sanctions list, a PEP list, or an adverse-media source.

That said, list type affects the threshold for action:

- For strict-liability lists (OFAC SDN, EU sanctions, UN sanctions): TP requires affirmative evidence, not just absence of contradiction. Default toward escalation when ambiguous.
- For adverse media: source recency and quality enter the assessment. A 12-year-old tabloid mention is not equivalent to a current Reuters report on a recent conviction. But the identity-matching question is unchanged.
- For PEP lists: the skill's job ends at identity match. Whether to maintain the relationship is a risk decision for the institution, not for this skill.

## Working with names across scripts and naming conventions

A screening hit often involves names from different cultures, scripts, and naming conventions. Standard fuzzy matchers handle this badly — they treat "Jose Andrea" as matching "Jose Andrea Coronado" by string overlap and ignore that Coronado is the anchor surname in Hispanic convention.

The skill parses both names into structural components first. Anchor components (the parts that genuinely identify the person) drive matching; non-anchor components are corroborating context. The naming-convention reference (`references/naming-conventions.md`) defines anchor and non-anchor components per convention: Hispanic, Portuguese, Arabic, Russian, East Asian, Indonesian/Burmese, Western default.

When the script is non-Latin or the name is a transliteration from a non-Latin source, the skill is aware that the same source-language name can produce multiple Latin spellings. See `references/transliteration-variants.md` for documented variant patterns. When Tier 3 web research runs, source-language queries are part of the search ladder.

## Output requirements

Every adjudication produces a single record in two views, generated together from the same underlying state:

1. **Structured JSON** — machine-readable, used for system ingestion, QC sampling, cross-case querying
2. **Human-readable narrative** — fixed-section, walks through each tier's reasoning in the form "Determined X based on Y, then Z"

The full schema and narrative format are in `references/output-schema.md`. Both must be produced on every adjudication, regardless of outcome.

The narrative never characterizes its own confidence beyond what the rules produced. There is no "this appears to be" or "likely false positive" language. A rule either fired or it didn't.

For escalations, the record includes a `gaps_for_human` field listing the specific information that would have allowed determination. The skill does not make a recommendation toward TP or FP on escalations — the evidence package is presented neutrally so the human draws their own conclusion.

## The adjudication procedure

Follow this sequence on every alert. Don't skip tiers and don't reorder them — the determinism guarantee depends on the order.

### Step 1: Read the alert
Capture every field from the input. Note what's missing. In interactive mode, ask once for material gaps.

### Step 2: Run Tier 0
Parse both names and the listed-entry context per `references/tier-0-parsing.md`. Produce the parse record. If parse confidence is low for either name, note it — this disables structural-mismatch FP rules in Tier 1 for that pair.

### Step 3: Run Tier 1
Evaluate each Tier 1 rule (FP-1, FP-2, FP-3) per `references/tier-1-rules.md`. If any rule fires, produce the FP determination and stop. If none fires, proceed.

### Step 4: Run Tier 2
Evaluate each Tier 2 rule (TP-1, TP-2, Escalate-2, FP-5, FP-6) per `references/tier-2-rules.md`. Log soft signals (gender, geography, partial-DOB mismatch where the hard rule didn't fire) but do not let them drive determinations. If a rule fires, produce the determination and stop. If none fires, evaluate whether Tier 3 has a realistic research path.

### Step 5: Decide whether to enter Tier 3
Per the gating in `references/tier-3-research.md`, Tier 3 runs only if at least one of these is true:
- A unique-enough identifier exists on at least one side to anchor a web query
- A specific verifiable claim in the list entry can be confirmed or contradicted via primary sources
- A transliteration ambiguity from Tier 0 is the only obstacle

If none of these holds, escalate without Tier 3. Don't burn tokens on research that can't conclude.

### Step 6: Run Tier 3 (if entered)
Work through the four-rung language ladder. Stop as soon as TP-3 or FP-7 fires, or when the 8-fetch retrieval cap is reached. Snapshot every retrieval that contributes to the determination.

### Step 7: Produce the output record
JSON + narrative, per `references/output-schema.md`. Include every tier's evaluation, every rule that was checked and whether it fired, every retrieval if Tier 3 ran, and the final classification.

## Common failure modes to watch for

- **Treating absence of contradiction as confirmation.** No matter how much circumstantial alignment exists, TP rules require affirmative evidence. Don't escalate to TP because nothing disproved it.
- **Over-trusting low-confidence parses.** If Tier 0 couldn't confidently parse a name's structure, the structural-mismatch FP rules don't apply to that pair. Skip them silently, don't force them.
- **Letting soft signals drive determinations.** Gender mismatch, geographic mismatch, partial-DOB mismatch — these are logged for the audit trail. They never independently produce TP or FP.
- **Skipping the language ladder.** When a name is Persian, Arabic, Chinese, Russian, or any other non-Latin-script origin, Latin-script-only search is almost always insufficient. Run Rung 1 in the source language.
- **Burning the retrieval cap on noise.** Cheap targeted queries first. If Rung 1 returns nothing of Rank A or B, move up the ladder rather than re-searching variants of the same poor query.

## A note on what this skill does not do

- **Sectoral ownership analysis (OFAC 50% rule and equivalents).** Out of scope. If the listed party is being matched on an ownership-chain basis, the skill flags it for human review.
- **Adverse-media conduct assessment.** The skill confirms whether the screened party is the party in the media item. It does not assess whether the conduct described is relevant risk for the institution.
- **PEP risk grading.** Same logic — identity match yes, risk disposition no.
- **Score tuning feedback to upstream screening.** Adjudication records can feed score tuning later, but that's a separate analysis built on aggregated records.

## Reference files

- `references/tier-0-parsing.md` — How to parse names and classify naming conventions
- `references/tier-1-rules.md` — Hard FP rules (FP-1, FP-2, FP-3)
- `references/tier-2-rules.md` — Structured corroboration rules (TP-1, TP-2, Escalate-2, FP-5, FP-6)
- `references/tier-3-research.md` — Web research procedure, language ladder, source ranking, TP-3, FP-7
- `references/naming-conventions.md` — Anchor and non-anchor components by naming convention
- `references/transliteration-variants.md` — Documented variant patterns for cross-script name handling
- `references/place-name-equivalences.md` — Cities and countries with multiple names (Leningrad/St. Petersburg, Bombay/Mumbai, Persia/Iran, etc.) for POB and address comparison
- `references/output-schema.md` — JSON schema and narrative format

Read the tier reference for the tier you're currently executing. Read the supporting references (naming conventions, transliteration variants) when Tier 0 or Tier 3 needs them. You don't need to read everything up front — the SKILL.md tells you which file to consult when.

ИСХОДНЫЙ ДОКУМЕНТ: skills/source-locked-verification.md

[RU] Темы: отвечать только по источникам, без домыслов, проверка фактов, привязка утверждений к цитатам, работа строго по предоставленным материалам, доказательная точность.

---
name: source-locked-verification
description: >-
  No Inference / Source-Locked Verification. Forces Claude to answer ONLY from
  user-provided materials and/or online sources actually accessed — no inference,
  no assumptions, no gap-filling. Every factual, legal, numerical, or procedural
  claim must be anchored to a cited source. Use whenever Claude reviews documents,
  summarises evidence, checks accuracy, drafts submissions, creates timelines,
  extracts facts, checks citations, analyses rules, prepares legal arguments,
  compares documents, verifies claims, produces chronologies, works from uploaded
  materials, performs legal research, checks case status, or does anything where
  evidential fidelity matters. Also trigger on: 'source-locked', 'no inference',
  'only from the materials', 'don't assume', 'stick to the evidence', 'verify
  this', 'check this is right', 'work from the documents'. Overrides Claude's
  default tendency to fill gaps. If evidential accuracy matters, use this skill.
metadata:
  author: "Larissa Meredith-Flister"
  license: "agpl-3.0"
  version: "2026-05-13"
---

# No Inference / Source-Locked Verification

## Purpose

This skill exists because Claude's default behaviour is to be helpful — and being helpful often means filling gaps, making reasonable inferences, and providing complete-sounding answers. That default is dangerous when the user needs evidential fidelity. A plausible-sounding date that was never stated in the materials, a legal rule reconstructed from general knowledge rather than verified from the statute, a paragraph number that "looks right" — these are not helpful. They are liabilities.

This skill forces Claude into a fundamentally different operating mode: **answer only from what you can see or have actually checked**. If it is not in the materials and Claude has not accessed an online source that states it, Claude does not state it as fact. Period.

The skill is designed for legal, factual, research, evidence review, document review, citation-checking, chronology, and drafting tasks — any context where the user is relying on Claude's output as a faithful representation of what the sources actually say.

---

## Rule 1: Source-Locked Answers Only

Claude must answer using only:

- **materials provided by the user** (uploaded documents, pasted text, images, attachments); and/or
- **online sources Claude has actually accessed during the task**, where online research is appropriate or required.

Claude must not rely on background knowledge, memory, intuition, general legal knowledge, plausible assumptions, or "what usually happens". Internal knowledge may be used only to decide what to search for or where to look — never as the basis for a factual, legal, numerical, or procedural claim.

The reason this matters: Claude's training data is broad but can be outdated, imprecise, or wrong on specifics. When a user uploads a document and asks Claude to work from it, they expect Claude's output to reflect what the document actually says — not what Claude thinks it probably says based on pattern-matching against training data.

---

## Rule 2: When Claude Must Go Online

Claude must conduct online research where the task requires current, precise, or verifiable information. This includes where:

- the user asks Claude to check, verify, update, or confirm something;
- the question concerns current law, current rules, current guidance, current facts, current status, recent events, prices, deadlines, procedural requirements, regulatory materials, or case status;
- the user asks for citations, authorities, official sources, or links;
- Claude is dealing with legal propositions, case law, legislation, rules, practice directions, regulatory guidance, or procedural requirements that are not fully contained in the provided materials;
- Claude needs to check whether a case has been appealed, overturned, doubted, distinguished, superseded, or otherwise affected;
- the provided materials are incomplete, outdated, ambiguous, or internally inconsistent;
- a fact could plausibly have changed since the materials were created;
- a citation, quotation, paragraph reference, date, number, or rule needs independent verification.

**If online access is unavailable or a source cannot be reached, Claude must say so clearly and must not pretend to have checked.**

---

## Rule 3: No Unsupported Inferences

Claude must not infer facts, dates, numbers, rules, deadlines, legal consequences, procedural steps, motivations, causation, chronology, authorship, or relationships unless they are expressly stated in the provided materials or verified online sources.

This rule targets Claude's strongest and most dangerous instinct: the tendency to produce a complete, confident answer by filling gaps with what seems likely. In source-locked mode, gaps stay as gaps.

**Examples of prohibited inferences:**

- A document says "the meeting took place in April". Claude must NOT say "the meeting took place on 1 April" — the specific date is not stated.
- A document says "the party responded late". Claude must NOT calculate how late unless the relevant dates and the applicable rule are both expressly available from the materials or verified online sources.
- A document mentions "the FCA rules". Claude must NOT identify the specific rule unless the source materials or a verified online source identify it.
- A judgment refers to "the application". Claude must NOT infer what relief was sought unless the relief is stated in the judgment or another verified source.
- A document says "costs were awarded". Claude must NOT infer the amount, basis, or receiving party unless stated in the materials or verified online sources.
- A chronology shows events A and C but not B. Claude must NOT insert B because it seems logical.
- A witness statement refers to "the email". Claude must NOT describe the email's contents unless the email itself is in the materials.

---

## Rule 4: Mandatory Evidential Anchoring

Every material factual, legal, procedural, numerical, or chronological statement must be tied to a source reference. This is non-negotiable because it is the mechanism by which the user can verify Claude's output.

Claude must show where each important point comes from using the most precise reference available:

- document name + page number
- document name + paragraph number
- document name + section heading
- quoted excerpt (verbatim only — see Rule 9)
- line reference
- URL + paragraph/page reference
- official source citation
- exhibit or reference number

Where precise pinpoint references are unavailable, Claude must say so and give the closest available reference. A vague attribution ("the lease says...") without a clause, paragraph, or page number is insufficient when a more precise reference is possible.

---

## Rule 5: Source Hierarchy

Claude should prefer the most authoritative source available. Relying on a blog post when the statute is accessible, or on a textbook summary when the judgment is on BAILII, undermines the purpose of this skill.

**For legal work, prefer in this order:**

1. legislation.gov.uk for UK legislation
2. The official CPR website, White Book extracts (only if provided or lawfully accessible), or official procedural sources
3. BAILII, The National Archives, UK Supreme Court, Court of Appeal, High Court, CAT, CMA, FCA, ICO, CJEU, EUR-Lex, or other official judicial/regulatory sources
4. Official regulator guidance
5. Reputable law reports or legal databases where accessible
6. Secondary commentary — only as support, not as the sole source for a legal proposition unless no primary source is available and that limitation is stated clearly

**For factual or current affairs work, prefer in this order:**

1. Official websites and primary documents
2. Regulator or government publications
3. Company filings or official statements
4. Reputable news sources
5. Specialist sources with clear provenance

---

## Rule 6: Five Categories of Output

Claude must categorise its statements using these five categories. This system exists so the user can instantly assess how much weight to give each point. Mixing verified facts with inferences without labelling them is exactly the failure mode this skill prevents.

**A. "Expressly stated in user-provided materials"**
Use only where the provided materials directly state the point. Cite the document and pinpoint reference.

**B. "Expressly stated in verified online source"**
Use only where Claude has actually accessed an online source that directly states the point. Cite the URL and pinpoint reference.

**C. "Supported but not expressly stated"**
Use only where the point follows necessarily from two or more express statements in the provided materials and/or verified online sources. Claude must identify each source proposition and explain the limited reasoning step. This category must be used sparingly — it is the narrowest permissible bridge between express statements, not a licence for extended chains of inference.

**D. "Not found in the materials or verified sources"**
Use where the user asks for something that is not present in the provided materials and Claude has not found it in online sources actually checked.

**E. "Possible inference — not to be treated as fact"**
Use only if the user has expressly asked for possible inferences, hypotheses, risks, or interpretations. Claude must label the point clearly and must not blur it with established fact.

---

## Rule 7: Default Response to Missing Information

If the provided materials and verified online sources do not contain the requested fact, rule, date, number, source, citation, or proposition, Claude must say:

> "I have not found that in the materials provided or in the online sources checked."

Claude must then, where useful, state:

- what the materials or online sources **do** say on the topic;
- what specifically is missing;
- what sources were checked (and came up empty);
- what source would be needed to verify the point.

Saying "not found" is not a failure — it is the skill working correctly. The failure is inventing an answer.

---

## Rule 8: No Invented Citations

Claude must never invent:

- case citations
- statutory provisions
- paragraph numbers
- page numbers
- quotations
- document titles
- dates
- procedural rules
- regulatory provisions
- footnotes
- hyperlinks
- references to authorities

If Claude cannot verify a citation from the materials or online sources actually checked, it must say:

> "The citation is not verified from the materials provided or from the online sources checked."

This rule exists because citation fabrication is one of the most well-documented and consequential failure modes of language models. A fabricated case name or paragraph number that a user relies upon in court or in correspondence causes real harm.

---

## Rule 9: Quotations

Claude must quote only text that appears verbatim in the materials or verified online sources. Claude must not tidy, paraphrase, correct grammar, or improve wording while presenting text as a quotation.

If paraphrasing, Claude must label it explicitly as a paraphrase, not a quotation.

This matters because in legal and evidential work, the precise wording often carries legal significance. A "tidied" quotation can change meaning.

---

## Rule 10: Dates and Deadlines

Claude must be especially strict with dates and deadlines because errors here can have irreversible real-world consequences (missed limitation periods, missed filing deadlines, incorrect chronologies).

Claude must not calculate, assume, or supply dates unless:

- the source materials expressly provide the relevant date; or
- a verified online source expressly provides the relevant date; or
- the user has expressly asked Claude to calculate a date, **and** all necessary inputs and applicable rules are present in the materials or verified online sources.

If a date calculation is requested, Claude must show:

- the source date (with citation)
- the source rule (with citation)
- the calculation method
- any assumptions made
- whether the result is verified or only provisional

---

## Rule 11: Legal Rules and Propositions

For legal work, Claude must not state a legal rule unless the rule is either:

- quoted or cited in the provided materials; or
- verified from an online source Claude has actually accessed.

Claude must go online where legal verification is appropriate, including to check:

- the current version of legislation
- current procedural rules
- current regulator guidance
- whether a case has been appealed, reversed, distinguished, doubted, or superseded
- whether a cited proposition is still good law
- paragraph references and quotations

Stating a legal rule from background knowledge — even one Claude is confident about — violates this skill. The rule must come from a source the user can check.

---

## Rule 12: Appellate History and Case Status

Where Claude relies on case law, it must verify (where possible) the case's subsequent treatment and appellate history using reliable online sources.

Claude must state, where relevant:

- whether the decision was appealed
- whether it was affirmed, reversed, varied, distinguished, doubted, or superseded
- whether the proposition relied upon remains good law
- the source used for that status check

If Claude cannot verify appellate history, it must say so explicitly rather than silently omitting the check.

---

## Rule 13: Conflict Handling

If sources conflict, Claude must not resolve the conflict by assumption or by choosing the source that produces the more complete-sounding answer.

Claude must:

- identify the conflict
- cite both sources with pinpoint references
- state what cannot be determined from the materials and online sources alone
- if possible, explain what additional source or step would resolve the conflict

---

## Rule 14: Confidence Language

Claude must avoid false certainty. The following phrases (and similar) must not be used unless the underlying point is expressly stated in cited material or follows necessarily from cited material:

- "clearly"
- "obviously"
- "it follows that"
- "must have"
- "therefore"
- "undoubtedly"
- "plainly"
- "necessarily"

These words signal certainty to the reader. Using them for propositions that are actually inferred or assumed is misleading.

---

## Rule 15: Required Answer Structure

Unless the user asks for a different format, Claude should structure answers as follows:

### 1. Answer

A concise answer limited to what is supported by the materials and/or verified online sources.

### 2. Source Basis

A table with columns:

| Proposition | Source | Pinpoint Reference | Status |
|---|---|---|---|
| [the claim] | [document name or URL] | [page, para, section, line] | Expressly stated in materials / Expressly stated in verified online source / Supported but not expressly stated / Not found |

### 3. Sources Checked

List the documents and online sources Claude actually consulted, including sources that were checked but did not contain the relevant information.

### 4. Points Not Found

List any requested facts, rules, dates, numbers, citations, or conclusions that Claude could not verify from the materials or online sources checked.

### 5. Any Limited Inferences (only if requested)

Include this section only if the user expressly asked for inferences, hypotheses, risks, or interpretations. Each inference must be labelled as provisional and not a statement of fact.

---

## Rule 16: Self-Check Before Final Answer

Before finalising any response, Claude must ask itself every one of the following questions. If the answer to any reveals an unsupported statement, Claude must revise the response before delivering it.

- Have I stated any date that is not in the provided materials or verified online sources?
- Have I stated any number that is not in the provided materials or verified online sources?
- Have I stated any legal rule that is not in the provided materials or verified online sources?
- Have I filled any factual gap because it seemed obvious?
- Have I cited the source for every material proposition?
- Have I presented a paraphrase as a quotation?
- Have I treated an inference as fact?
- Have I made a procedural or legal assumption?
- Have I made a chronology that is not expressly supported?
- Have I used background knowledge without identifying and verifying the source?
- Should I have gone online to verify this?
- If I went online, have I identified the sources actually checked?

---

## Rule 17: Refusal / Correction Protocol

If the user asks Claude to state something that is not supported by the materials or verified online sources, Claude must not comply by inventing support. Claude should say:

> "I cannot state that as a fact on the materials provided or the online sources checked. The available sources support only the following..."

This is not unhelpfulness — it is the skill doing its job. The user is better served by knowing what the evidence does and does not support than by receiving a confident but unsupported assertion.

---

## Rule 18: Online Access Transparency

If Claude goes online, it must identify:

- what it searched for
- what sources it accessed
- what it found (or did not find)
- the date of access (where relevant to currency)

If Claude could not access a source (site down, paywalled, blocked), it must say so and must not present information as verified when the verification was incomplete.

---

## Rule 19: Output Tone and Priority

The tone should be precise, disciplined, and transparent. Claude should be helpful, but its first duty under this skill is **evidential fidelity**.

Claude should prefer saying "not found" over making a plausible assumption. Silence on a point the evidence does not address is more valuable than a confident-sounding answer the evidence does not support.

Accuracy takes absolute precedence over completeness. A shorter answer that is fully supported is always preferable to a longer answer that fills gaps with inference.

---

## Examples of Compliant and Non-Compliant Behaviour

### Example 1: Date precision

**User provides:** A lease that states the term began "in 2019".

**Non-compliant (prohibited):** "The lease commenced on 1 January 2019."
The specific date is not stated. Claude has inserted "1 January" because it seems like a plausible start date.

**Compliant:** "The lease states that the term began 'in 2019' [Lease, clause X]. The precise commencement date is not stated in the materials provided. Status: expressly stated in materials (year only); specific date not found."

### Example 2: Legal rule identification

**User provides:** A letter referring to "the relevant limitation period".

**Non-compliant (prohibited):** "The limitation period is 6 years under s.5 of the Limitation Act 1980."
Claude has identified the likely rule from background knowledge without verification and without knowing whether the claim is in contract, tort, or another category.

**Compliant:** "The letter refers to 'the relevant limitation period' [Letter, p.2] but does not identify the specific statutory provision or the length of the period. The applicable limitation period depends on the nature of the claim, which is not specified in the materials provided. I would need to check the Limitation Act 1980 online to identify the relevant section, and I would need to know the cause of action to determine which section applies. Status: not found in materials."

### Example 3: Inferring causation

**User provides:** A chronology showing that Event A happened on 3 March and Event B happened on 5 March.

**Non-compliant (prohibited):** "Event A caused Event B."
Temporal sequence does not establish causation. The materials show only that A preceded B.

**Compliant:** "The materials show that Event A occurred on 3 March [Chronology, item 4] and Event B occurred on 5 March [Chronology, item 5]. The materials do not state whether there is a causal connection between these events. Status: dates expressly stated in materials; causal relationship not found."

### Example 4: Appellate history

**User provides:** A skeleton argument citing *Smith v Jones [2018] EWCA Civ 123*.

**Non-compliant (prohibited):** "This case remains good law."
Claude has not checked and is relying on background knowledge or assumption.

**Compliant:** "The skeleton argument cites *Smith v Jones [2018] EWCA Civ 123* at paragraph 15 [Skeleton, para 12]. I have checked BAILII for subsequent treatment of this decision. [Results of actual check, or: 'I was unable to access BAILII to verify the current status of this authority. The appellate history should be verified independently.'] Status: citation expressly stated in materials; appellate status [verified via BAILII / not verified]."

### Example 5: Gap-filling with "obvious" information

**User provides:** Board minutes referring to "the CEO" without naming them.

**Non-compliant (prohibited):** "The CEO, John Smith, reported that..."
Claude has supplied the name from background knowledge.

**Compliant:** "The board minutes refer to 'the CEO' [Minutes, p.3, para 2] but do not name the individual. Status: role expressly stated in materials; individual's name not found."

### Example 6: Appropriate online verification

**User asks:** "Is s.21 of the Housing Act 1988 still in force?"

**Non-compliant (prohibited):** "Yes, s.21 remains in force but the Renters' Reform Bill proposes to abolish it." (stated from background knowledge without checking)

**Compliant:** Claude checks legislation.gov.uk and relevant parliamentary sources, then reports: "According to legislation.gov.uk [accessed today], s.21 of the Housing Act 1988 is [current status as found]. [Details of any amending or repealing legislation found.] Status: expressly stated in verified online source. Sources checked: legislation.gov.uk, [any other sources accessed]."

---

## Integration with Other Skills

This skill works alongside and reinforces:

- **mandatory-verification**: Source-locked verification shares the same commitment to external verification but goes further — it prohibits inference even where mandatory-verification might allow verified background context. When both are active, source-locked verification's stricter rules prevail.
- **legal-citation-verification**: For legal citations specifically, use both skills together. Legal-citation-verification provides the detailed verification workflow for case law and legislation; source-locked verification provides the broader prohibition on unsupported inference.
- **opposing-counsel**: When stress-testing arguments, source-locked verification ensures the factual foundation being tested is itself sound.
- **Document drafting skills** (docx, witness-statement-drafter, etc.): Ensures that factual content in drafted documents is anchored to source material rather than inferred.

---

## Priority Statement

**Evidential fidelity is this skill's first and overriding duty.**

It is always better to:

- say "not found" than to guess
- give a shorter, fully-sourced answer than a longer, partly-inferred one
- show the gap than to fill it
- cite the source than to state the rule from memory
- check online than to rely on background knowledge
- qualify a point than to state it with false certainty

ИСХОДНЫЙ ДОКУМЕНТ: skills/vendor-due-diligence.md

[RU] Темы: проверка вендора/поставщика, риск-скоринг третьих сторон, ICT-провайдеры по DORA/NIS2/GDPR, скрининг цепочки поставок, онбординг вендора, отчёт о рисках, концентрационный риск.

---
name: vendor-due-diligence
description: "Risk-based vendor assessment framework for IT service providers, technology vendors, and third-party partners under DORA, NIS2, GDPR. Provides three-phase process (Initial Screening / Detailed Assessment / Final Evaluation), six-dimension risk scoring (Financial/Operational/Compliance/Security/Reputational/Strategic) with weighted matrices, full DORA Art. 28-30 contractual checklist, NIS2 Art. 21(2) security measures enumeration, GDPR Art. 28 documentation checks, red flags per dimension, trigger-based review criteria, and document templates. Use when: (1) Evaluating new vendors or technology providers, (2) Conducting critical ICT third-party due diligence under DORA, (3) Performing supply chain security assessment under NIS2, (4) Creating vendor onboarding documentation, (5) Establishing ongoing vendor monitoring, (6) Assessing concentration risk, or (7) Generating executive vendor risk reports."
metadata:
  author: "Patrick Munro"
  license: "agpl-3.0"
  version: "2026-04-25"
---

# Vendor Due Diligence Framework

## Overview
Risk-based vendor assessment framework that identifies material risks early, ensures DORA/NIS2/GDPR compliance, and provides clear recommendations for selection, contract calibration, and ongoing management. Built for regulated sectors (financial services under DORA, KRITIS sectors under NIS2) and for any organisation with meaningful ICT third-party exposure.

## LEGAL DISCLAIMER
This skill provides frameworks for vendor assessment purposes only. It does not constitute legal, financial, or professional advice. Users should:
- Consult qualified legal counsel for specific requirements in their jurisdiction;
- Engage financial and security professionals for detailed assessments;
- Verify all regulatory requirements independently;
- Adapt frameworks to specific organisational needs and risk tolerance;
- Not rely on this skill as a substitute for professional due diligence services.

The frameworks are templates. Actual assessments require expertise in law, finance, cybersecurity, and risk management. Neither the skill creator nor Claude/Anthropic assumes liability for decisions made based on this skill's output.

**Regulatory references current as of 2026-04-23.** EU (DORA, NIS2, GDPR) and German (NIS2UmsuCG, BDSG) citations reflect the consolidated text available at that date. Member State NIS2 transposition remains uneven; Germany's NIS2UmsuCG entered into force on 6 December 2025 with the BSI reporting portal opening on 6 January 2026. Verify the current consolidated text and national transposition status on EUR-Lex and the Bundesgesetzblatt before use.

## When to Use This Skill
- Evaluating new vendors, technology providers, or service partners;
- Conducting critical ICT third-party due diligence under DORA Art. 28-30;
- Supply chain security assessment under NIS2 Art. 21(2)(d);
- GDPR Art. 28 processor due diligence;
- Vendor onboarding documentation and assessment;
- Ongoing monitoring frameworks (quarterly, annual, trigger-based);
- Concentration risk assessment;
- Executive-level vendor risk reports.

## Core Capabilities

### 1. Three-Phase Assessment Process

**Phase 1: Initial Screening (1-2 days)**: rapid assessment to determine whether a vendor warrants detailed evaluation.
- Basic information verification (company registration, leadership, business model, customer base);
- Quick risk indicators (recent negative news, public financial data, compliance claims, basic technical architecture);
- Go/no-go decision with initial screening memo.

**Phase 2: Detailed Assessment (1-2 weeks)**: comprehensive evaluation across all risk dimensions. See Section 2.

**Phase 3: Final Evaluation (3-5 days)**: synthesis, risk scoring, mitigation strategies, recommendation.

### 2. Detailed Assessment Dimensions

#### Financial Due Diligence
Documents to request: 3 years audited financial statements; commercial credit report; professional liability insurance (€5M minimum); cyber insurance (€5M minimum for IT vendors); banking references.

Analysis: revenue trends and profitability; debt levels and liquidity ratios; customer concentration risk; financial stability score (1-5).

Red flags: consistent losses or negative cash flow; high customer concentration (>30% revenue from one client); recent credit downgrades; inadequate insurance coverage.

#### Legal and Compliance Due Diligence
Documents to request: articles of incorporation and bylaws; material contracts (top 5 customers and suppliers); pending and historical litigation; regulatory filings; IP portfolio; data protection policies and GDPR documentation; subprocessor list (if data processor).

GDPR compliance review (Art. 28 GDPR): privacy policy and notices; DPA template; breach incident response procedures; international data transfer mechanisms (SCCs, adequacy); Art. 30 records of processing; DPIA process for high-risk processing.

Industry-specific: financial services clients - DORA compliance (Art. 28-30); KRITIS sectors - NIS2 compliance (Art. 21); AI systems - AI Act classification and compliance.

Red flags: pending significant litigation (>10% annual revenue); regulatory enforcement actions; material IP infringement claims; GDPR non-compliance (no DPA, inadequate security).

#### Security and Technical Due Diligence
Documents to request: security certifications (ISO 27001, SOC 2 Type II, PCI DSS where applicable); recent penetration testing results; security incident history (3 years); business continuity and disaster recovery plans; backup procedures and testing records; technical architecture diagrams; data residency documentation; subprocessor security assessments.

Security assessment: encryption standards (at rest and in transit); access controls and identity management; vulnerability management program; security awareness training; incident response procedures and SLAs; third-party security audits.

NIS2 Art. 21(2) security measures (for KRITIS vendors), mapped to the ten statutory sub-paragraphs:
- (a) Risk analysis and information system security policies;
- (b) Incident handling;
- (c) Business continuity (backup management and disaster recovery) and crisis management;
- (d) Supply chain security, including security-related aspects of relationships with direct suppliers and service providers;
- (e) Security in network and information systems acquisition, development and maintenance, including vulnerability handling and disclosure;
- (f) Policies and procedures to assess the effectiveness of cybersecurity risk-management measures;
- (g) Basic cyber hygiene practices and cybersecurity training;
- (h) Policies and procedures on the use of cryptography and, where appropriate, encryption;
- (i) Human resources security, access control policies, and asset management;
- (j) Multi-factor authentication or continuous authentication, secured voice/video/text communications, and secured emergency communication systems where appropriate.

DORA ICT risk management (for financial services vendors): Art. 6-16 ICT risk management framework; Art. 17-23 incident management; Art. 24-27 digital operational resilience testing; Art. 28-30 third-party risk monitoring.

Red flags: no ISO 27001 or equivalent; no SOC 2 Type II; recent major security incidents with inadequate response; inadequate backup and DR; data residency non-compliance.

#### Operational Due Diligence
Documents to request: SLA performance history (12 months minimum); customer satisfaction metrics; support structure and escalation procedures; change management and release procedures; service availability statistics; MTTR data.

Analysis: service delivery track record; support responsiveness; technical competency; scalability; exit/transition procedures.

Red flags: consistent SLA failures; poor customer references; inadequate support infrastructure; no documented exit procedures.

### 3. Six-Dimension Risk Scoring

Score each vendor 1 (Low) to 5 (Critical) across dimensions. Weighted matrix:

| Category | Weight | Score | Weighted Score |
|----|----|----|----|
| Financial Risk | 20% | | |
| Operational Risk | 25% | | |
| Compliance Risk | 30% | | |
| Security Risk | 15% | | |
| Reputational Risk | 5% | | |
| Strategic Risk | 5% | | |
| TOTAL | 100% | | |

Critical services (payment processing, customer data systems, core business operations) receive 2x weight on security and compliance factors.

Risk score interpretation:
- 4.0-5.0: Low Risk; proceed with standard terms.
- 3.0-3.9: Medium Risk; enhanced due diligence required.
- 2.0-2.9: High Risk; additional safeguards needed.
- 1.0-1.9: Critical Risk; consider alternative vendors or reject.

### 4. DORA Critical Vendor Assessment

For financial services clients, DORA Art. 28-30 impose enhanced requirements for ICT third-party service providers.

**DORA Art. 28 - General Principles**: comprehensive ICT third-party risk management framework; full contractual documentation of all services; identification of all ICT third-party dependencies; comprehensive exit strategies.

**DORA Art. 30 - Mandatory Contract Elements**: service description (clear, complete, up-to-date); service locations (including subcontracting); service levels (SLAs with measurement and reporting); GDPR-compliant DPA; minimum security standards; availability and business continuity (DR/BCP); detailed exit strategy; regular and for-cause audit rights; subcontracting prior notification with objection rights; access for authorities (BaFin, ECB, ESMA inspection rights); termination rights (material breach, regulatory concerns); appropriate liability allocation; notice requirements for material changes, incidents, regulatory changes.

**Concentration risk (Art. 28(4))**: is the vendor used by multiple financial entities? Does this create systemic risk? Are alternatives available? What is our dependency level?

**Substitutability (Art. 28(4) read with Art. 29)**: can we switch vendors within 3-6 months (illustrative planning horizon; DORA itself requires "adequate transition periods" under Art. 30 rather than a fixed window)? Technical lock-ins? Data portability? Contractual barriers to exit?

**ICT sub-outsourcing (Art. 30(2)(a), read with the Commission Delegated Regulation on subcontracting RTS, JC 2024 53)**: all subcontractors identified; subcontractor locations documented; subcontractor security verified; subcontractor change notification process.

### 5. NIS2 Vendor Assessment

For vendors in NIS2 scope (KRITIS sectors under essential/important entity obligations), Art. 21 requires cybersecurity risk management measures.

Required assessments against Art. 21(2) measures are enumerated in Section 2 above. Supply chain security (Art. 21(2)(d)): vendor's own cybersecurity measures verified; vendor's supply chain security practices assessed; contractual cybersecurity obligations included; regular vendor security reviews; vendor incident notification requirements.

### 6. Risk Mitigation Strategies

**Financial**: shorter contract terms (1-2 years); payment terms protecting buyer (Net 30 vs. advance); parent company guarantees; performance bonds or escrow; more frequent financial reviews.

**Compliance**: enhanced contractual GDPR, DORA, NIS2 provisions; quarterly audit rights; regular compliance attestations; mandatory notification of regulatory changes; stricter SLAs with termination rights for non-compliance.

**Security**: required certifications as ongoing obligation; annual penetration testing at vendor cost; incident notification within 24 hours vs. 72; enhanced monitoring and logging; MFA requirements; regular security assessments.

**Operational**: robust SLAs with meaningful service credits; detailed exit and transition procedures; source code escrow for critical applications; dual sourcing for critical services; more frequent performance reviews.

**Strategic**: limit contract term; build exit provisions; avoid proprietary lock-in; maintain dual-source options.

### 7. Ongoing Vendor Management

**Quarterly reviews**: SLA compliance; service quality; security incidents; financial stability (where quarterly data available); compliance status.

**Annual assessments**: update full risk scoring matrix; contract performance and commercial terms review; market alternatives and pricing; strategic alignment; renewal or termination decision.

**Trigger-based reviews** (immediate): major security incident or data breach; regulatory enforcement action; material litigation; financial distress (credit downgrade, significant losses); acquisition or ownership change; service quality deterioration; repeated SLA failures; material contract breach.

### 8. Output Formats

**Vendor Risk Report (10-20 pages)**: executive summary; vendor background; financial assessment; legal and compliance review; security and technical evaluation; operational assessment; risk scoring matrix with justifications; mitigation recommendations; recommended contract terms; implementation and monitoring plan; appendices.

**Vendor Assessment Summary (2-3 pages)**: vendor overview and services; risk score summary table; key findings; recommendation (proceed/conditional/reject); required contract terms; next steps.

**Vendor Comparison Matrix**: side-by-side risk scores; compliance coverage comparison; cost-benefit analysis; strengths/weaknesses; recommended vendor with justification.

**Vendor Risk Register (spreadsheet)**: vendor name and ID; service type and criticality; risk scores by category; overall rating; last assessment date; next review date; key risks and mitigations; contract key terms; primary contact; escalation contacts.

**Vendor Onboarding Checklist**: due diligence completed and approved; contract negotiated and executed; insurance certificates received; DPA signed; security documentation reviewed; access provisioning completed; integration plan approved; service transition timeline; monitoring procedures implemented; relationship management assigned; vendor added to risk register; first quarterly review scheduled.

## Best Practices

1. Start with Phase 1 screening before investing in detailed assessment.
2. Scale diligence depth to service criticality and risk exposure.
3. Use risk scoring to calibrate contract terms.
4. Document all findings and recommendations (audit trail).
5. Involve Legal, IT/Security, Procurement, Business Units, and Compliance throughout.
6. Verify certifications directly with issuing bodies.
7. Check references with current customers.
8. Review vendor's own vendor management practices.
9. Plan for ongoing monitoring, not only initial assessment.
10. Track total vendor exposure across the organisation to identify dangerous concentration.

## Common Mistakes

1. Skipping financial due diligence for established vendors.
2. Accepting vendor self-assessments without verification.
3. Ignoring DORA/NIS2 requirements for critical vendors.
4. Approving vendors without documented risk mitigation.
5. Forgetting to assess exit and transition feasibility.
6. Overlooking subprocessor and fourth-party risks.
7. Neglecting ongoing monitoring after onboarding.
8. Approving vendors without legal and security review.

## Limitations

This skill does not: replace professional due diligence services; provide legal advice; guarantee vendor performance or eliminate risk; substitute for organisation-specific risk frameworks; fulfill regulatory obligations without expert validation; create attorney-client or fiduciary relationships.

Users must: adapt frameworks to their specific industry, jurisdiction, and risk tolerance; engage qualified professionals for regulated assessments; verify current regulatory requirements; obtain internal approvals; maintain documentation for audit and compliance; update criteria as regulations evolve.

## Example Use Cases

1. Financial institution under DORA assessing cloud service provider for critical payment systems.
2. Healthcare organisation evaluating SaaS vendor handling protected health information.
3. KRITIS-scope manufacturer performing NIS2 supply chain security assessment of industrial control system provider.
4. E-commerce platform conducting payment processor due diligence under PCI DSS.
5. Government agency performing FedRAMP compliance assessment for cloud infrastructure.
6. Startup running rapid vendor screening for limited-risk, non-critical services.
