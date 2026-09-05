import pandas as pd
import numpy as np
import shap

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


# ============================================================
# 1. LOAD DATA
# ============================================================

transaction = pd.read_csv("../data/train_transaction.csv")
identity = pd.read_csv("../data/train_identity.csv")

print("Transaction shape:", transaction.shape)
print("Identity shape:", identity.shape)


# ============================================================
# 2. MERGE DATA
# ============================================================

data = transaction.merge(
    identity,
    on="TransactionID",
    how="left"
)

print("\nCombined shape:", data.shape)
print("\nAvailable identity/card columns:")
print([
    col for col in data.columns
    if col.startswith("card")
    or col in ["TransactionID", "TransactionDT", "addr1"]
])


# ============================================================
# 3. FEATURE ENGINEERING
# ============================================================

SECONDS_IN_DAY = 24 * 60 * 60

data["TransactionHour"] = (
    (data["TransactionDT"] % SECONDS_IN_DAY) // 3600
).astype(int)

data["TransactionDay"] = (
    data["TransactionDT"] // SECONDS_IN_DAY
).astype(int)

data["LogTransactionAmt"] = np.log1p(
    data["TransactionAmt"]
)

# ============================================================
# 3B. PAST TRANSACTION / VELOCITY FEATURES
# ============================================================
# IMPORTANT:
# These features use ONLY transactions that happened BEFORE
# the current transaction. Future transactions are never used.
#
# Because the IEEE-CIS dataset does not contain a clean
# customer_id, we use the available card fields as a
# card-profile proxy.

card_key_columns = [
    "card1",
    "card2",
    "card3",
    "card5",
    "card6"
]

# Create a stable card-profile key.
# Missing card values are replaced so they can still be grouped.
card_key = (
    data[card_key_columns]
    .astype("string")
    .fillna("Unknown")
    .agg("|".join, axis=1)
)

# Work in chronological order.
velocity_data = pd.DataFrame({
    "OriginalIndex": data.index,
    "CardProfile": card_key,
    "TransactionDT": data["TransactionDT"].values,
    "TransactionAmt": data["TransactionAmt"].values
})

velocity_data = velocity_data.sort_values(
    ["CardProfile", "TransactionDT", "OriginalIndex"]
).reset_index(drop=True)

# Arrays for fast past-only calculations.
times = velocity_data["TransactionDT"].to_numpy()
amounts = (
    velocity_data["TransactionAmt"]
    .fillna(0)
    .to_numpy(dtype=float)
)

last_10_min_count = np.zeros(len(velocity_data), dtype=np.int32)
last_1_hour_count = np.zeros(len(velocity_data), dtype=np.int32)
last_1_hour_amount = np.zeros(len(velocity_data), dtype=float)

# TransactionDT is measured in seconds in the IEEE-CIS dataset.
TEN_MINUTES = 10 * 60
ONE_HOUR = 60 * 60

# Calculate historical features separately for each card profile.
for _, group in velocity_data.groupby(
    "CardProfile",
    sort=False
):
    positions = group.index.to_numpy()
    group_times = times[positions]
    group_amounts = amounts[positions]

    # Prefix sum lets us calculate historical amount quickly.
    prefix_amount = np.concatenate(
        ([0.0], np.cumsum(group_amounts))
    )

    for j, pos in enumerate(positions):
        current_time = group_times[j]

        # Search only to the LEFT of the current transaction.
        # Therefore the current/future transaction is never included.
        left_10 = np.searchsorted(
            group_times,
            current_time - TEN_MINUTES,
            side="left"
        )

        left_1h = np.searchsorted(
            group_times,
            current_time - ONE_HOUR,
            side="left"
        )

        # j is the current transaction position.
        last_10_min_count[pos] = j - left_10
        last_1_hour_count[pos] = j - left_1h

        last_1_hour_amount[pos] = (
            prefix_amount[j] - prefix_amount[left_1h]
        )

# Put the calculated features back in original transaction order.
velocity_data["TransactionsLast10Min"] = last_10_min_count
velocity_data["TransactionsLast1Hour"] = last_1_hour_count
velocity_data["AmountLast1Hour"] = last_1_hour_amount

velocity_features = velocity_data.sort_values(
    "OriginalIndex"
)[
    [
        "TransactionsLast10Min",
        "TransactionsLast1Hour",
        "AmountLast1Hour"
    ]
].to_numpy()

data[
    [
        "TransactionsLast10Min",
        "TransactionsLast1Hour",
        "AmountLast1Hour"
    ]
] = velocity_features

print("\nPast transaction / velocity features created:")
print("TransactionsLast10Min")
print("TransactionsLast1Hour")
print("AmountLast1Hour")

# ============================================================
# 3C. PAST CARD BEHAVIOUR FEATURES
# ============================================================
# These features also use ONLY transactions that occurred
# BEFORE the current transaction.
#
# They describe the previous behaviour of the same
# card-profile proxy.

previous_count = np.zeros(len(velocity_data), dtype=np.int32)
previous_average_amount = np.zeros(len(velocity_data), dtype=float)
previous_max_amount = np.zeros(len(velocity_data), dtype=float)
current_vs_previous_average = np.ones(len(velocity_data), dtype=float)

for _, group in velocity_data.groupby(
    "CardProfile",
    sort=False
):
    positions = group.index.to_numpy()
    group_amounts = amounts[positions]

    running_sum = 0.0
    running_max = 0.0

    for j, pos in enumerate(positions):

        # Only transactions before the current one.
        previous_count[pos] = j

        if j > 0:
            average_amount = running_sum / j

            previous_average_amount[pos] = average_amount
            previous_max_amount[pos] = running_max

            current_amount = group_amounts[j]

            if average_amount > 0:
                current_vs_previous_average[pos] = (
                    current_amount / average_amount
                )
            else:
                current_vs_previous_average[pos] = 1.0

        else:
            # No history exists for the first transaction.
            previous_average_amount[pos] = 0.0
            previous_max_amount[pos] = 0.0
            current_vs_previous_average[pos] = 1.0

        # Update history AFTER calculating the current row.
        # This prevents the current transaction from leaking
        # into its own historical features.
        running_sum += group_amounts[j]
        running_max = max(running_max, group_amounts[j])

velocity_data["PreviousTransactionCount"] = previous_count
velocity_data["PreviousAverageAmount"] = previous_average_amount
velocity_data["PreviousMaxAmount"] = previous_max_amount
velocity_data["CurrentAmountVsPreviousAverage"] = (
    current_vs_previous_average
)

historical_features = velocity_data.sort_values(
    "OriginalIndex"
)[
    [
        "PreviousTransactionCount",
        "PreviousAverageAmount",
        "PreviousMaxAmount",
        "CurrentAmountVsPreviousAverage"
    ]
].to_numpy()

data[
    [
        "PreviousTransactionCount",
        "PreviousAverageAmount",
        "PreviousMaxAmount",
        "CurrentAmountVsPreviousAverage"
    ]
] = historical_features

print("\nPast card behaviour features created:")
print("PreviousTransactionCount")
print("PreviousAverageAmount")
print("PreviousMaxAmount")
print("CurrentAmountVsPreviousAverage")

print("\nEngineered features created:")
print("TransactionHour")
print("TransactionDay")
print("LogTransactionAmt")


# ============================================================
# 3D. DEVICE / IDENTITY SIGNATURE
# ============================================================
# IEEE-CIS does not contain a guaranteed persistent device ID.
# Therefore this is a device/identity signature, not a guaranteed
# unique physical-device fingerprint.
#
# We keep the signature for inspection/display, but DO NOT feed the
# full combined signature to the model. A raw combined categorical
# value can make the model over-rely on rare/missing combinations.
# Instead, the model receives the individual device/environment
# signals plus how much device information is available.

device_signature_columns = [
    "DeviceType",
    "DeviceInfo",
    "id_30",
    "id_31",
    "id_33"
]

device_signature_columns = [
    col for col in device_signature_columns
    if col in data.columns
]

device_signature_parts = (
    data[device_signature_columns]
    .astype("string")
)

# Normalize values without turning missing values into one dominant
# model category. Missing values remain missing for the model.
for col in device_signature_columns:
    device_signature_parts[col] = (
        device_signature_parts[col]
        .str.strip()
        .str.lower()
    )

# Human-readable signature for transaction inspection only.
data["DeviceIdentitySignature"] = (
    device_signature_parts
    .fillna("unknown")
    .agg("|".join, axis=1)
)

# Number of available device/environment signals.
data["DeviceInfoAvailableCount"] = (
    device_signature_parts.notna().sum(axis=1).astype(float)
)

# 1 means no device/environment information was available.
data["DeviceInfoMissing"] = (
    (data["DeviceInfoAvailableCount"] == 0).astype(int)
)

print("\nDevice / identity signature created:")
print("DeviceType")
print("DeviceInfo")
print("id_30 (OS)")
print("id_31 (Browser)")
print("id_33 (Screen resolution)")
print("DeviceInfoAvailableCount")
print("DeviceInfoMissing")
print(
    "Unique device/identity signatures:",
    data["DeviceIdentitySignature"].nunique()
)

# ============================================================
# 4. SELECT FEATURES
# ============================================================

features = [
    "TransactionAmt",
    "LogTransactionAmt",

    "TransactionsLast10Min",
    "TransactionsLast1Hour",
    "AmountLast1Hour",

    "PreviousTransactionCount",
    "PreviousAverageAmount",
    "PreviousMaxAmount",
    "CurrentAmountVsPreviousAverage",

    "TransactionDT",
    "TransactionHour",
    "TransactionDay",

    "ProductCD",

    "card1",
    "card2",
    "card3",
    "card4",
    "card5",
    "card6",

    "addr1",
    "addr2",

    "dist1",
    "dist2",

    "P_emaildomain",
    "R_emaildomain",

    "DeviceType",
    "DeviceInfo",
    "id_30",
    "id_31",
    "id_33",
    "DeviceInfoAvailableCount",
    "DeviceInfoMissing"
]

X = data[features].copy()
y = data["isFraud"]


# ============================================================
# 5. NUMERICAL FEATURES
# ============================================================

numeric_features = [
    "TransactionAmt",
    "LogTransactionAmt",

    "TransactionsLast10Min",
    "TransactionsLast1Hour",
    "AmountLast1Hour",

    "PreviousTransactionCount",
    "PreviousAverageAmount",
    "PreviousMaxAmount",
    "CurrentAmountVsPreviousAverage",

    "TransactionDT",
    "TransactionHour",
    "TransactionDay",

    "card1",
    "card2",
    "card3",
    "card5",

    "addr1",
    "addr2",

    "dist1",
    "dist2"
]


# ============================================================
# 6. CATEGORICAL FEATURES
# ============================================================

categorical_features = [
    "ProductCD",
    "card4",
    "card6",
    "P_emaildomain",
    "R_emaildomain",
    "DeviceType",
    "DeviceInfo",
    "id_30",
    "id_31",
    "id_33"
]


# ============================================================
# 7. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Test samples:", len(X_test))

print("\nTraining fraud distribution:")
print(y_train.value_counts())

print("\nTest fraud distribution:")
print(y_test.value_counts())


# ============================================================
# 8. NUMERICAL PIPELINE
# ============================================================

numeric_pipeline = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    )
])


# ============================================================
# 9. CATEGORICAL PIPELINE
# ============================================================

categorical_pipeline = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="most_frequent")
    ),

    (
        "encoder",
        OneHotEncoder(handle_unknown="ignore")
    )
])


# ============================================================
# 10. PREPROCESSOR
# ============================================================

preprocessor = ColumnTransformer([
    (
        "num",
        numeric_pipeline,
        numeric_features
    ),

    (
        "cat",
        categorical_pipeline,
        categorical_features
    )
])


# ============================================================
# 11. RANDOM FOREST MODEL
# ============================================================

model = Pipeline([
    (
        "preprocessor",
        preprocessor
    ),

    (
        "classifier",
        RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
    )
])


# ============================================================
# 12. TRAIN MODEL
# ============================================================

print("\nTraining Random Forest...")

model.fit(
    X_train,
    y_train
)

import joblib

joblib.dump(model, "fraud_model.pkl")

print("Model saved successfully!")


# ============================================================
# 13. FRAUD PROBABILITY
# ============================================================

y_probability = model.predict_proba(
    X_test
)[:, 1]

print("\n==============================================")
print("FIRST 10 FRAUD PROBABILITIES")
print("==============================================")

for probability in y_probability[:10]:
    print(f"{probability:.2%}")


# ============================================================
# 14. RISK LEVEL FUNCTION
# ============================================================

def get_risk_level(probability):

    if probability < 0.40:
        return "LOW"

    elif probability < 0.70:
        return "MEDIUM"

    else:
        return "HIGH"


# ============================================================
# 15. RISK ACTION FUNCTION
# ============================================================

def get_action(risk_level):

    if risk_level == "LOW":
        return "ALLOW"

    elif risk_level == "MEDIUM":
        return "VERIFY"

    else:
        return "REVIEW"


# ============================================================
# 16. CREATE RISK LEVELS
# ============================================================

risk_levels = [
    get_risk_level(probability)
    for probability in y_probability
]


# ============================================================
# 17. FEATURE IMPORTANCE
# ============================================================

rf_model = model.named_steps["classifier"]

feature_names = model.named_steps[
    "preprocessor"
].get_feature_names_out()

importances = rf_model.feature_importances_

importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importances
})

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print("\n==============================================")
print("TOP 20 FEATURE IMPORTANCES")
print("==============================================")

print(
    importance_df
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 18. THRESHOLD COMPARISON
# ============================================================

thresholds = [
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80
]

print("\n==============================================")
print("THRESHOLD COMPARISON")
print("==============================================")

for threshold in thresholds:

    y_threshold = (
        y_probability >= threshold
    ).astype(int)

    report = classification_report(
        y_test,
        y_threshold,
        output_dict=True,
        zero_division=0
    )

    precision = report["1"]["precision"]
    recall = report["1"]["recall"]
    f1 = report["1"]["f1-score"]

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        y_threshold
    ).ravel()

    false_positive_rate = (
        fp / (fp + tn)
    )

    print(
        f"\nThreshold: {threshold:.0%}"
        f"\nPrecision: {precision:.2%}"
        f"\nRecall: {recall:.2%}"
        f"\nF1 Score: {f1:.2%}"
        f"\nFalse Positive Rate: "
        f"{false_positive_rate:.2%}"
        f"\nFalse Positives: {fp:,}"
        f"\nMissed Fraud: {fn:,}"
    )


# ============================================================
# 19. FALSE-POSITIVE / FALSE-NEGATIVE COST ANALYSIS
# ============================================================

FALSE_POSITIVE_COST = 10
FALSE_NEGATIVE_COST = 100

print("\n==============================================")
print("COST-BASED THRESHOLD ANALYSIS")
print("==============================================")
print(f"False Positive Cost : {FALSE_POSITIVE_COST}")
print(f"False Negative Cost : {FALSE_NEGATIVE_COST}")

cost_results = []

for threshold in thresholds:

    y_cost_pred = (
        y_probability >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_test,
        y_cost_pred
    ).ravel()

    fp_cost = fp * FALSE_POSITIVE_COST
    fn_cost = fn * FALSE_NEGATIVE_COST
    total_cost = fp_cost + fn_cost

    cost_results.append(
        (threshold, fp, fn, total_cost)
    )

    print(f"\nThreshold: {threshold:.0%}")
    print(
        f"False Positive Cost : "
        f"{fp:,} × {FALSE_POSITIVE_COST} = {fp_cost:,}"
    )
    print(
        f"False Negative Cost : "
        f"{fn:,} × {FALSE_NEGATIVE_COST} = {fn_cost:,}"
    )
    print(f"Total Cost          : {total_cost:,}")

best_threshold, best_fp, best_fn, best_cost = min(
    cost_results,
    key=lambda item: item[3]
)

print("\n----------------------------------------------")
print(f"LOWEST-COST THRESHOLD: {best_threshold:.0%}")
print(f"False Positives : {best_fp:,}")
print(f"Missed Fraud    : {best_fn:,}")
print(f"Total Cost      : {best_cost:,}")
print("----------------------------------------------")


# ============================================================
# 19. RISK LEVEL DISTRIBUTION
# ============================================================

risk_distribution = pd.Series(
    risk_levels
).value_counts()

print("\n==============================================")
print("RISK LEVEL DISTRIBUTION")
print("==============================================")

print(risk_distribution)


# ============================================================
# 20. RISK LEVEL PERCENTAGE
# ============================================================

risk_percentage = (
    pd.Series(risk_levels)
    .value_counts(normalize=True)
    * 100
)

print("\n==============================================")
print("RISK LEVEL PERCENTAGE")
print("==============================================")

for level, percentage in risk_percentage.items():

    print(
        f"{level}: {percentage:.2f}%"
    )


# ============================================================
# 21. ACTUAL FRAUD RATE BY RISK LEVEL
# ============================================================

risk_data = pd.DataFrame({
    "RiskLevel": risk_levels,
    "ActualFraud": y_test.values
})

risk_summary = risk_data.groupby(
    "RiskLevel"
).agg(
    Transactions=("ActualFraud", "count"),
    FraudCases=("ActualFraud", "sum")
)

risk_summary["FraudRate"] = (
    risk_summary["FraudCases"]
    / risk_summary["Transactions"]
    * 100
)

print("\n==============================================")
print("ACTUAL FRAUD RATE BY RISK LEVEL")
print("==============================================")

print(risk_summary)


# ============================================================
# 22. RISK DECISION EXAMPLES
# ============================================================

print("\n==============================================")
print("RISK DECISION EXAMPLES")
print("==============================================")

for i in range(10):

    risk = risk_levels[i]

    action = get_action(risk)

    print(
        f"Transaction {i + 1}: "
        f"Risk Score = {y_probability[i]:.2%} | "
        f"Risk = {risk} | "
        f"Action = {action}"
    )


# ============================================================
# 23. TRANSACTION-LEVEL DETAILS
# ============================================================

print("\n==============================================")
print("TRANSACTION-LEVEL DETAILS")
print("==============================================")

for i in range(5):

    transaction_row = X_test.iloc[i]

    print(f"\nTransaction {i + 1}")
    print("-" * 50)

    print(
        f"Risk Score        : "
        f"{y_probability[i]:.2%}"
    )

    print(
        f"Risk Level        : "
        f"{risk_levels[i]}"
    )

    print(
        f"Recommended Action: "
        f"{get_action(risk_levels[i])}"
    )

    print("\nTransaction Signals:")

    print(
        f"Transaction Amount : "
        f"{transaction_row['TransactionAmt']}"
    )

    print(
        f"Product Code       : "
        f"{transaction_row['ProductCD']}"
    )

    print(
        f"Card Type          : "
        f"{transaction_row['card4']}"
    )

    print(
        f"Device Type        : "
        f"{transaction_row['DeviceType']}"
    )

    print(
        f"Email Domain       : "
        f"{transaction_row['P_emaildomain']}"
    )

    print(
        f"Transaction Hour   : "
        f"{transaction_row['TransactionHour']}"
    )

    print(
        f"Transactions Last 10 Min : "
        f"{transaction_row['TransactionsLast10Min']}"
    )

    print(
        f"Transactions Last 1 Hour : "
        f"{transaction_row['TransactionsLast1Hour']}"
    )

    print(
        f"Amount Last 1 Hour       : "
        f"{transaction_row['AmountLast1Hour']:.2f}"
    )

    print(
        f"Previous Transactions    : "
        f"{transaction_row['PreviousTransactionCount']}"
    )

    print(
        f"Previous Average Amount  : "
        f"{transaction_row['PreviousAverageAmount']:.2f}"
    )

    print(
        f"Previous Maximum Amount  : "
        f"{transaction_row['PreviousMaxAmount']:.2f}"
    )

    print(
        f"Current / Previous Avg   : "
        f"{transaction_row['CurrentAmountVsPreviousAverage']:.2f}x"
    )


# ============================================================
# 24. SHAP EXPLAINABILITY
# ============================================================

print("\n==============================================")
print("SHAP TRANSACTION EXPLANATION")
print("==============================================")

# Transform test data using the trained preprocessor
X_test_transformed = model.named_steps[
    "preprocessor"
].transform(X_test.iloc[:5])

# Convert transformed data to numeric format for SHAP
X_test_transformed = X_test_transformed.toarray().astype(float)


# Create TreeExplainer for Random Forest
explainer = shap.TreeExplainer(
    rf_model
)


# Calculate SHAP values
shap_values = explainer.shap_values(
    X_test_transformed
)


# SHAP versions can return either:
# 1. A list [class_0, class_1]
# 2. A 3D numpy array
#
# We need the fraud class = class 1.

if isinstance(shap_values, list):

    fraud_shap_values = shap_values[1]

else:

    if shap_values.ndim == 3:

        fraud_shap_values = shap_values[:, :, 1]

    else:

        fraud_shap_values = shap_values


# ============================================================
# 25. SHOW SHAP EXPLANATION
# ============================================================

# ============================================================
# 25. HUMAN-READABLE SHAP EXPLANATION
# ============================================================

print("\n==============================================")
print("HUMAN-READABLE SHAP EXPLANATION")
print("==============================================")


# Map encoded feature names to business-friendly names
def get_business_feature(feature):

    if "ProductCD_" in feature:
        return "Product Category"

    elif "card6_" in feature:
        return "Card Type"

    elif "card1" in feature:
        return "Card Identifier"

    elif "card2" in feature:
        return "Card Information"

    elif "card3" in feature:
        return "Card Category"

    elif "card5" in feature:
        return "Card Information"

    elif "DeviceInfoAvailableCount" in feature:
        return "Device Information Availability"

    elif "DeviceInfoMissing" in feature:
        return "Missing Device Information"

    elif "DeviceType_" in feature:
        return "Device Type"

    elif "DeviceInfo_" in feature:
        return "Device Information"

    elif "id_30_" in feature:
        return "Operating System"

    elif "id_31_" in feature:
        return "Browser"

    elif "id_33_" in feature:
        return "Screen Resolution"

    elif "P_emaildomain_" in feature:
        return "Purchaser Email Domain"

    elif "R_emaildomain_" in feature:
        return "Recipient Email Domain"

    elif "TransactionAmt" in feature:
        return "Transaction Amount"

    elif "LogTransactionAmt" in feature:
        return "Transaction Amount Pattern"

    elif "TransactionsLast10Min" in feature:
        return "Recent Transaction Velocity"

    elif "TransactionsLast1Hour" in feature:
        return "Hourly Transaction Velocity"

    elif "AmountLast1Hour" in feature:
        return "Recent Spending Amount"

    elif "PreviousTransactionCount" in feature:
        return "Previous Transaction History"

    elif "PreviousAverageAmount" in feature:
        return "Previous Average Spending"

    elif "PreviousMaxAmount" in feature:
        return "Previous Maximum Spending"

    elif "CurrentAmountVsPreviousAverage" in feature:
        return "Amount vs Previous Average"

    elif "TransactionHour" in feature:
        return "Transaction Hour"

    elif "TransactionDay" in feature:
        return "Transaction Day"

    elif "TransactionDT" in feature:
        return "Transaction Time"

    elif "addr1" in feature:
        return "Billing Address"

    elif "addr2" in feature:
        return "Billing Region"

    elif "dist1" in feature:
        return "Distance"

    elif "dist2" in feature:
        return "Distance Pattern"

    else:
        return feature


# Transform first 5 transactions
X_test_transformed = model.named_steps[
    "preprocessor"
].transform(X_test.iloc[:5])


# Convert to numeric
X_test_transformed = (
    X_test_transformed
    .toarray()
    .astype(float)
)


# Create SHAP explainer
explainer = shap.TreeExplainer(
    rf_model
)


# Calculate SHAP values
shap_values = explainer.shap_values(
    X_test_transformed
)


# Handle SHAP output format
if isinstance(shap_values, list):

    fraud_shap_values = shap_values[1]

else:

    if shap_values.ndim == 3:
        fraud_shap_values = shap_values[:, :, 1]
    else:
        fraud_shap_values = shap_values


# Feature names
feature_names = model.named_steps[
    "preprocessor"
].get_feature_names_out()


# ============================================================
# SHOW EXPLANATIONS
# ============================================================

for i in range(5):

    print(f"\nTransaction {i + 1}")
    print("-" * 50)

    print(
        f"Risk Score : "
        f"{y_probability[i]:.2%}"
    )

    print(
        f"Risk Level : "
        f"{risk_levels[i]}"
    )

    print(
        f"Action     : "
        f"{get_action(risk_levels[i])}"
    )

    # Create explanation dataframe
    explanation = pd.DataFrame({
        "Feature": feature_names,
        "SHAP": fraud_shap_values[i]
    })

    explanation["AbsoluteSHAP"] = (
        explanation["SHAP"].abs()
    )

    # Sort strongest signals first
    explanation = explanation.sort_values(
        by="AbsoluteSHAP",
        ascending=False
    )

    # Avoid showing duplicate business features
    shown_features = set()

    print("\nTop Risk Signals:")

    count = 0

    for _, row in explanation.iterrows():

        business_feature = get_business_feature(
            row["Feature"]
        )

        # Skip duplicates
        if business_feature in shown_features:
            continue

        shown_features.add(
            business_feature
        )

        if row["SHAP"] > 0:

            print(
                f"↑ {business_feature}"
                f" → increases model risk"
            )

        else:

            print(
                f"↓ {business_feature}"
                f" → decreases model risk"
            )

        count += 1

        if count == 5:
            break

# ==============================
# SAVE REAL DEMO CASES
# ==============================

demo_data = X_test.copy()
demo_data["ActualFraud"] = y_test.values
demo_data["Probability"] = model.predict_proba(X_test)[:, 1]

low_case = demo_data[demo_data["Probability"] < 0.40].sort_values("Probability").iloc[0]
medium_case = demo_data[
    (demo_data["Probability"] >= 0.40) &
    (demo_data["Probability"] < 0.70)
].iloc[0]
high_case = demo_data[demo_data["Probability"] >= 0.70].sort_values(
    "Probability", ascending=False
).iloc[0]

print("\n========== REAL DEMO CASES ==========")

print("\nLOW:")
print(low_case)

print("\nMEDIUM:")
print(medium_case)

print("\nHIGH:")
print(high_case)