### On-Page Recommendation System Design

This document outlines the design for a "Customers also bought/viewed" recommendation system for product pages.

---

### 1. Solution Proposal: Hybrid Recommendation System

A **hybrid approach** combining collaborative filtering and content-based filtering is the best fit.

**Why it's the best fit:**
* **Mitigates Cold Start:** Content-based filtering provides recommendations for new products with no interaction data.
* **Leverages Scarce User Data:** Collaborative filtering captures powerful user intent signals, even from limited data.
* **Increases Diversity & Relevance:** The proposed model enriches standard "also-bought" lists with similar items, preventing overly narrow or repetitive suggestions.

**The Hybrid Logic:**

For a given product $A$:
1.  Find products $B$ with a high **Lift score** relative to $A$ (Normalized Collaborative).
2.  Find products similar to the original product $A$ (Content-based).
3.  Find products similar to the top-associated product $B$ (Content-based enrichment).
4.  Combine, score, and rank these candidates to produce the final list.

---

### 2. Data Sources & Feature Sets

| Data Source | Data Points | Feature Set |
| :--- | :--- | :--- |
| **User Interactions** | Order history, page view events. | **Co-occurrence Pairs:** Generate `(product_A, product_B, frequency)` from orders and user sessions. This forms the basis for collaborative filtering. |
| **Product Catalog** | Product title, description, tags, images. | **Content Embeddings:**<br> - **Text:** Generate vector embeddings from title + description using a model like `OpenAI text embedding`.<br> - **Image:** Generate vector embeddings from product images using a model like `CLIP`.<br> - **Combined Vector:** A single vector per product representing its content. |

---

### 3. Approach & Scoring

#### Chosen Approach: Multi-Source Candidate Generation & Ranking

**1. Candidate Generation:**
* **Collaborative Candidates ($C_{cf}$):** For product $A$, calculate the **Lift score** for all co-purchased products. Retrieve the top N products ($B_1, B_2, ...$) with the highest lift, indicating a strong, non-random association. This avoids recommending items that are simply global bestsellers.

$$Lift(A, B) = \frac{\text{Transactions containing both A \& B} \cdot \text{Total Transactions}}{(\text{Transactions with A}) \cdot (\text{Transactions with B})}$$


* **Content-based Candidates ($S_A$):** Find the top K products most similar to $A$ using cosine similarity on content embeddings: $sim(v_A, v_X)$.
* **Enrichment Candidates ($S_B$):** For each product $B_i$ in $C_{cf}$, find the top M products most similar to $B_i$.

**2. Ranking & Scoring:**
Combine all candidates into a single pool: $Pool = C_{cf} \cup S_A \cup S_B$.
Assign a score to each product $P$ in the pool. A weighted scoring function can be used:

$$Score(P) = w_1 \cdot \text{co\_occur\_score}(P, A) + w_2 \cdot \text{sim}(P, A) + w_3 \cdot \max_{B \in C_{cf}} \text{sim}(P, B)$$

* $w_1, w_2, w_3$ are tunable weights.
* Filter out product $A$, out-of-stock items, and duplicates.
* Return the top 3-5 products by score.

#### Key Performance Indicators (KPIs)

| KPI | Formula | Purpose |
| :--- | :--- | :--- |
| **Click-Through Rate (CTR)** | $\frac{\text{Clicks on Recommendations}}{\text{Impressions of Recommendations}}$ | Measures user engagement with the recommendations. |
| **Conversion Rate (CVR)** | $\frac{\text{Orders with a Recommended Item}}{\text{Clicks on Recommendations}}$ | Measures the effectiveness of recommendations in driving purchases. |
| **Coverage** | $\frac{\text{# Products with Recommendations}}{\text{Total # Products}}$ | Measures the percentage of product pages where we can show recommendations. |

---

### 4. Implementation Plan

#### Phase 1: Data & Feature Engineering (Foundation)
* **Priority:** High
* **Estimate:** 2 Weeks
    * **Task 1.1:** Set up data ingestion pipeline from Shopify API (Products, Orders).
    * **Task 1.2:** **[Offline]** Script to generate and store product content embeddings (text + image). Use a vector database (e.g., Pinecone) or a file store.
    * **Task 1.3:** **[Offline]** Script to process interaction data and create co-occurrence tables (`(item_A, item_B, score)`).

#### Phase 2: Backend Model & API
* **Priority:** High
* **Estimate:** 1.5 Weeks
    * **Task 2.1:** Implement the hybrid recommendation logic (candidate generation, scoring, ranking).
    * **Task 2.2:** Build a simple API endpoint (e.g., `GET /recommendations?product_id=...`) that executes the logic and returns a list of product IDs.
    * **Task 2.3:** Deploy the service (e.g., via serverless function or container).

#### Phase 3: Frontend Integration & A/B Testing
* **Priority:** Medium
* **Estimate:** 1.5 Weeks
    * **Task 3.1:** Develop the UI component in the Shopify theme to display recommendations.
    * **Task 3.2:** Integrate the UI component with the recommendation API.
    * **Task 3.3:** Set up an A/B test to measure the impact of the feature on KPIs against a control group with no recommendations.

#### Phase 4: Monitoring & Iteration
* **Priority:** Ongoing
* **Estimate:** Ongoing
    * **Task 4.1:** Monitor API performance and recommendation quality.
    * **Task 4.2:** Schedule periodic re-runs of the offline data processing jobs.
    * **Task 4.3:** Analyze A/B test results and tune the scoring model weights ($w_1, w_2, w_3$).

**Total Estimated Time (MVP): ~5 Weeks**