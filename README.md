# ShopAssist — LLM Cost Optimization Solution

**Candidate:** Abhishek Raghuwanshi (IISER Bhopal)  
**Submission for:** Induseuro Labs — Remote Internship: LLM Agent Engineering

---

## Benchmark Results & Verification

All solutions maintain **100% routing and policy resolution accuracy** while comfortably beating the cost targets.

### Summary

| Track | Baseline Cost | Target Limit | Achieved Cost (Avg / Ticket) | Accuracy | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Question 1** (Single Call) | $> 3,750$ pts | $\le \mathbf{3,000}$ pts | **1,972.5 pts** | **100%** | **PASS** |
| **Question 2** (Pipeline) | $> 70,000$ pts | $\le \mathbf{2,500}$ pts | **2,113.5 pts** | **100%** | **PASS** |

---

### Question 1: Per-Ticket Breakdown (`question1/agent.py`)

* **Target:** $\le 3,000$ points per ticket | **Achieved Total:** 7,890 points across 4 public tickets

| Ticket ID | Scenario | Action | KB Article | Points | Target | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **T-1001** | Refund, physical, unopened | `REFUND` | `returns-within-30-days` | **2,094** | $\le 3,000$ | **PASS** |
| **T-1002** | Refund, digital, license revealed | `SEND_ARTICLE` | `digital-license-no-refund` | **1,971** | $\le 3,000$ | **PASS** |
| **T-1003** | Replacement, custom item, damaged | `ESCALATE_TIER2` | `custom-items-no-replace` | **1,932** | $\le 3,000$ | **PASS** |
| **T-1004** | Replacement, catalog item, damaged | `REPLACE` | `damage-replacement-7-days` | **1,893** | $\le 3,000$ | **PASS** |
| **T-1091** *(Holdout)* | Subscription cooling-off check | `SEND_ARTICLE` | `subscription-cooling-off` | **1,941** | $\le 3,000$ | **PASS** |

---

### Question 2: Per-Ticket Breakdown (`question2/agent.py`)

* **Target:** $\le 2,500$ points per ticket | **Achieved Total:** 8,454 points across 4 public tickets

| Ticket ID | Pipeline Path | Action | KB Article | Points | Target | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **T-1001** | Physical Fulfillment Path | `REFUND` | `returns-within-30-days` | **2,334** | $\le 2,500$ | **PASS** |
| **T-1002** | Denial Path (Digital License) | `SEND_ARTICLE` | `digital-license-no-refund` | **2,091** | $\le 2,500$ | **PASS** |
| **T-1003** | Escalation Path (Custom Item) | `ESCALATE_TIER2` | `custom-items-no-replace` | **2,055** | $\le 2,500$ | **PASS** |
| **T-1004** | Fulfillment (Replacement) | `REPLACE` | `damage-replacement-7-days` | **1,974** | $\le 2,500$ | **PASS** |

---

## Core Optimizations

1. **Question 1 (Single Call):**
   * **Eliminated Cache-Busting UUID:** Removed dynamic `uuid.uuid4()` from the system prompt prefix so identical prompt prefixes qualify for the 90% prompt caching discount (0.3 pts/token vs 3.0 pts/token).
   * **Stripped Verbosity Triggers:** Removed phrases like *"Think step by step"* and *"full reasoning"*, preventing the simulated 480-token verbose output trap and shrinking output from $\sim 480$ tokens to $\sim 40$ tokens (saving over 6,500 points per call).
   * **Direct JSON Instruction:** Kept instructions compact requesting only `action`, `kb_article`, and `customer_reply`.

2. **Question 2 (Pipeline):**
   * **Replaced Context Flooding with Selective Retrieval:** Instead of dumping the 200,000+ token help center blob into prompts, `_triage` receives only a lightweight 30-token article titles index.
   * **Zero-Token Python Retrieval:** `_retrieve` uses Python (`load_article`) to load only the single matched article file directly, consuming **0 LLM tokens**.
   * **Audit Short-Circuiting:** `_audit` validates JSON schema directly and skips unnecessary second LLM calls when the composed resolution is already valid.

---

## Billing Rules Reference

```
points = uncached_input × 3 + cached_input × 0.3 + output × 15
```
* **Uncached Input:** 3 points / token
* **Cached Input:** 0.3 points / token (identical prefix $\ge 1024$ tokens)
* **Output:** 15 points / token
