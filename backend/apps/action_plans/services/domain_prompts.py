import re

DOMAIN_RAG_KEYWORDS = {
    "SERVICE_LAW":        "service law promotion transfer seniority government employee cadre",
    "LAND_ACQUISITION":   "land acquisition compensation market value deduction developmental charges",
    "CRIMINAL":           "criminal law bail conviction acquittal FIR charge cognizable offence",
    "CONSTITUTIONAL":     "fundamental rights writ petition judicial review Article 14 19 21 26 226",
    "TAXATION":           "income tax assessment demand ITAT tribunal AO deduction exemption",
    "MOTOR_VEHICLES":     "motor accident compensation MACT multiplier dependency loss of income",
    "LABOUR":             "industrial dispute reinstatement workman unfair dismissal retrenchment",
    "FAMILY_CIVIL":       "matrimonial divorce maintenance custody partition civil suit",
    "COMMERCIAL":         "contract breach commercial arbitration tender bid procurement",
    "ENVIRONMENTAL":      "environmental pollution clearance CRZ forest land diversion",
    "GENERAL":            "High Court Karnataka government writ petition order",
}

RAG_THRESHOLDS = {
    "SERVICE_LAW":      0.78,
    "LAND_ACQUISITION": 0.80,
    "CRIMINAL":         0.75,
    "CONSTITUTIONAL":   0.70,   # Most abstract — need lower threshold
    "TAXATION":         0.75,
    "MOTOR_VEHICLES":   0.78,
    "LABOUR":           0.78,
    "FAMILY_CIVIL":     0.72,
    "COMMERCIAL":       0.75,
    "ENVIRONMENTAL":    0.72,
    "GENERAL":          0.75,
}

def get_domain_key(area_of_law: str) -> str:
    """Map extracted area_of_law to a standard domain key."""
    if not area_of_law:
        return "GENERAL"
    
    aol = area_of_law.lower().strip()
    
    domain_patterns = [
        ("SERVICE_LAW",      ["service law", "service matter", "government servant", "civil services",
                               "promotion", "transfer", "seniority", "departmental proceeding"]),
        ("LAND_ACQUISITION", ["land acquisition", "compensation", "land revenue", "acquisition",
                               "rfctlarr", "writ against acquisition"]),
        ("CRIMINAL",         ["criminal", "penal code", "crpc", "bnss", "ipc", "bns", "ndps",
                               "pocso", "prevention of corruption", "bail", "sentence"]),
        ("CONSTITUTIONAL",   ["constitutional", "fundamental right", "article 14", "article 19",
                               "article 21", "article 25", "article 26", "writ jurisdiction",
                               "administrative law", "arbitrary", "equality"]),
        ("TAXATION",         ["income tax", "gst", "goods and services", "customs", "excise",
                               "value added tax", "vat", "tax", "itat", "tribunal revenue"]),
        ("MOTOR_VEHICLES",   ["motor vehicle", "motor accident", "mact", "road accident",
                               "compensation accident", "insurance claim accident"]),
        ("LABOUR",           ["labour", "industrial dispute", "workman", "reinstatement",
                               "retrenchment", "unfair labour", "standing orders"]),
        ("FAMILY_CIVIL",     ["matrimonial", "divorce", "maintenance", "custody", "partition",
                               "succession", "inheritance", "family", "matrimony"]),
        ("COMMERCIAL",       ["contract", "commercial", "arbitration", "tender", "procurement",
                               "bid", "purchase", "supply agreement"]),
        ("ENVIRONMENTAL",    ["environment", "pollution", "forest", "wildlife", "crz",
                               "environmental clearance", "ngt", "moef", "green tribunal"]),
    ]
    
    for domain_key, keywords in domain_patterns:
        if any(kw in aol for kw in keywords):
            return domain_key
    
    return "GENERAL"


# AGENT 1 DOMAIN ADDITIONS
AGENT1_DOMAINS = {
    "SERVICE_LAW": """
DOMAIN: Service Law
Focus questions:
- Did petitioner exhaust the remedy before Central Administrative Tribunal (CAT) before approaching HC?
  (If no, HC may lack jurisdiction — strong appeal ground)
- Does the precedent concern the specific cadre/post in dispute?
- Did SC uphold or strike down similar departmental discretion (transfers, DPC, promotions)?
Government's typical strong ground: Courts should not substitute their judgment for DPC/departmental discretion.
Government's typical weak ground: Arbitrary transfer orders without ACR consideration.
Relevant statutes to recognise: Karnataka Civil Services Rules 1957, Article 309/310/311 Constitution,
  Central Civil Services (CCA) Rules 1965, Karnataka State Civil Services Act 1978.""",
    "LAND_ACQUISITION": """
DOMAIN: Land Acquisition / Compensation
Focus questions:
- Did SC approve or disapprove deduction percentages in the 35-53% range?
- Was Pointe-based evidence (exemplar sale deeds) present or absent?
- Did SC uphold or reduce enhanced compensation from Reference Court?
Government's typical strong ground: No comparable sale deeds for the same locality + period. Deductions proportionate.
Government's typical weak ground: Deduction exceeds 53% (SC ceiling), no evidence of developmental potential.
Relevant statutes: Land Acquisition Act 1894 (Sections 4, 6, 11, 18, 23, 28, 34), 
  RFCTLARR Act 2013, Karnataka Land Acquisition Rules.""",
    "CRIMINAL": """
DOMAIN: Criminal Law
Identify whether this is: appeal against ACQUITTAL / appeal against CONVICTION / BAIL matter / SENTENCE revision
Focus questions for appeal against acquittal:
- Did SC reinstate conviction after HC acquittal? (Sets "perverse finding" standard)
- Was the finding of fact perverse (ignored documentary evidence, unreliable single witness)?
Government's typical strong ground (prosecution): Clear circumstantial evidence chain, medical/forensic corroboration.
Government's typical weak ground: Sole witness, delayed FIR, no independent corroboration.
Relevant statutes: IPC 1860 / BNS 2023, CrPC 1973 / BNSS 2023, Indian Evidence Act / BSA 2023,
  specific special acts (NDPS, POCSO, Prevention of Corruption).""",
    "CONSTITUTIONAL": """
DOMAIN: Constitutional / Administrative Law (Writ Jurisdiction)
Focus questions:
- Did SC hold that HC overstepped by directing executive policy (Article 226 limits)?
- Was there a fundamental rights violation finding that SC reversed on appeal?
- Does the precedent distinguish "religious function" from "state-sponsored cultural event"?
  (Relevant for Art. 25/26 challenges like the Gaurav case)
Government's typical strong ground: Legitimate state interest, rational nexus to public purpose, non-discriminatory.
Government's typical weak ground: Absolute prohibition of a fundamental right without proportionality.
Relevant provisions: Articles 12-35 (Fundamental Rights), Article 226 (HC writ), Article 136 (SLP),
  Wednesbury unreasonableness, Anisminic error of jurisdiction.""",
    "TAXATION": """
DOMAIN: Taxation (Income Tax / GST / Customs / State taxes)
Focus questions:
- Did SC hold that HC cannot re-examine ITAT/Tribunal's factual findings unless perverse?
- Did SC uphold tax demand despite procedural defects when the demand is otherwise valid?
- Was assessment within limitation under relevant Finance Act?
Government's typical strong ground: Tax demand within limitation, evidence of undisclosed income/unaccounted credit, 
  AO followed assessment procedure, CBDT circular supports position.
Government's typical weak ground: Assessment time-barred, CBDT circular directly contradicts demand,
  natural justice violated (no opportunity to respond before demand).
Relevant statutes: Income Tax Act 1961, CGST Act 2017, Customs Act 1962, Finance Acts (year-specific),
  Karnataka Value Added Tax Act, KVAT Rules.""",
    "MOTOR_VEHICLES": """
DOMAIN: Motor Vehicles / Accident Compensation (MACT)
Focus questions:
- Does the precedent apply Sarla Verma / Pranay Sethi multiplier table?
- Did SC correct multiplier misapplication (wrong age-bracket selection)?
- Did SC hold that future prospects addition is mandatory for employed victims?
Government's typical position: The government is usually the insurer's counsel or road authority.
  Challenge if: Wrong multiplier applied, speculative income, duplication of heads of compensation.
Government's typical weak ground: Sarla Verma/Pranay Sethi formula is now settled — cannot dispute it.
Relevant statutes: Motor Vehicles Act 1988 (Section 166, 168), Schedule II, 
  Pranay Sethi (2017) 16 SCC 680 (structured compensation heads).""",
    "LABOUR": """
DOMAIN: Labour / Industrial Disputes
Focus questions:
- Was domestic inquiry conducted and proved misconduct before dismissal?
- Did SC uphold reinstatement only when no inquiry was held, or even with flawed inquiry?
Government's typical strong ground (as employer): Valid domestic inquiry, misconduct proved, 
  proportionate punishment for proved misconduct.
Government's typical weak ground: No inquiry held, inquiry held but procedurally flawed,
  punishment grossly disproportionate (dismissal for minor misconduct).
Relevant statutes: Industrial Disputes Act 1947, Industrial Employment (Standing Orders) Act 1946,
  Karnataka Shops and Commercial Establishments Act, Payment of Wages Act 1936.""",
    "FAMILY_CIVIL": """
DOMAIN: Family / Civil / Matrimonial
Note: This domain has LOW RAG utility — precedents are fact-specific and rarely bind.
Focus: Identify whether the case involves a QUESTION OF LAW (precedent useful) or 
  pure facts (precedent not useful).
Government's typical role: None in family law. If present, likely as custodian of minors or land records.
Relevant statutes: Hindu Marriage Act 1955, Hindu Succession Act 1956, CPC 1908,
  Guardians and Wards Act 1890, Karnataka Scheduled Castes and Tribes (Prohibition of Transfer) Act.""",
    "COMMERCIAL": """
DOMAIN: Commercial / Contract / Arbitration / Procurement
Focus questions:
- Did SC uphold government's right to rescind contracts under force majeure / public interest?
- Was the tender/bid cancellation arbitrary (Article 14) or within discretion?
- Did SC interfere with arbitral awards on limited grounds (patent illegality, public policy)?
Government's typical strong ground: Policy decision to cancel tender, security clearance concerns,
  arbitral award patently illegal or contrary to public policy.
Government's typical weak ground: Tender conditions changed mid-bid without justification,
  procedurally arbitrary rejection of lowest bidder.
Relevant statutes: Arbitration and Conciliation Act 1996, Indian Contract Act 1872,
  Karnataka Transparency in Public Procurements Act 1999, KTPP Rules 2000.""",
    "ENVIRONMENTAL": """
DOMAIN: Environmental Law
Focus questions:
- Did SC apply the precautionary principle / polluter pays principle against the state?
- Did SC uphold forest diversion / land use change ordered by government?
- Was NGT's (National Green Tribunal) jurisdiction properly exercised?
Government's typical strong ground: Environmental clearance granted after due process, 
  Compensatory Afforestation done, public interest in the project.
Government's typical weak ground: No EIA conducted, clearance granted without public hearing,
  project in CRZ/forest without MOEF approval.
Relevant statutes: Environment Protection Act 1986, Forest Conservation Act 1980,
  Wildlife Protection Act 1972, Water Act 1974, NGT Act 2010, CRZ Notification."""
}


# AGENT 2 DOMAIN ADDITIONS
AGENT2_DOMAINS = {
    "SERVICE_LAW": """
DOMAIN-SPECIFIC APPEAL TRIGGERS — flag any of these if present:
- HC directed specific appointment/promotion without considering DPC recommendation → Appeal (usurps executive function)
- HC granted retrospective promotion creating precedent for entire cadre → Appeal urgently (financial impact)
- HC directed transfer to specific post → Appeal (transfers are administrative prerogative)
- Petitioner did not approach CAT before HC → Strong jurisdictional ground for appeal
- HC directed holding of DPC within weeks → Appeal if operationally impossible, or comply if simple
PRO-COMPLIANCE TRIGGERS:
- Original dismissal/punishment was without proper inquiry (Article 311 violation) → Comply
- Same cadre already gets the benefit elsewhere → Comply to avoid inequality claim""",
    "LAND_ACQUISITION": """
DOMAIN-SPECIFIC APPEAL TRIGGERS:
- Enhanced compensation more than 1.5× Reference Court award → Appeal (significant financial exposure)
- Deduction percentage reduced below 35% → Appeal (deductions within 35-53% are SC-approved)
- Interest awarded above Section 28/34 LAA rates → Appeal (statutory cap violation)
- Compensation awarded for land beyond what was actually acquired → Strong appeal
PRO-COMPLIANCE TRIGGERS:
- Accumulated interest (9% p.a.) over 3-5 year appeal period will exceed any potential saving → Comply
- Comparable sale deeds from the period were produced by petitioner → Comply
MATH NOTE: Reference the MATH VALIDATION REPORT if provided.""",
    "CRIMINAL": """
STATE (PROSECUTION) APPEAL TRIGGERS (against acquittal):
- HC reversed conviction by ignoring documentary/forensic evidence → Appeal ("perverse finding")
- HC applied wrong legal standard (e.g., required certainty instead of "beyond reasonable doubt") → Appeal
- Material witness not examined by HC → Appeal
STATE COMPLIANCE TRIGGERS:
- Accused acquitted on consistent version of events, no new evidence → Comply
- Retrial witnesses unavailable after years → Comply
- SC success rate for state appeals against acquittal is historically below 25% → Weight this heavily""",
    "CONSTITUTIONAL": """
APPEAL TRIGGERS:
- HC directed government to frame a scheme or policy within a deadline → Appeal (policy-making is executive function)
- HC struck down a government GO/notification without hearing all affected parties → Appeal
- HC extended fundamental right beyond its text (e.g., treated cultural event as religious function) → Appeal
- Single judge struck down a state law → Appeal to Division Bench (mandatory for constitutional validity)
COMPLIANCE TRIGGERS:
- HC found clear procedural violation with no remedy except compliance → Comply
- Discrimination is admitted with no rational basis → Comply
- Political controversy of appeal exceeds legal benefit → Comply (but note appeal option)""",
    "TAXATION": """
═══ MACRO-REVENUE / CASCADING-PRECEDENT RULE (overrides cost-benefit) ═══
A tax judgment is NEVER about just the petitioner before the court. The HC's
interpretation of any tax statute, GST notification, or exemption clause becomes
BINDING PRECEDENT across the entire state. Before applying the small-principal
→ COMPLY rule, check:

  Did the court INTERPRET a tax provision (statute / notification / circular)?
    → YES: APPEAL is MANDATORY, regardless of the individual petitioner's
            liability. Even ₹0 in this case = crores in state-wide revenue leakage.
            Do NOT write "minimal financial exposure", "isolated property",
            "small revenue impact". The exposure is the WHOLE TAX BASE.
    → NO (court only granted fact-specific waiver, sympathy relief, or set aside
       penalty without altering rule interpretation): The cost-benefit rule applies.

Concrete examples of MANDATORY-APPEAL statutory interpretation:
  • HC reads "residential dwelling" exemption to include commercial hostels
    (revenue leakage = every hostel operator in Karnataka)
  • HC interprets Rule 86A CGST as requiring pre-decisional hearing
    (revenue leakage = every credit-block dispute statewide)
  • HC holds a transaction is not "supply" under §7 CGST
    (revenue leakage = every similar transaction)
  • HC expands input tax credit eligibility beyond §16/17 limits
  • HC reads down a customs/excise notification's scope
  • HC quashes an assessment circular as ultra vires

Examples of FACTUAL-RELIEF (cost-benefit applies → COMPLY allowed):
  • HC waives penalty on natural justice grounds for ONE assessee
  • HC condones delay in filing return for ONE specific case
  • HC quashes a single assessment order for procedural defect
    (without re-interpreting the underlying provision)

APPEAL TRIGGERS:
- ANY judgment interpreting a tax provision against the State → APPEAL (see rule above)
- HC quashed on procedural grounds only; revenue demand is factually valid → Appeal
- HC allowed deduction not permitted by the specific section → Appeal
- Revenue loss > ₹10 lakh and legal error is identifiable → Appeal
COMPLIANCE TRIGGERS:
- Assessment was time-barred under the specific Finance Act provision → Comply
- CBDT/department's own circular contradicts the demand → Comply
- Natural justice clearly violated for ONE assessee, no statutory interpretation issue → Comply""",
    "MOTOR_VEHICLES": """
APPEAL TRIGGERS:
- Multiplier used is outside Sarla Verma/Pranay Sethi age table → Appeal on specific ground
- Future prospects added for deceased victim below 25 when not employed → Challenge
- Compensation for same head awarded twice (duplication) → Appeal only that part
COMPLIANCE TRIGGERS:
- Multiplier and income figures are within the SC formula → Comply
- Government (road authority) rarely wins delay appeals on quantum once formula applied → Comply
NOTE: Government win rate in MACT quantum appeals is very low. Comply unless clear formula error.""",
    "LABOUR": """
APPEAL TRIGGERS:
- Reinstatement ordered despite proved misconduct in valid inquiry → Appeal
- HC reduced punishment from dismissal to lesser penalty: assess if reinstatement creates organisational disruption → Appeal if yes
COMPLIANCE TRIGGERS:
- No domestic inquiry was conducted → Comply (SC consistently upholds reinstatement in this case)
- Inquiry was held but workman not allowed to cross-examine → Comply""",
    "FAMILY_CIVIL": "",
    "COMMERCIAL": """APPEAL TRIGGERS:
- HC interfering with tender cancellation on policy grounds → Appeal (SC gives wide discretion in procurement)
- HC set aside arbitral award beyond patent illegality / public policy grounds → Appeal
COMPLIANCE TRIGGERS:
- Tender conditions were changed mid-bid without justification → Comply
- Arbitral award is factually correct even if procedurally imperfect → Comply""",
    "ENVIRONMENTAL": """APPEAL TRIGGERS:
- HC stayed project despite valid environmental clearance on record → Appeal to DB with full EC record
- NGT order exceeded its own jurisdiction under NGT Act 2010 → Appeal to SC
COMPLIANCE TRIGGERS:
- EIA was not conducted or public hearing was skipped → Comply
- Project is in CRZ/forest without MOEF approval → Comply""",
    "GENERAL": ""
}

# AGENT 3 DOMAIN ADDITIONS
AGENT3_DOMAINS = {
    "SERVICE_LAW": """
ADDITIONAL RISKS:
- Reinstatement orders create ongoing salary liability from the date of reinstatement
- If reinstatement is stayed by appellate court, government avoids this liability during appeal
- Personal contempt is common in service cases — officers named in the order are personally at risk
- Check: Does the order name a specific Commissioner/Secretary? Their career is at risk for non-compliance.
- Check: Is the directed action time-bound (DPC to meet within 4 weeks)? Assess feasibility.""",
    "LAND_ACQUISITION": """
ADDITIONAL RISKS:
- Interest under Section 34 LAA (9% p.a.) on the difference between amount deposited and enhanced amount runs from date of award
- If Collector has not yet deposited the Reference Court amount: urgency is VERY HIGH (contempt AND interest)
- Delay in appeal = confirmed additional interest obligation with zero upside
- Government can obtain stay of enhanced compensation by depositing the Reference Court award and providing security for the difference
- Check: Has the Collector already deposited the original award? If yes, only the differential is at risk.""",
    "CRIMINAL": """
ADDITIONAL RISKS:
- Government cannot be held in contempt for filing appeal against acquittal: contempt risk = LOW
- If accused has been released: re-arrest after appeal is upheld is administratively complex
- If bail was granted by HC: government should apply for cancellation of bail simultaneously with appeal if accused is dangerous
- For Section 439 bail (serious offences): SLP should be filed within 7 days if accused is a flight risk""",
    "CONSTITUTIONAL": """
ADDITIONAL RISKS:
- Orders directing policy/scheme formulation have rolling contempt risk — each week of non-compliance worsens the situation
- If HC struck down a government notification: that notification is void immediately — government must act accordingly pending appeal
- Sensitive cases (religious, caste, gender): non-compliance generates reputational risk beyond legal risk
- Check: Is the HC order self-executing (e.g., "the GO is quashed") or directive (e.g., "the government shall within 3 months")?
  Self-executing orders require immediate compliance of the underlying action; directive orders allow time.""",
    "TAXATION": """
ADDITIONAL RISKS:
- Revenue permanently lost if appeal not filed within limitation — no condonation for revenue-side delay
- Pre-deposit requirement: Some tribunals require department to pre-deposit 20% of demand before appeal is heard
- If assessment quashed: refund + interest at 9% p.a. under Section 244A IT Act must be paid within 3 months
- AO who raised the erroneous demand may face ACR/departmental consequences → internal accountability risk""",
    "MOTOR_VEHICLES": """
ADDITIONAL RISKS:
- MACT awards carry interest at 9% p.a. from date of accident — every month of delay adds to government/insurer's liability
- Insurance company may have third-party direction against government (road defect) — separate liability head
- Contempt risk is MEDIUM: courts routinely issue notices for non-deposit of MACT awards""",
    "LABOUR": """
ADDITIONAL RISKS:
- Reinstatement without back wages still creates ongoing salary liability from date of order
- If workman was senior, reinstatement could displace another current employee
- Labour court/HC can attach government property for non-compliance of wage awards
- Check: Does the order include back wages for the entire period? This could be 5-10 years of salary — compute liability""",
    "FAMILY_CIVIL": "",
    "COMMERCIAL": """ADDITIONAL RISKS:
- Arbitral award: courts require pre-deposit before staying enforcement under Section 36 A&C Act
- Tender disputes: interim injunctions can halt ongoing projects — assess operational impact
- Government win rate in procurement writ appeals: ~55% — appeal often pays""",
    "ENVIRONMENTAL": """ADDITIONAL RISKS:
- NGT orders carry criminal penalties for non-compliance under NGT Act — contempt risk is HIGH
- HC stay on project = immediate halt of all site activity — financial bleeding per day
- Environmental clearance if quashed: entire project re-approval required — assess project viability""",
    "GENERAL": ""
}

# AGENT 4 DOMAIN ADDITIONS
AGENT4_DOMAINS = {
    "SERVICE_LAW": """
SERVICE LAW OVERLAY:

═══ CASCADING-EFFECT GUARDRAIL ═══
Service Law judgments rarely affect only the petitioners in court — they typically extend to the
entire cadre/sub-cadre. Before deciding APPEAL vs COMPLY:
  1. Ask: "Does this ratio bind the State for ALL similarly-placed employees?"
  2. If yes, the real financial liability is the cadre-wide cost, not just the petitioners.
  3. Despite the cascading cost, DO NOT recommend APPEAL when the ratio is already settled by
     the Supreme Court (e.g., KPTCL v. C.P. Mundinamani for terminal increments). An SLP against
     settled SC law will be DISMISSED IN LIMINE and waste public funds.
  4. Frame primary_reasoning as: "Although cascading liability is significant, the SC has settled
     this question — appeal is futile. COMPLY."

═══ DOMAIN RULES ═══
- Appeal against reinstatement orders where no inquiry was conducted → NOT recommended (virtually never succeeds at SC)
- Appeal against retrospective promotion orders → STRONGLY recommended UNLESS settled by SC against the State
- For transfer/posting orders → COMPLY almost always (transfer is government's right; appeal rarely succeeds)
- For orders directing DPC within specific weeks → File a representation; appeal only if operationally impossible
- Government win rate in service law HC writ appeals: ~38%

═══ CONTEMPT URGENCY ═══
Service Law orders almost always carry a deadline (e.g., "Compliance within eight weeks").
ANY service-law order with a deadline + compliance verb is CONTEMPT RISK = HIGH. Named officers
(Secretary, Commissioner, Director) are personally exposed if the deadline slips.""",
    "LAND_ACQUISITION": """
LAND ACQUISITION OVERLAY:

═══ MATH TRAP GUARDRAIL (mandatory) ═══
If the EXTRACTED FINANCIAL FIGURES block or the NUMBERS DETECTED IN OPERATIVE ORDER block
contains ANY rupee amounts or percentages, you MUST:
  1. Cite the specific number(s) in primary_reasoning.
  2. NEVER write "no financial exposure", "no financial data is provided",
     or "no specific amounts" — the numbers are right there. Read them.
  3. Compute or estimate principal exposure from those numbers.
  4. Compare against interest accrual at 9% p.a. (Section 28/34 LAA) over 3-5 years.

═══ DIRECTIONAL MATH (don't argue against the State's interest) ═══
- Deduction % HIGHER = LESS payout = GOOD for State. Never argue a deduction is "too high".
- Government's appeal grounds on deduction should always argue deduction should be HIGHER, not lower.
- A 53% deduction is the SC-approved ceiling (Lal Chand v. Union). If HC applied 53%, the State
  has LOCKED IN the maximum legal deduction — APPEALING risks the SC reducing it. COMPLY.
- A 30-35% deduction is on the low end — the State has appeal merit to push it higher.

Mathematical benchmarks:
- If enhanced compensation <= 20% above Reference Court award: COMPLY (interest will exceed saving)
- If enhanced compensation >= 50% above Reference Court award: APPEAL (significant exposure)
- If deduction is AT or NEAR the 53% SC ceiling: COMPLY — appeal could only worsen the State's position
- Always: Government can deposit Reference Court award and give court security for the balance,
  allowing appeal without contempt risk. Recommend this route.
- Government win rate in land acquisition compensation appeals: ~45%""",
    "CRIMINAL": """
CRIMINAL LAW OVERLAY:

═══ STATE-AS-APPELLANT INVERSION TRAP ═══
In criminal appeals the State is FREQUENTLY the APPELLANT (e.g., appeal against acquittal,
appeal against quashing of FIR under §482 CrPC, prosecution challenges).
  • Use the GOVERNMENT ROLE block in case details — NOT just the disposition word.
  • If GOVERNMENT ROLE = GOVT_LOST, the State LOST, even if disposition is "Dismissed".
  • Never write "the State prevailed" when GOVT_LOST is set.

═══ FUTILITY-OF-APPEAL CHECK ═══
Before recommending APPEAL in a criminal matter, verify:
  • Is the HC order based on SETTLED Supreme Court precedent (e.g., Aneeta Hada, B. Jayaraj,
    Sharad Birdhichand Sarda)? If yes → COMPLY. SLPs against settled SC law are dismissed in limine.
  • Did the State fail on a PROCEDURAL defect (e.g., failure to arraign the company under
    vicarious liability, hostile star witness, no independent corroboration)? If yes → COMPLY.
    Re-filing a properly-drafted complaint (within limitation) is a better remedy than SLP.

═══ DOMAIN RULES ═══
- State appeal against acquittal: COMPLY unless HC finding is demonstrably perverse
  (SC success rate for state in acquittal reversal: <20%)
- State opposing bail: If accused is a serious/repeat offender → APPEAL. Otherwise → COMPLY.
- For sentence reduction orders: Appeal only if sentence is shockingly lenient for the offence
- Government win rate in criminal appeals: ~22% (low — courts protect personal liberty)

═══ CONTEMPT URGENCY ═══
HC orders dismissing State appeals or quashing FIRs almost never contain
affirmative directives against the State. Contempt Risk = LOW unless the order
explicitly directs the State to do something with a deadline.""",
    "CONSTITUTIONAL": """
CONSTITUTIONAL LAW OVERLAY:

═══ DISMISSED ≠ COMPLY (UI nuance) ═══
When a constitutional writ petition is DISMISSED, the State has WON. There are no directions to
"comply with" — there is nothing for the department to do. In this case:
  • verdict.decision = COMPLY  (the closest enum value)
  • primary_reasoning MUST explicitly state: "The petition was dismissed; no directions issued
    against the State. No compliance action is required — the file may be CLOSED."
  • appeal_grounds = [] (do NOT invent grounds)
  • Contempt Risk = LOW (no directives exist)
  • Confidence: 0.90+

═══ DOMAIN RULES ═══
- HC order directing policy within a time frame → APPEAL (preserves executive space; near-certain success at DB)
- HC striking down state law → APPEAL IMMEDIATELY (constitutional validity requires DB hearing)
- Art. 25/26 religious freedom cases: Government must show the event is state-sponsored and secular in character
  (Gaurav case: Dasara festival organized by the State, not by the temple trust → state can choose chief guest freely)
- Government win rate in constitutional writ appeals: ~52% (above average, courts respect executive policy)""",
    "TAXATION": """
TAXATION OVERLAY:

═══ MACRO-REVENUE RULE (HARD OVERRIDE — applies before cost-benefit) ═══
If THIS COURT'S judgment INTERPRETS any tax provision (statute, notification, circular, rule)
against the State, you MUST recommend APPEAL — even when the individual petitioner's
financial liability is small or zero. Reasoning template:

  "Although the petitioner's individual liability is only ₹X, the court's interpretation
   of [provision] becomes binding precedent for all similarly-situated taxpayers in
   Karnataka, creating massive statewide revenue leakage. The cost-of-delay calculus
   that applies to ordinary monetary judgments does NOT apply here — protecting the
   state's tax base requires immediate appeal regardless of the principal in this case."

Do NOT write "minimal exposure", "small revenue impact", "isolated property",
"single taxpayer" when the court has interpreted a tax provision. Those phrases are
the diagnostic signature of the Macro-Revenue Trap and a 70B-quality recommendation
will never use them in a statutory-interpretation case.

═══ DOMAIN RULES ═══
- ANY statutory-interpretation case against the State → APPEAL is mandatory
- ALWAYS file a protective appeal if revenue loss > ₹10 lakh (revenue cannot condone delay)
- HC quashed assessment on procedural ground only: APPEAL (~65% success)
- HC reversed ITAT finding of undisclosed income: APPEAL (factual findings should not be re-examined)
- HC found assessment time-barred (correctly): COMPLY (cannot win on this)
- HC waives penalty for ONE assessee on natural-justice grounds, no precedent on interpretation: COMPLY
- Government (revenue) win rate in IT/GST appeals: ~48%""",
    "MOTOR_VEHICLES": """
MOTOR VEHICLES OVERLAY:
- MACT quantum appeals by government/insurer have very low success rate (~15-20%)
- COMPLY unless: wrong multiplier applied (verifiable from Pranay Sethi table), or duplication of heads
- If staying the award: court will require deposit of 50% of awarded amount → assess if worth it
- Never appeal a MACT award on ground that victim was partially negligent — contributory negligence must be raised at MACT stage
- Government win rate in MACT quantum appeals: ~18% (recommend COMPLY in most cases)""",
    "LABOUR": """
LABOUR LAW OVERLAY:
- Reinstatement without inquiry: COMPLY (SC has settled this — inquiry is mandatory before dismissal)
- Reinstatement with proved misconduct: APPEAL (only valid domestic inquiry protects the order)
- Back wages: Courts often award full back wages — if no inquiry, comply on reinstatement AND back wages
- For ongoing liability: Calculate total back wages + future salary and weigh against appeal costs
- Government win rate in reinstatement appeals: ~40% (only when valid domestic inquiry exists)""",
    "FAMILY_CIVIL": """
FAMILY/CIVIL OVERLAY:
- Government is rarely a party. If present as a record keeper or land-grant authority:
  Comply with any procedural directions about records.
- In partition/succession disputes involving government land grants:
  Appeal if title is disputed without examining original grant records.
- For maintenance orders where state is custodian of funds: Comply promptly — courts are strict.""",
    "COMMERCIAL": """
COMMERCIAL/PROCUREMENT OVERLAY:
- HC interfering with tender cancellation: APPEAL if decision was on policy grounds
  (SC gives wide discretion to government in procurement decisions — high success rate ~60%)
- Arbitral award against government: APPEAL only on "patent illegality" or "public policy" grounds
  (post-BALCO, courts have narrow review of arbitral awards)
- Government win rate in procurement disputes: ~55% (best domain for government — appeal often pays)""",
    "ENVIRONMENTAL": """
ENVIRONMENTAL OVERLAY:
- HC staying government project on environmental grounds: APPEAL to DB with full environmental clearance record
- NGT orders: Challenge before SC if NGT exceeded jurisdiction or applied wrong standard
- Precautionary principle: Government must show adequate safeguards were adopted — if not, COMPLY
- Government win rate in environmental challenges: ~35% (courts apply high scrutiny — compliance is often more strategic)""",
    "GENERAL": ""
}

def build_agent_prompt(agent_num: int, domain_key: str, universal_task: str) -> str:
    """Builds the prompt by combining universal instructions with domain overlays."""
    prompt = universal_task
    
    domain_overlay = ""
    if agent_num == 1:
        domain_overlay = AGENT1_DOMAINS.get(domain_key, "")
    elif agent_num == 2:
        domain_overlay = AGENT2_DOMAINS.get(domain_key, "")
    elif agent_num == 3:
        domain_overlay = AGENT3_DOMAINS.get(domain_key, "")
    elif agent_num == 4:
        domain_overlay = AGENT4_DOMAINS.get(domain_key, "")
        
    if domain_overlay:
        prompt += f"\n\n{domain_overlay}"
        
    return prompt
