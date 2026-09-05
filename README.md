# AI Risk Manager

An explainable AI-based fraud risk scoring system for payment transactions.

The system analyzes transaction, behavioural, historical, payment, and device/identity signals to estimate fraud probability and convert it into an operational decision:

- LOW → ALLOW
- MEDIUM → VERIFY
- HIGH → REVIEW

The project is designed as a defense-only fraud detection and risk decisioning system.

---

## 1. Problem

Payment fraud detection is challenging because fraudulent transactions are rare compared with legitimate transactions.

A useful fraud detection system therefore needs to do more than classify transactions as fraud or legitimate.

It should:

- identify suspicious transactions,
- control false positives,
- provide a measurable fraud detection performance,
- explain why a transaction received its risk score,
- and translate the model output into an actionable decision.

---

## 2. Solution

AI Risk Manager combines machine learning with an explainable risk decision layer.

For every transaction, the system produces:

1. Fraud probability
2. Risk level
3. Recommended action
4. Top contributing signals

Example:

Transaction
↓
Feature Engineering
↓
Random Forest
↓
Fraud Probability
↓
Risk Decision
↓
ALLOW / VERIFY / REVIEW
↓
SHAP Explanation

---

## 3. Key Features

### AI Fraud Risk Scoring

The ML model produces a fraud probability for every transaction.

### Risk-Based Decisioning

| Risk Score | Risk Level | Action |
|------------|------------|--------|
| < 40% | LOW | ALLOW |
| 40% – <70% | MEDIUM | VERIFY |
| ≥ 70% | HIGH | REVIEW |

### Behavioural Signals

The model uses transaction history and velocity features such as:

- transactions in the last 10 minutes,
- transactions in the last hour,
- amount spent in the last hour,
- previous transaction count,
- previous average transaction amount,
- previous maximum transaction amount,
- current amount compared with historical average.

### Device / Identity Signals

The system uses available identity-related signals including:

- DeviceType
- DeviceInfo
- operating-system information
- browser information
- screen-resolution information
- identity-signal availability

These are treated as composite device/identity signals rather than assuming that any single field uniquely identifies a device.

### Payment Signals

The model also considers:

- transaction amount,
- product category,
- card attributes,
- card type,
- address information,
- distance-related signals,
- purchaser and recipient email-domain information.

### Explainable AI

SHAP is used to identify the features contributing most strongly to an individual prediction.

The dashboard presents these signals as:

- Higher Risk
- Lower Risk

This allows the decision to be inspected instead of presenting only a black-box score.

---

## 4. Machine Learning

The project uses a Random Forest classifier with class balancing.

### Model

```text
RandomForestClassifier
n_estimators = 100
max_depth = 15
min_samples_leaf = 5
class_weight = balanced
random_state = 42
