# PolicyLens Failure & Weakness Analysis

This document summarizes the analyzed failure cases and pipeline weaknesses observed during the evaluation run.

## Observed Failures / Weaknesses (20 cases)

### CASE 1: Question 1 - Direct Factual
* **Question**: "What does Article 25 of the Constitution of Pakistan state regarding equality of citizens?"
* **Expected Sections**: `All citizens are equal before law and are entitled to equal protection of law. There shall be no discrimination on the basis of sex alone. Nothing in ...`
* **Observed Answer**: "[LOCAL FALLBACK - NO API KEY] Content: CONSTITUTION OF THE ISLAMIC REPUBLIC OF PAKISTAN [1] Content: Article 240. [2] Appointments and conditions of service Subject to the Constitution, the appointmen..."
* **Failure Type**: Retrieval Failure (0% Hit Rate)
* **Root Cause**: The embedding vector for the question did not align close enough with the target document chunks in the vector space, resulting in relevant paragraphs falling outside the Top-K retrieved items.
* **Proposed Improvement**: Increase chunk overlap and tune dense embedding thresholds, or supplement search with keyword-based retrieval (hybrid BM25).

### CASE 2: Question 2 - Direct Factual
* **Question**: "What is the definition of the State under Article 7 of the Constitution of Pakistan?"
* **Expected Sections**: `The State means the Federal Government, Parliament, a Provincial Government, a Provincial Assembly, and such local or other authorities in Pakistan as...`
* **Observed Answer**: "[LOCAL FALLBACK - NO API KEY] Content: Article 240. [1] Appointments and conditions of service Subject to the Constitution, the appointments to and the terms and conditions of service of persons in th..."
* **Failure Type**: Retrieval Failure (0% Hit Rate)
* **Root Cause**: The embedding vector for the question did not align close enough with the target document chunks in the vector space, resulting in relevant paragraphs falling outside the Top-K retrieved items.
* **Proposed Improvement**: Increase chunk overlap and tune dense embedding thresholds, or supplement search with keyword-based retrieval (hybrid BM25).

### CASE 3: Question 3 - Direct Factual
* **Question**: "What is the punishment for theft under Section 379 of the Pakistan Penal Code?"
* **Expected Sections**: `Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both...`
* **Observed Answer**: "[LOCAL FALLBACK - NO API KEY] Content: Section 11. [1] Appointments and conditions of service Subject to the Constitution, the appointments to and the terms and conditions of service of persons in the..."
* **Failure Type**: Retrieval Failure (0% Hit Rate)
* **Root Cause**: The embedding vector for the question did not align close enough with the target document chunks in the vector space, resulting in relevant paragraphs falling outside the Top-K retrieved items.
* **Proposed Improvement**: Increase chunk overlap and tune dense embedding thresholds, or supplement search with keyword-based retrieval (hybrid BM25).

