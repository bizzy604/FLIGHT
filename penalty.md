# 📘 Comprehensive Guide to VDC Penalty Interpretation

---

## 🧠 Understanding

1. **Passenger Types:**  
   - ADT (Adult)  
   - Young Adult (subset of ADT)  
   - CHD (Child)  
   - INFT (Infant)  

2. **Applicability Across APIs:**  
   - `AirShopping`  
   - `FlightPrice`  
   - `OrderView` (including `OrderCreate`, `OrderChange`, `OrderRetrieve`)  
   - `OrderReshop` (Reissue)  
   - `OrderRequote` (Reissue)

3. **Penalty Types Covered:**  
   - Cancel  
   - Change  
   - No-show Cancel  
   - No-show Change  
   - Upgrade  
   - Future penalty types

---

## ⚙️ Assumption

Agency UI presents penalty details at the **Origin-Destination (OD)** level or **Itinerary level**, while the VDC API can provide more granular **segment-level data**.

---

## 🔎 Key Point

The **precise amount** for a cancellation or change **will only be revealed after initiating** the actual transaction via:  
- `RefundQuote RS API`  
- `Reshop/Requote RS API`

---

## 📊 Penalty Value Logic: MAX / MIN Interpretation

### ✅ API Consumer Guidance

| Interpretation | Action |
|----------------|--------|
| MAX only       | Treat as final penalty |
| MIN + MAX      | Display range |
| No value       | Assume MAX |

---

### 🧾 Penalty Display Examples

#### 📍 Segment Level vs OD Level Interpretation

| Trip Type    | Source   | Segment Penalty                        | UI (OD) Penalty          |
|--------------|----------|----------------------------------------|---------------------------|
| One Way      | VDC API  | A-B: MIN 100, MAX 120                  | A-C: MIN 100, MAX 200     |
| Round Trip   | VDC API  | A-B, B-C: MIN 100-130                  | A-C, C-A: MIN 90, MAX 130 |
| Multi-City   | VDC API  | A-B, B-C, C-B, B-A: 100-130            | A-C, C-A: MIN 90, MAX 130 |

---

## 📐 Penalty Table Logic Interpretation

### 🚫 Cancel Penalty Rules

| Cancel Fee | Refundable | Interpretation                               | Penalty | Refund | Cancel Allowed |
|------------|------------|----------------------------------------------|---------|--------|----------------|
| TRUE       | TRUE       | Partially refundable                         | Yes     | Yes    | Yes            |
| FALSE      | TRUE       | Fully refundable                             | No      | Yes    | Yes            |
| FALSE      | FALSE      | Non-refundable                               | No      | No     | No             |
| Missing    | TRUE       | Refundable, penalty unknown                  | Unknown | Yes    | Yes            |
| Missing    | FALSE      | Non-refundable                               | No      | No     | No             |
| FALSE      | Missing    | Refundability unknown                        | No      | Unknown| Unknown        |
| TRUE       | Missing    | Cancel allowed with fee, refund unknown      | Yes     | Unknown| Yes            |
| Missing    | Missing    | Cancel details unknown                       | Unknown | Unknown| Unknown        |

---

### 🔁 Change Penalty Rules

| Change Fee | Change Allowed | Interpretation                          | Penalty | Change Allowed |
|------------|----------------|------------------------------------------|---------|----------------|
| TRUE       | TRUE           | Change with penalty + fare difference    | Yes     | Yes            |
| FALSE      | TRUE           | Free change + fare difference            | No      | Yes            |
| FALSE      | FALSE          | Not allowed                              | No      | No             |
| Missing    | TRUE           | Change allowed, penalty unknown          | Unknown | Yes            |
| Missing    | FALSE          | Change not allowed                       | No      | No             |
| FALSE      | Missing        | Change allowed unknown                   | No      | Unknown        |
| TRUE       | Missing        | Change allowed with fee                  | Yes     | Yes            |
| Missing    | Missing        | Change status unknown                    | Unknown | Unknown        |

---

## 🚨 "Unknown" Recommendation to API Consumers

When data is unclear or missing:  
- Assume **most restrictive** outcome  
- Treat as **Non-refundable and Non-changeable**

---

## 📎 Summary

| Topic             | Insight                                      |
|------------------|----------------------------------------------|
| Passenger Types   | Penalty varies by ADT, CHD, INFT             |
| Interpretation    | MIN = base, MAX = likely charge              |
| Display           | Segment-level (VDC API) vs OD-level (UI)     |
| Rules Logic       | Based on multiple flag combinations          |
| Missing Data      | Default to MAX or most restrictive assumption|

