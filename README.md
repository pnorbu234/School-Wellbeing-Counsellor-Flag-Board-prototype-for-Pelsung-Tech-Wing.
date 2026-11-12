# SA Wellbeing Flag Board

A one-day prototype for the Pelsung Tech Wing challenge. It uses only the supplied synthetic dataset.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `streamlit run app.py`

The supplied CSV loads by default. A different CSV with the same required columns can be uploaded in the sidebar.

## What works

- Loads all records and displays student ID, school and class.
- Applies the four baseline flags in the order specified in the brief.
- Displays a reason for each flag and sorts Urgent students first.
- Supports Not started, In progress and Closed follow-up statuses.
- Saves statuses to a local JSON file so they survive refreshes while local file storage remains available.
- Filters by school, class and flag; searches by student ID.
- Provides a separate supervisor view with no student IDs or free-text comments.
- Suppresses groups smaller than five and individual flag counts below five as `<5`.
- Highlights a missing sleep response as a data-quality warning.

## Rules and assumptions

1. Urgent: `q6_thoughts_of_self_harm = Yes`.
2. High: `q3_bullied = Often` OR `q2_safe_at_home = 1`.
3. Review: any two of (`q1_sleep_well <= 2`, `q5_sad_most_days = Yes`, `q4_trusted_adult = No`) OR `q7_wants_counsellor = Yes`.
4. None: all other responses.

Rules are applied in order; the first matching rule sets the flag. A missing sleep answer is not counted as poor sleep. It is displayed as a data-quality warning instead.

## Extra improvement

**Missing-response indicator:** counsellors are alerted when the sleep response is blank. This helps them notice incomplete survey records without automatically increasing a student's risk flag.

## Privacy and safety

Only the supplied synthetic dataset should be used. Never upload real student wellbeing or mental-health data to this prototype or to AI tools. The supervisor view excludes student IDs and comments. Small groups and small flag counts are suppressed to reduce disclosure risk.

This is a demonstration, not a production system. It has no authentication, role-based access control, encrypted database, audit log, or production-grade backups. An Urgent flag requires prompt review by an authorised counsellor under school safeguarding procedures. A flag is not a diagnosis and does not replace professional judgement.

## AI tools used

Edit this section to accurately list every tool you actually used. Example:
- ChatGPT: helped interpret the brief, plan the dashboard, draft and explain code, and prepare documentation.

**Example prompt that worked:** "Build a Streamlit app that reads this synthetic CSV, applies the four flagging rules in order, sorts Urgent records first, and provides a separate privacy-protected supervisor aggregate."

**Prompt that failed:** describe one prompt that genuinely failed during your work. Do not claim a failure that did not happen. An example of an overly broad prompt would be: "Build the whole production-ready platform in one step."

## What I would build next

- Secure sign-in and separate counsellor/supervisor permissions.
- Encrypted database, audit trail and production-grade backups.
- A documented urgent-case escalation and follow-up process.
- Further privacy review of aggregate reporting, including complementary suppression.
- Dzongkha labels and usability testing with counsellors.
- Automated tests for every baseline rule and edge case.
