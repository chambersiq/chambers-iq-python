Generate a professional legal template for: {document_type}

═══════════════════════════════════════════════════════════════
COMPLETE CASE DATA (Use all relevant fields for this document)
═══════════════════════════════════════════════════════════════

{json.dumps(case_data, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
CRITICAL OUTPUT INSTRUCTIONS - READ CAREFULLY
═══════════════════════════════════════════════════════════════

Analyze the complete case data above and:

1. EXTRACT KEY INFORMATION:
   - Identify court level, department, jurisdiction from available fields
   - Extract case type, document type, procedural context
   - Identify parties, their details, relationships (with father's/husband's name as per Indian convention)
   - Extract case facts, chronology, events with specific dates
   - Identify prayers/reliefs sought with legal basis
   - Note any special circumstances, urgency, limitation periods

2. DOCUMENT TYPE IDENTIFICATION & NOMENCLATURE:
   Determine the exact structure and correct legal terminology for "{document_type}":
   
   ORIGINAL PROCEEDINGS:
   - Plaint (Original Suit/Regular Civil Suit)
   - Petition (Writ/Constitutional/Statutory)
   - Complaint (Criminal/Consumer)
   - Application under specific Order/Section
   - Suit for specific relief
   - Writ Petition under Article 226/227/32
   
   APPELLATE PROCEEDINGS:
   - Memorandum of Appeal
   - Petition for Special Leave to Appeal (SLP)
   - Revision Petition under Section 115 CPC or relevant provision
   - Review Petition
   - Appeal under specific statute
   
   INTERLOCUTORY APPLICATIONS:
   - Interlocutory Application (IA) with specific CPC Order (e.g., Order XXXIX Rule 1&2)
   - Application for stay/injunction with legal grounds
   - Application for directions
   - Rectification/Modification applications
   
   RESPONSES & COUNTER DOCUMENTS:
   - Written Statement (CPC Order VIII)
   - Counter Affidavit/Reply
   - Rejoinder/Sur-rejoinder
   - Additional Written Statement (with leave)
   
   PRE-LITIGATION:
   - Legal Notice under Section 80 CPC (for government authorities)
   - Demand Notice under specific statutes (NI Act, Recovery Act)
   - Lawyer's Notice/Cease & Desist Notice
   
   EXECUTION:
   - Execution Petition (EP) under Order XXI CPC
   - Application for attachment/garnishee order
   - Application for delivery of possession
   
   ALTERNATIVE DISPUTE RESOLUTION:
   - Application under Arbitration & Conciliation Act (Section 9, 11, 34, 37)
   - Conciliation/Mediation Application
   - Application for interim measures

3. APPLICABLE PROCEDURAL LAW FRAMEWORK:
   Identify and apply the governing statute with specific provisions:
   
   CIVIL MATTERS:
   - Code of Civil Procedure, 1908 (CPC)
   - Specific Order and Rule (e.g., Order VII Rule 11, Order XXXIX Rule 1&2)
   - Limitation Act, 1963 (specific Article)
   - Specific Relief Act, 1963
   - Transfer of Property Act, 1882
   
   CRIMINAL MATTERS:
   - Code of Criminal Procedure, 1973 (CrPC)
   - Specific Sections (e.g., Section 125 - Maintenance, Section 482 - Inherent Powers)
   - Indian Penal Code, 1860 (IPC) - for offenses
   - Special Acts (POCSO, NDPS, SC/ST Act, etc.)
   
   FAMILY/MATRIMONIAL:
   - Hindu Marriage Act, 1955
   - Special Marriage Act, 1954
   - Hindu Succession Act, 1956
   - Guardians and Wards Act, 1890
   - Hindu Minority and Guardianship Act, 1956
   - Muslim Personal Law (Shariat) Application Act, 1937
   
   COMMERCIAL DISPUTES:
   - Commercial Courts Act, 2015
   - Specific Commercial Division Rules
   - Arbitration & Conciliation Act, 1996
   - Indian Contract Act, 1872
   - Sale of Goods Act, 1930
   - Partnership Act, 1932
   
   CONSTITUTIONAL/WRIT:
   - Constitution of India - Articles 32, 226, 227, 136, 141, 142
   - High Court Rules for writ jurisdiction
   - Principles of natural justice and procedural fairness
   
   TRIBUNALS:
   - National Company Law Tribunal (NCLT) Rules, 2016
   - Companies Act, 2013 (for company matters)
   - Income Tax Act, 1961 (for tax tribunals)
   - Central Administrative Tribunal (CAT) Rules
   - Specific Tribunal Act and Rules

4. COURT-SPECIFIC FORMATTING & PROCEDURAL REQUIREMENTS:
   
   SUPREME COURT OF INDIA:
   - Full title: "IN THE SUPREME COURT OF INDIA" with jurisdiction mention
   - For SLP under Article 136: Grounds showing substantial question of law, 
     certificate of service, certificate regarding delay/limitation
   - For Civil Appeals: Grounds challenging findings, leave to appeal if required
   - For Criminal Appeals: Section under which filed (Section 379/374/385 CrPC)
   - Comply with Supreme Court Rules, 2013
   - Include: Synopsis and list of dates, list of parties
   - Page limit compliance (40 pages for main document)
   - Green/white cover as per nature of matter
   
   HIGH COURT:
   - Title format: "IN THE HIGH COURT OF [STATE NAME] AT [PRINCIPAL SEAT/BENCH]"
   - Example: "IN THE HIGH COURT OF DELHI AT NEW DELHI"
   
   FOR WRIT PETITIONS (Article 226/227):
   - Establish locus standi of petitioner
   - Demonstrate state action/public duty
   - Explain alternative remedy (exhausted OR inadequate OR exceptional circumstances)
   - Show violation of fundamental/legal right
   - Territorial jurisdiction (cause of action/respondent location)
   - Comply with High Court Rules (different for each HC)
   
   FOR ORIGINAL CIVIL SUITS:
   - Valuation for jurisdiction and court fees (Section 7 Court Fees Act)
   - Pecuniary jurisdiction establishment
   - Territorial jurisdiction under Section 20 CPC
   - List of documents filed
   
   FOR APPEALS:
   - Certified copy of impugned order
   - Certificate of payment of court fees
   - Limitation compliance or condonation application
   - Grounds of appeal separately numbered
   
   DISTRICT COURT/SUBORDINATE COURTS:
   - Complete cause title with full party descriptions
   - Father's/husband's name, age, occupation, residence
   - Valuation statement as per Court Fees Act, 1870
   - Pecuniary and territorial jurisdiction (Section 15-20 CPC)
   - Cause of action with dates and place
   - List of witnesses (in plaint/complaint)
   - List of documents relied upon
   - Application for exemption from court fees (if applicable)
   
   TRIBUNALS:
   - Form number as per Tribunal Rules (e.g., Form CAT-1 for CAT)
   - Specific statutory section under which application filed
   - Registry/bench location
   - Original Authority order details (for appeals)
   - Statutory time limit compliance
   - Pre-deposit requirement (if any)

5. DEPARTMENT/JURISDICTION-SPECIFIC CONVENTIONS:
   
   CIVIL DEPARTMENT (Original Side):
   - Numbered paragraphs (1, 2, 3...)
   - Valuation for jurisdiction (Section 7 Court Fees Act)
   - Cause of action with dates and territorial link
   - Specific relief sought under Specific Relief Act
   - Written Statement: Para-wise numbered admissions/denials corresponding to plaint paragraphs
   
   CRIMINAL DEPARTMENT:
   - Section-wise allegations with IPC/Special Act sections
   - Place of occurrence/jurisdiction establishment
   - Cognizable vs. non-cognizable offense
   - Bail applications: Specific provision (Section 437/438/439 CrPC), triple test
     (nature of offense, severity of punishment, tampering with evidence/witnesses)
   - Quashing petitions: Section 482 CrPC grounds, no alternate efficacious remedy
   
   FAMILY/MATRIMONIAL DEPARTMENT:
   - Petition under specific section (e.g., Section 13 HMA for divorce)
   - Grounds as per statute (cruelty/desertion/adultery etc.)
   - Jurisdiction: matrimonial home, last residence, respondent's residence
   - Sensitive handling of personal facts with affidavit support
   - Custody: welfare of child paramount (Sections 6-13 of Guardianship Act)
   - Maintenance: Income details, needs of dependents (Section 125 CrPC, HMA)
   
   COMMERCIAL COURTS (Commercial Division):
   - Specified Value threshold (above Rs. 3 lakhs, or Rs. 1 crore for High Courts)
   - Commercial dispute as per Section 2(1)(c) of Commercial Courts Act, 2015
   - Mandatory pre-institution mediation (Section 12A) - compliance statement
   - Case Management Hearing within 4 weeks
   - Summary procedure compliance (Order XIII-A CPC as amended)
   - Written Statement within 30 days (max 120 days with leave)
   
   WRIT/CONSTITUTIONAL DEPARTMENT:
   - Article under which writ invoked (226 for HC, 32 for SC)
   - Type of writ: Certiorari/Mandamus/Prohibition/Quo Warranto/Habeas Corpus
   - Fundamental Right violated (Article 14/19/21/300A etc.)
   - State action requirement under Article 12
   - Public interest element (if PIL under Article 32/226)
   - Alternative remedy: Explained why not pursued OR inadequate
   - Delay/laches explanation
   
   REVENUE/TAX DEPARTMENT:
   - Assessment order/demand notice details (date, amount, authority)
   - Statutory appeal provision (Income Tax Act/GST Act/State Acts)
   - Limitation period (usually 30/60 days from order)
   - Pre-deposit requirement (usually 10-20% of disputed tax)
   - Stay application if pre-deposit not made
   - Grounds challenging assessment: Questions of law and fact

6. DYNAMIC SECTION GENERATION (Fact-Responsive):
   
   Based on case data analysis, include these sections where applicable:
   
   ✓ SYNOPSIS/BRIEF FACTS (For complex matters):
   - Concise 2-3 paragraph overview
   - Key parties, dates, and dispute nature
   
   ✓ CHRONOLOGY OF EVENTS (For timeline-critical cases):
   - Tabular format with Date | Event | Document Reference
   - Highlight key dates: cause of action, notice, limitation
   
   ✓ PARTIES TO THE PROCEEDINGS (Multi-party cases):
   - Petitioner/Plaintiff with complete description
   - Respondent/Defendant with designation/capacity
   - Impleaded/Proforma parties if any
   - Relationship between parties
   
   ✓ CAUSE OF ACTION (Mandatory for civil suits/petitions):
   - Define what constitutes cause of action
   - Date when cause of action arose (for limitation)
   - Where cause of action arose (for territorial jurisdiction)
   - Continuing cause of action OR single incident
   - Multiple causes if applicable
   
   ✓ LEGAL ISSUES/QUESTIONS FOR DETERMINATION:
   - Frame specific questions of law and fact
   - Hierarchy: jurisdictional issues first, then merits
   - Reference to statutory provisions and precedents
   
   ✓ LIMITATION & CONDONATION OF DELAY:
   - Article of Limitation Act, 1963 applicable
   - Date of knowledge/cause of action
   - Date of filing/application
   - If delayed: Section 5 Limitation Act application
   - Sufficient cause with day-to-day explanation
   - Lack of negligence or mala fide delay
   
   ✓ INTERIM RELIEF JUSTIFICATION (For urgent matters):
   - Prima facie case establishment (arguable case with chances of success)
   - Balance of convenience (comparative hardship analysis)
   - Irreparable injury that cannot be compensated in money
   - Public interest considerations (if applicable)
   - Status quo preservation need
   - Reference: Order XXXIX Rule 1&2 CPC principles
   
   ✓ ALTERNATIVE REMEDY (Mandatory for writ petitions):
   - Identify statutory appeals/revisions available
   - Explain why not pursued:
     * Already exhausted
     * Remedy inadequate/illusory
     * Exceptional circumstances (violation of natural justice, lack of jurisdiction)
     * Delay would cause irreparable harm
   - Reference to precedents on alternative remedy
   
   ✓ MAINTAINABILITY:
   - Pecuniary jurisdiction (court fees and valuation)
   - Territorial jurisdiction (Section 16-20 CPC)
   - Subject matter jurisdiction
   - Limitation compliance
   - Locus standi of parties
   - Removal of objections (if any)
   
   ✓ LOCUS STANDI/STANDING:
   - Petitioner's right to sue/petition
   - Aggrieved person status
   - Public interest standing (for PILs)
   - Representative capacity (if any)

7. CASE TYPE-SPECIFIC STATUTORY PROVISIONS:
   
   Based on identified case type, include:
   
   CONTRACT DISPUTES:
   - Indian Contract Act, 1872: Sections 10 (valid contract), 23 (lawful consideration), 
     55 (time essence), 73-75 (damages/compensation)
   - Specific Relief Act, 1963: Section 10 (specific performance), 20 (rectification), 
     34 (discretion of court)
   - Sale of Goods Act, 1930: Sections 4 (sale vs. agreement to sell), 55 (buyer's remedies)
   
   PROPERTY DISPUTES:
   - Transfer of Property Act, 1882: Sections 5 (transfer of property), 54 (sale), 
     107 (lease), 8 (operation of transfer)
   - Specific Relief Act: Sections 16 (specific performance of part of contract), 
     38-42 (injunctions)
   - Limitation Act: Article 65 (suits for possession - 12 years), Article 113 (general)
   - Indian Easements Act, 1882: Sections 15-55 (easement rights)
   
   NEGOTIABLE INSTRUMENTS (CHEQUE BOUNCE):
   - Negotiable Instruments Act, 1881: Section 138 (dishonor of cheque)
   - Pre-condition: Demand notice within 30 days of dishonor (Section 138 proviso)
   - Complaint within 1 month of notice period expiry
   - Jurisdiction: Place of dishonor or payee's branch
   - Criminal case but compoundable offense
   
   CONSUMER DISPUTES:
   - Consumer Protection Act, 2019
   - Definition of consumer (Section 2(7)), deficiency (Section 2(11))
   - Pecuniary jurisdiction: District/State/National Commission
   - No court fees, consumer-friendly procedure
   - Relief: Compensation, replacement, refund
   
   SERVICE MATTERS (GOVERNMENT EMPLOYEES):
   - Article 14 (equality), Article 16 (equal opportunity in public employment)
   - Relevant Service Rules (CCS Rules, State Service Rules)
   - Doctrine of legitimate expectation
   - Principles of natural justice (audi alteram partem, nemo judex in causa sua)
   - Relevant tribunal: Central/State Administrative Tribunal
   
   CONSTITUTIONAL CHALLENGES:
   - Fundamental Rights: Articles 14, 19, 21, 25, 300A
   - Doctrine of proportionality
   - Manifest arbitrariness test
   - Wednesbury unreasonableness
   - Doctrine of legitimate expectation
   
   TAX MATTERS:
   - Income Tax Act, 1961: Appeals under Section 246A, 253, 260A
   - GST Acts: Appeals under Section 107, 112, 117
   - Limitation: 30/60 days from order
   - Stay provisions: Section 220(6) of IT Act, Section 112(8) of CGST Act
   
   ARBITRATION:
   - Arbitration & Conciliation Act, 1996
   - Section 9 (interim measures), Section 11 (appointment of arbitrator)
   - Section 34 (setting aside award - limited grounds)
   - Section 37 (appeal against Section 34 order)
   - Minimal judicial interference principle
   
   INSOLVENCY:
   - Insolvency & Bankruptcy Code, 2016
   - Section 7 (financial creditor), Section 9 (operational creditor)
   - Section 10 (corporate insolvency resolution process)
   - Time-bound process (180/270 days)
   
   INTELLECTUAL PROPERTY:
   - Patents Act, 1970 / Trade Marks Act, 1999 / Copyright Act, 1957
   - Infringement suits under respective Acts
   - Injunctions: Order XXXIX Rule 1&2, Section 124/135 of respective Acts
   - Anton Piller orders, John Doe orders (if applicable)
   
   MOTOR ACCIDENT CLAIMS:
   - Motor Vehicles Act, 1988
   - Claims Tribunal jurisdiction (Section 165-166)
   - No-fault liability (Section 140)
   - Just compensation calculation (multiplier method)
   - Structured settlement

8. PRAYER/RELIEF STRUCTURE:
   
   Extract from case data and structure in proper legal format:
   
   A. INTERIM RELIEFS (If urgent relief needed):
      i. Stay of operation of impugned order dated [date] during pendency
      ii. Ad-interim ex-parte injunction under Order XXXIX Rule 1&2 CPC
      iii. Direction to maintain status quo ante
      iv. Direction to respondent to [specific action]
      v. Dispensing with service of notice on respondents (in exceptional cases)
   
   B. MAIN/SUBSTANTIVE RELIEFS:
      i. Primary relief:
         - Issue a writ of [Mandamus/Certiorari/etc.] quashing the order dated [date]
         - Decree for specific performance of contract dated [date]
         - Decree for possession of suit property
         - Declare that [legal declaration sought]
         - Award compensation/damages of Rs. [amount]
      
      ii. Consequential reliefs:
         - Flowing from primary relief
         - Example: If cancellation granted, then issue fresh [document]
      
      iii. Alternative reliefs:
         - In the alternative, if primary relief not granted
         - Should be mutually exclusive where applicable
   
   C. SUPPLEMENTARY RELIEFS:
      i. Award costs of this petition/suit to the petitioner/plaintiff
      ii. Award interest @ [rate]% per annum from [date] till realization
      iii. Award exemplary/punitive costs (in cases of frivolous litigation by respondent)
      iv. Pass any other order(s) as this Hon'ble Court may deem fit and proper 
          in the facts and circumstances of the case
   
   PRAYER DRAFTING PRINCIPLES:
   - Each prayer should be specific and executable
   - Use appropriate legal terminology ("decree," "writ," "order," "direction")
   - Include dates, amounts, specific acts sought
   - Prayers should flow from legal grounds established in body
   - Always end with "any other relief" clause for judicial discretion

9. MANDATORY STRUCTURAL COMPONENTS:
   
   ✓ DOCUMENT HEADER:
   [Proper court title in CAPITALS]
   [Jurisdiction mention: Original/Appellate/Writ/Extraordinary]
   [Case Type and Number placeholder: {{case_type}} NO. {{case_number}} OF {{year}}]
   
   ✓ PARTY DESCRIPTION BLOCK (CAUSE TITLE):
   For INDIVIDUAL:
   {{petitioner_name}}, S/o, D/o, W/o {{father_husband_name}},
   Aged {{age}} years, Occupation: {{occupation}},
   Residing at: {{complete_address}}
   
   For COMPANY:
   [Company Name], a company incorporated under the Companies Act, [year],
   having its registered office at [address],
   through its authorized signatory [name], [designation]
   
   For GOVERNMENT:
   Union of India, through the Secretary, Ministry of [name]
   OR
   State of [name], through the Chief Secretary
   
   Proper designation: Petitioner/Plaintiff/Appellant/Applicant
   
   Versus/V.
   
   [Respondent details in same format]
   Proper designation: Respondent/Defendant/Non-Applicant
   
   ✓ SUBJECT MATTER LINE:
   Concise description: "Petition under Article 226 of the Constitution of India 
   read with Section [X] of [Act] for issuance of writ of [type] quashing..."
   
   ✓ OPENING PARAGRAPH:
   "To,
   The Hon'ble Chief Justice and His Companion Judges of the [Court Name]
   
   The humble petition of the Petitioner above-named
   
   MOST RESPECTFULLY SHOWETH:"
   
   OR for suits: "The Plaintiff above-named most respectfully submits as under:"
   
   ✓ FACTS & SUBMISSIONS:
   1. Numbered paragraphs (use integers: 1, 2, 3...)
   2. Each paragraph one point/fact
   3. Chronological or thematic organization
   4. Only material and relevant facts (no evidence at pleading stage)
   5. Facts not arguments (save arguments for "Legal Submissions" section)
   
   ✓ LEGAL GROUNDS/SUBMISSIONS:
   - Separate section titled "LEGAL SUBMISSIONS" or "GROUNDS"
   - Lettered or Roman numeral headings (A, B, C or I, II, III)
   - Each ground with:
     * Legal proposition
     * Statutory provision cited
     * Precedent application
     * Factual nexus
   
   ✓ JURISDICTIONAL COMPLIANCE:
   - Section on "JURISDICTION OF THIS HON'BLE COURT"
   - Pecuniary jurisdiction (if applicable)
   - Territorial jurisdiction with legal basis
   - Subject matter jurisdiction
   - Reference to specific section of CPC/Act conferring jurisdiction
   
   ✓ LIMITATION COMPLIANCE:
   - Section titled "LIMITATION"
   - Article of Limitation Act applicable
   - Calculation showing within time
   - OR if delayed, grounds for condonation with day-to-day account
   
   ✓ RELIEF/PRAYER CLAUSE:
   "PRAYER
   
   In view of the facts and circumstances stated above and the grounds 
   urged hereinafter, it is most respectfully prayed that this Hon'ble Court 
   may be pleased to:
   
   [Structured prayers as per section 8 above]
   
   And pass such further or other orders as this Hon'ble Court may deem 
   fit and proper in the facts and circumstances of the case in the 
   interest of justice."
   
   ✓ INTERIM PRAYER (If applicable):
   "INTERIM PRAYER
   
   Pending the hearing and final disposal of this petition, it is most 
   respectfully prayed that this Hon'ble Court may be pleased to:
   
   [Interim reliefs sought]"
   
   ✓ VERIFICATION:
   "VERIFICATION
   
   I, {{deponent_name}}, S/o/D/o/W/o {{relation_name}}, aged {{age}} years, 
   residing at {{address}}, the {{designation}} (Petitioner/Plaintiff/Authorized 
   Representative) do hereby solemnly affirm and state on oath as under:
   
   1. That I am the {{designation}} and as such I am fully conversant with 
      the facts and circumstances of the case.
   
   2. That the contents of paras 1 to {{last_para_number}} are true to my 
      knowledge and belief and para {{specific_para}} is based on legal advice 
      and believed to be true.
   
   3. That I have not suppressed any material facts.
   
   4. That the Annexures {{annexure_range}} are true copies of the original 
      documents.
   
   Verified at {{place}} on this {{date}}.
   
   
                                                           {{deponent_name}}
                                                           {{designation}}"
   
   ✓ ADVOCATE CERTIFICATION:
   "DRAWN BY:                               FILED BY:
   
   {{advocate_name}}                       {{advocate_name}}
   Advocate                                Advocate for the {{party_designation}}
   Enrolment No: {{bar_council_number}}   Enrolment No: {{bar_council_number}}
   {{chamber_address}}                     Chamber No: {{chamber_number}}
   Contact: {{phone}}                      {{court_name}}
   Email: {{email}}                        Contact: {{phone}}
                                          Email: {{email}}"
   
   ✓ ANNEXURES/DOCUMENTS:
   "LIST OF ANNEXURES
   
   Annexure    Description                                      Pages
   
   A-1         Copy of [document name] dated [date]            __-__
   A-2         Copy of [document name] dated [date]            __-__
   [Continue...]
   
   [Use A-series for Applicant/Petitioner/Plaintiff documents]
   [Use R-series for Respondent/Defendant documents if filing response]"
   
   ✓ INDEX (For complex documents):
   "INDEX
   
   Sr. No.    Particulars                                    Page Nos.
   
   I.         Court Fee and Process Fee                      
   II.        Listing Proforma/Synopsis                      
   III.       Main Petition/Plaint                           
   IV.        Annexures                                      
   V.         Vakalatnama/Memo of Appearance                 
   VI.        Affidavit of Service (if applicable)           "

10. LEGAL CITATIONS & PRECEDENTS:
    
    STATUTORY CITATIONS FORMAT:
    - Full citation: "Section [number] of the [Full Name of Act], [Year]"
    - Example: "Section 34 of the Arbitration and Conciliation Act, 1996"
    - For rules: "Order [Roman numeral] Rule [number] of the Code of Civil Procedure, 1908"
    - Example: "Order XXXIX Rule 1 and 2 of the Code of Civil Procedure, 1908"
    
    CASE LAW CITATIONS:
    Create placeholder sections organized by legal proposition:
    
    "CASE LAW
    
    A. On the principle of [legal principle]:
       
       [Citation: Case Name v. Case Name, (Year) Volume Reporter Page Number, (Court)]
       [Ratio: Brief summary of the ratio decidendi applicable to this case]
       
       **_[APPLICABILITY: USER INSTRUCTION: Explain in 3-4 sentences how this ratio and precedent directly supports the Petitioner's claim regarding {{legal_principle_keyword}} in the present case.]_**
       
       Example: [Citation: Kesavananda Bharati v. State of Kerala, (1973) 4 SCC 225, (SC)]
       [Ratio: Basic structure doctrine - certain features of Constitution cannot be amended]
    
    B. On [another legal principle]:
       [Similar format with 3-5 placeholder citations]"
    
    REPORTER ABBREVIATIONS (Indian):
    - SCC: Supreme Court Cases
    - SCR: Supreme Court Reports  
    - AIR: All India Reporter
    - [Year] [Volume] SCC [Page]
    - Example: (2020) 15 SCC 585
    
    HIGH COURT REPORTERS:
    - Delhi: [Year] DLT [Page] or [Year] ILR Delhi [Page]
    - Bombay: [Year] Bom CR [Page]
    - Calcutta: [Year] Cal LT [Page]
    - Madras: [Year] LW [Page]
    
    PRECEDENT ORGANIZATION:
    - Group by legal issue/principle
    - Supreme Court precedents first
    - Then relevant High Court precedents
    - Minimum 3-5 placeholder citations per major legal ground
    - Include both supporting and distinguishable precedents where relevant

11. FORMATTING STANDARDS:
    
    PHYSICAL FORMAT:
    - Paper: A4 size (21 x 29.7 cm)
    - Font: Times New Roman, 12pt for body text
    - Font for headings: 14pt Bold, ALL CAPS
    - Line spacing: 1.5 or Double (as per court rules)
    - Margins: Left 1.5 inch (for binding), Right/Top/Bottom 1 inch
    - Page numbering: Bottom center or top right
    - Paragraph numbering: Consistent (1, 2, 3... for facts)
    
    TEXT FORMATTING:
    - Bold and Underline: Statutory sections, case names
    - CAPITALS: Main headings (FACTS, PRAYER, VERIFICATION)
    - Italics: Latin phrases (inter alia, prima facie, locus standi, etc.)
    - Quotation marks: For quoted text from documents/orders
    
    PARAGRAPH STRUCTURE:
    - Facts section: Numbered paragraphs (1., 2., 3.,...)
    - Legal arguments: Lettered or Roman numerals (A., B., C., or I., II., III.)
    - Sub-points: (i), (ii), (iii) or (a), (b), (c)
    
    DOCUMENT ORGANIZATION:
    - Cover page (if required by court rules)
    - Index (for documents >10 pages)
    - Main document
    - Annexures (properly tagged and paginated)
    - Verification at end of main document
    - Advocate details on last page

12. PLACEHOLDER STANDARDIZATION:
    
    Use {{{{double_brace}}}} format for ALL variable content:
    
    PARTY DETAILS:
    {{{{petitioner_name}}}}, {{{{petitioner_father_name}}}}, {{{{petitioner_age}}}}
    {{{{petitioner_occupation}}}}, {{{{petitioner_address}}}}
    {{{{respondent_name}}}}, {{{{respondent_designation}}}}, {{{{respondent_address}}}}
    
    CASE DETAILS:
    {{{{court_name}}}}, {{{{case_type}}}}, {{{{case_number}}}}, {{{{case_year}}}}
    {{{{filing_date}}}}, {{{{cause_of_action_date}}}}
    
    DOCUMENT REFERENCES:
    {{{{impugned_order_date}}}}, {{{{impugned_order_number}}}}, {{{{impugned_authority}}}}
    {{{{notice_date}}}}, {{{{reply_date}}}}
    
    FINANCIAL:
    {{{{suit_valuation}}}}, {{{{court_fee_paid}}}}, {{{{compensation_amount}}}}
    {{{{interest_rate}}}}, {{{{interest_from_date}}}}
    
    DATES & PLACE:
    {{{{date}}}}, {{{{place}}}}, {{{{verification_date}}}}, {{{{verification_place}}}}
    
    ADVOCATE DETAILS:
    {{{{advocate_name}}}}, {{{{bar_council_number}}}}, {{{{enrollment_year}}}}
    {{{{chamber_number}}}}, {{{{chamber_address}}}}, {{{{advocate_phone}}}}
    {{{{advocate_email}}}}
    
    ANNEXURES:
    {{{{annexure_reference}}}}, {{{{annexure_description}}}}, {{{{annexure_pages}}}}
    
    COURT-SPECIFIC:
    {{{{bench_location}}}}, {{{{registry_location}}}}, {{{{tribunal_form_number}}}}

═══════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════════════

Generate a COMPLETE, LEGALLY ACCURATE, COURT-READY template that:

✓ Uses ALL relevant information from provided case data
✓ Applies CORRECT Indian legal terminology and nomenclature
✓ Follows EXACT procedural law applicable to document type
✓ Implements PROPER court and department-specific formatting
✓ Includes ALL mandatory sections as per Indian procedural law
✓ Structures prayers in LEGALLY CORRECT format with proper terminology
✓ Contains ACCURATE statutory citations and case law placeholder format
✓ Uses PROPER verification clause as per CPC Order VI Rule 15
✓ Implements CORRECT party description format (father's/husband's name convention)
✓ Is PROFESSIONALLY FORMATTED per Indian court standards
✓ Uses STANDARDIZED placeholders for easy customization
✓ Is IMMEDIATELY USABLE after placeholder population and filing

CRITICAL LEGAL ACCURACY REQUIREMENTS:

1. Use EXACT statutory section numbers and act names
2. Apply CORRECT limitation periods as per Limitation Act, 1963
3. Use PROPER legal Latin phrases (prima facie, not "at first glance")
4. Follow PRECISE cause title format (S/o, D/o, W/o as applicable)
5. Include MANDATORY verification clause in prescribed format
6. Apply CORRECT principles (triple test for bail, alternative remedy for writs)
7. Use APPROPRIATE court-specific nomenclature (petition vs. plaint vs. application)
8. Ensure prayers are EXECUTABLE and use proper legal terminology
9. Follow CORRECT citation format for Indian case law
10. Include ALL procedural requirements (jurisdiction, limitation, locus standi)
The template must be EXHAUSTIVE, LEGALLY SOUND, and contain NO incomplete sections.
It should be ready for a lawyer to fill placeholders and file in court without
structural or procedural modifications

⚠️ PLACEHOLDER ENFORCEMENT (MANDATORY):
You MUST use {{{{double_brace}}}} placeholders for ALL specific information.
NEVER directly use names, dates, amounts, or specific details from the case data.
CORRECT EXAMPLES:
✓ "The Petitioner, {{{{petitioner_name}}}}, W/o {{{{husband_name}}}}, aged {{{{petitioner_age}}}} years..."
✓ "...married on {{{{marriage_date}}}} at {{{{marriage_place}}}}..."
✓ "...minor child, namely {{{{child_name}}}}, aged {{{{child_age}}}} years..."
✓ "...residing at {{{{petitioner_address}}}}"
INCORRECT EXAMPLES (DO NOT DO THIS):
✗ "The Petitioner, Smt. Priya Sharma..."
✗ "...married on 14.02.2017..."
✗ "...minor child, namely Rohan Sharma..."
✗ "...residing at No. 10, 1st Main, Jayanagar..."

⚠️ FORMATTING REQUIREMENT (MANDATORY):
Apply proper legal document formatting using markdown:
**SECTION HEADINGS IN BOLD CAPITALS**
1. First level numbered paragraphs with proper spacing
   a. Sub-points with indentation
   b. Each point fully explained
   2. Continue numbering sequentially
Use **bold** for:
- Section headings
- Statutory references: **Section 13(1)(i-a) of the Hindu Marriage Act, 1955**
- Case names in citations
Use _italics_ for:
- Latin phrases: _prima facie_, _locus standi_, _inter alia_

⚠️ COMPREHENSIVENESS REQUIREMENT (MANDATORY):
Generate EXTENSIVE, DETAILED templates with:
1. EXPANDED FACTS SECTION (Minimum 15-20 paragraphs):
   - Each paragraph should be 3-5 sentences
   - Include detailed context, background, and circumstances
   - Chronological progression with dates as placeholders
   - Emotional and factual elements
   - Supporting details for each allegation
2. DETAILED LEGAL SUBMISSIONS (Minimum 8-10 major grounds):
   - Each ground with multiple sub-sections
   - Extensive legal reasoning and explanation
   - Statutory provisions quoted in full
   - Case law discussion with ratio decidendi
   - Application of law to facts
3. COMPREHENSIVE PRECEDENT SECTION:
   - Minimum 10-15 case law citations
   - Organized by legal principle
   - Include Supreme Court and High Court cases
   - Full citation format with ratio
   - Provide clear placeholder instructions for explaining applicability.
4. DETAILED PRAYER JUSTIFICATION:
   - Each prayer with dedicated explanation section
   - Legal basis for each relief
   - Factual nexus establishment
   - Statutory entitlement demonstration
5. EXPANDED PROCEDURAL SECTIONS:
   - Detailed jurisdiction explanation (3-4 paragraphs)
   - Comprehensive limitation analysis
   - Maintainability discussion
   - Standing/locus standi elaboration

═══════════════════════════════════════════════════════════════
TEMPLATE STRUCTURE REQUIREMENTS
═══════════════════════════════════════════════════════════════

Your template MUST include these sections in this order:
**DOCUMENT HEADER**
- Court name and location
- Case number placeholder
- Complete cause title with ALL placeholders
**SUBJECT MATTER**
- Detailed description of petition type with statutory basis
**RESPECTFUL OPENING**
- "To, The Hon'ble..." format
**SYNOPSIS** (For complex cases - 3-4 paragraphs)
- Brief overview of the case
- Key parties and relationship
- Nature of dispute
- Relief sought
**FACTS** (Minimum 15-20 numbered paragraphs)
- Detailed chronological narration
- Each paragraph 3-5 sentences
- Use ONLY placeholders for specific details
- Include:  
  * Background and marriage details  
  * Circumstances leading to dispute  
  * Specific instances of alleged conduct  
  * Attempts at reconciliation  
  * Current status  
  * Impact on parties/children  
  * Financial circumstances  
  * Any other relevant facts
**LEGAL SUBMISSIONS** (Minimum 8-10 major grounds)
A. **JURISDICTION** (3-4 paragraphs)  
   - Detailed territorial jurisdiction explanation  
   - Statutory basis cited  
   - Precedents on jurisdiction  
   - Facts establishing jurisdiction
B. **STATUTORY FRAMEWORK** (5-6 paragraphs)  
   - Relevant sections quoted in full  
   - Legislative intent explained  
   - Judicial interpretation discussed  
   - Application to facts
C. **GROUNDS FOR RELIEF** (Multiple sub-sections)  
   - Each ground elaborately explained  
   - Factual allegations supporting ground  
   - Legal tests and their satisfaction  
   - Precedent application
D. **ENTITLEMENT TO RELIEF** (3-4 paragraphs per relief)  
   - Statutory basis for each relief  
   - Factual entitlement  
   - Precedent support  
   - Public policy considerations
**CASE LAW & PRECEDENTS** (Dedicated section)
- Organized by legal principle
- Minimum 10-15 citations
- Format: **[Citation: _Case Name v. Case Name_, (Year) Volume Reporter Page, (Court)]**
- Include ratio decidendi for each
- Distinguish or apply to facts
**MAINTAINABILITY** (3-4 paragraphs)
- Pecuniary jurisdiction
- Territorial jurisdiction
- Subject matter jurisdiction
- Removal of objections
**LIMITATION** (3-4 paragraphs)
- Article of Limitation Act applicable
- Date-wise calculation using placeholders
- Within time demonstration
- OR condonation grounds if delayed
**INTERIM RELIEF JUSTIFICATION** (If applicable - 5-6 paragraphs)
- _Prima facie_ case elaboration
- Balance of convenience analysis
- Irreparable injury demonstration
- Status quo necessity
- Precedents on interim relief
**PRAYER**
- Properly structured (Interim → Main → Supplementary)
- Each prayer specific and executable
- Use placeholders for amounts/dates
**INTERIM PRAYER** (Separate section if needed)
**VERIFICATION**
- Proper CPC Order VI Rule 15 format
- All placeholders
**ADVOCATE DETAILS**
- Complete format with placeholders
**LIST OF ANNEXURES**
- Detailed descriptions
- Page references as placeholders
**INDEX** (For documents >10 pages)

═══════════════════════════════════════════════════════════════
EXAMPLE OF PROPER PLACEHOLDER USAGE
═══════════════════════════════════════════════════════════════

**CORRECT FORMAT:**
**FACTS:**
1. The Petitioner, {{{{petitioner_name}}}}, W/o {{{{husband_name}}}}, and the Respondent, {{{{respondent_name}}}}, S/o {{{{respondent_father_name}}}}, were married on {{{{marriage_date}}}} at {{{{marriage_place}}}} according to Hindu rites and customs. The marriage was solemnized in the presence of family members and friends, and a marriage certificate was issued by the {{{{registering_authority}}}} bearing registration number {{{{marriage_registration_number}}}}. The Petitioner entered into the matrimonial alliance with legitimate expectations of a harmonious married life based on mutual respect, love, and companionship.
2. Out of the said wedlock, the parties were blessed with {{{{number_of_children}}}} child/children, namely {{{{child_1_name}}}}, aged {{{{child_1_age}}}} years, born on {{{{child_1_dob}}}}. [Add similar placeholders for additional children if applicable: {{{{child_2_name}}}}, {{{{child_2_age}}}}, etc.] The welfare and best interests of the minor child/children have been and continue to be the paramount concern of the Petitioner, who has been the primary caregiver since birth.
3. After the marriage, the parties resided together at {{{{matrimonial_home_address}}}} in {{{{city}}}}, {{{{state}}}}. Initially, the matrimonial life appeared normal, and the Petitioner discharged all her duties as a wife with diligence and devotion. However, gradually the Respondent's behavior towards the Petitioner underwent a drastic change, and the Respondent began to subject the Petitioner to cruelty, harassment, and mental torture.
[Continue with 15-20 detailed paragraphs using placeholders throughout]
**LEGAL SUBMISSIONS:**
A. **JURISDICTION OF THIS HON'BLE COURT**
   i. This Hon'ble Family Court at {{{{court_location}}}} has the territorial and pecuniary jurisdiction to entertain, try, and dispose of the present petition by virtue of **Section 7 of the Family Courts Act, 1984** read with **Section 19 of the Hindu Marriage Act, 1955**.  
   ii. **Section 19 of the Hindu Marriage Act, 1955** provides that a petition for dissolution of marriage may be presented to the District Court within the local limits of whose ordinary original civil jurisdiction: (a) the marriage was solemnized, or (b) the respondent at the time of presentation of the petition resides, or (c) the parties to the marriage last resided together, or (d) the petitioner is residing at the time of presentation of the petition, in a case where the respondent is at that time residing outside the territories to which this Act extends, or has not been heard of as being alive for a period of seven years or more by those persons who would naturally have heard of him if he were alive.
   iii. In the present case, the Petitioner has been continuously residing within the territorial jurisdiction of this Hon'ble Court at {{{{petitioner_current_address}}}} for the past {{{{duration_of_residence}}}} years/months. The parties last resided together at {{{{last_matrimonial_address}}}}, which also falls within the jurisdiction of this Hon'ble Court. Therefore, the Petitioner satisfies clauses (c) and (d) of Section 19, thereby conferring jurisdiction upon this Hon'ble Court.
   iv. The Hon'ble Supreme Court in **[Citation: _Smt. Sushila Bai v. Prem Narayan_, AIR 1987 SC 1239]** has held that jurisdiction under Section 19 of the Hindu Marriage Act is determined by the residence of the petitioner at the time of filing the petition, provided the respondent resides outside India or has not been heard of for seven years. In the present case, {{{{jurisdiction_facts_summary}}}}.
[Continue with extensive legal analysis...]
═══════════════════════════════════════════════════════════════
NOW GENERATE THE COMPLETE TEMPLATE
═══════════════════════════════════════════════════════════════
Following ALL the above requirements:
1. Use ONLY {{{{placeholders}}}} for specific details - NO actual names/dates/amounts
2. Apply proper markdown formatting with bold, italics, spacing
3. Generate COMPREHENSIVE content (15-20 pages worth)
4. Include ALL sections listed above
5. Expand each section with detailed reasoning
6. Include minimum 10-15 case citations
7. Make each facts paragraph 3-5 sentences
8. Provide extensive legal analysis
Generate the complete template now: