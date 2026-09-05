import joblib
import pandas as pd
import os
import shap


# ==================================================
# LOAD MODEL
# ==================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "fraud_model.pkl"
)

model = joblib.load(MODEL_PATH)


# ==================================================
# SHAP
# ==================================================

preprocessor = model.named_steps["preprocessor"]
rf_model = model.named_steps["classifier"]

feature_names = preprocessor.get_feature_names_out()

explainer = shap.TreeExplainer(rf_model)


# ==================================================
# BUSINESS FEATURE MAPPING
# ==================================================

def get_business_feature(feature):

    if feature.startswith("cat__ProductCD"):
        return "Product Category"

    if feature.startswith("cat__card4"):
        return "Card Type"

    if feature.startswith("cat__card6"):
        return "Card Category"

    if feature.startswith("cat__card1"):
        return "Card Identifier"

    if feature.startswith("cat__card2"):
        return "Card Information"

    if feature.startswith("cat__P_emaildomain"):
        return "Purchaser Email Domain"

    if feature.startswith("cat__R_emaildomain"):
        return "Recipient Email Domain"

    if feature.startswith("cat__DeviceType"):
        return "Device Type"

    if feature.startswith("cat__DeviceInfo"):
        return "Device Information"

    if feature.startswith("cat__id_30"):
        return "Operating System"

    if feature.startswith("cat__id_31"):
        return "Browser"

    if feature.startswith("cat__id_33"):
        return "Screen Resolution"

    if feature == "num__TransactionAmt":
        return "Transaction Amount"

    if feature == "num__LogTransactionAmt":
        return "Transaction Amount Pattern"

    if feature == "num__TransactionsLast10Min":
        return "Recent Transaction Velocity"

    if feature == "num__TransactionsLast1Hour":
        return "Hourly Transaction Velocity"

    if feature == "num__AmountLast1Hour":
        return "Recent Spending Amount"

    if feature == "num__PreviousTransactionCount":
        return "Previous Transaction History"

    if feature == "num__PreviousAverageAmount":
        return "Previous Average Spending"

    if feature == "num__PreviousMaxAmount":
        return "Previous Maximum Spending"

    if feature == "num__CurrentAmountVsPreviousAverage":
        return "Amount vs Previous Average"

    if feature == "num__TransactionHour":
        return "Transaction Hour"

    if feature == "num__TransactionDay":
        return "Transaction Day"

    if feature == "num__TransactionDT":
        return "Transaction Time"

    if feature == "num__addr1":
        return "Billing Address"

    if feature == "num__addr2":
        return "Billing Region"

    if feature == "num__dist1":
        return "Transaction Distance"

    if feature == "num__dist2":
        return "Distance Pattern"

    if feature == "num__DeviceInfoAvailableCount":
        return "Device Information Availability"

    if feature == "num__DeviceInfoMissing":
        return "Missing Device Information"

    if feature == "num__card3":
        return "Card Configuration"

    if feature == "num__card5":
        return "Card Level"

    return feature


# ==================================================
# PREDICT
# ==================================================

def predict_transaction(transaction):

    # Convert dictionary to DataFrame
    transaction_data = pd.DataFrame([transaction])

    # TransactionID is not a model feature
    model_data = transaction_data.drop(
        columns=["TransactionID"]
    )

    # ----------------------------------------------
    # FRAUD PROBABILITY
    # ----------------------------------------------

    probability = model.predict_proba(
        model_data
    )[0][1]

    # ----------------------------------------------
    # RISK DECISION
    # ----------------------------------------------

    if probability < 0.40:
        risk_level = "LOW"
        action = "ALLOW"

    elif probability < 0.70:
        risk_level = "MEDIUM"
        action = "VERIFY"

    else:
        risk_level = "HIGH"
        action = "REVIEW"

    # ----------------------------------------------
    # TRANSFORM FOR SHAP
    # ----------------------------------------------

    transformed_data = preprocessor.transform(
        model_data
    )

    if hasattr(transformed_data, "toarray"):
        transformed_data = transformed_data.toarray()

    transformed_data = transformed_data.astype(float)

    # ----------------------------------------------
    # SHAP
    # ----------------------------------------------

    shap_values = explainer.shap_values(
        transformed_data
    )

    if isinstance(shap_values, list):

        shap_for_fraud = shap_values[1][0]

    elif len(shap_values.shape) == 3:

        shap_for_fraud = shap_values[0, :, 1]

    else:

        shap_for_fraud = shap_values[0]

    # ----------------------------------------------
    # AGGREGATE SHAP
    # ----------------------------------------------

    aggregated = {}

    for feature, value in zip(
        feature_names,
        shap_for_fraud
    ):

        business_feature = get_business_feature(
            feature
        )

        if business_feature not in aggregated:
            aggregated[business_feature] = 0.0

        aggregated[business_feature] += float(value)

    # ----------------------------------------------
    # SORT
    # ----------------------------------------------

    sorted_features = sorted(
        aggregated.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    # ----------------------------------------------
    # TOP 5 REASONS
    # ----------------------------------------------

    reasons = []

    for feature, value in sorted_features[:5]:

        impact = (
            "HIGHER_RISK"
            if value > 0
            else "LOWER_RISK"
        )

        reasons.append({
            "feature": feature,
            "impact": impact,
            "shap_value": round(value, 4)
        })

    # ----------------------------------------------
    # RESPONSE
    # ----------------------------------------------

    return {
        "transaction_id": transaction["TransactionID"],
        "risk_score": round(float(probability), 4),
        "risk_percentage": f"{probability:.2%}",
        "risk_level": risk_level,
        "action": action,
        "reasons": reasons
    }