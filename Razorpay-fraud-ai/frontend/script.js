// ==========================================
// ELEMENTS
// ==========================================

const form =
    document.getElementById("transactionForm");

const analyzeButton =
    document.getElementById("analyzeButton");

const transactionIdElement =
    document.getElementById("transactionId");

const riskScoreElement =
    document.getElementById("riskScore");

const riskBadgeElement =
    document.getElementById("riskBadge");

const riskActionElement =
    document.getElementById("riskAction");

const reasonsContainer =
    document.getElementById("reasonsContainer");
    


// ==========================================
// RISK SIGNAL ELEMENTS
// ==========================================

const transactionSignalElement =
    document.getElementById("transactionSignal");

const velocitySignalElement =
    document.getElementById("velocitySignal");

const historySignalElement =
    document.getElementById("historySignal");

const deviceSignalElement =
    document.getElementById("deviceSignal");

const cardSignalElement =
    document.getElementById("cardSignal");

const locationSignalElement =
    document.getElementById("locationSignal");


// ==========================================
// SELECTED DEMO TRANSACTION
// ==========================================

let selectedDemoTransaction = null;


// ==========================================
// GENERATE TRANSACTION ID
// ==========================================

function generateTransactionId() {

    return `TXN-${Date.now()}`;

}


// ==========================================
// CLEAR DEMO WHEN USER MANUALLY EDITS
// ==========================================

form.addEventListener(
    "input",
    function () {

        selectedDemoTransaction = null;

    }
);


// ==========================================
// UPDATE RISK SIGNALS
// ==========================================

function updateRiskSignals(transaction) {


    // ======================================
    // TRANSACTION BEHAVIOR
    // ======================================

    const amount =
        Number(transaction.TransactionAmt || 0);

    const previousAverage =
        Number(
            transaction.PreviousAverageAmount || 0
        );

    let transactionStatus = "Normal";

    if (previousAverage > 0) {

        const ratio =
            amount / previousAverage;

        if (ratio >= 3) {

            transactionStatus =
                "Highly Unusual";

        } else if (ratio >= 1.5) {

            transactionStatus =
                "Elevated";

        } else {

            transactionStatus =
                "Normal";

        }

    }


    transactionSignalElement.textContent =
        transactionStatus;


    // ======================================
    // TRANSACTION VELOCITY
    // ======================================

    const last10Min =
        Number(
            transaction.TransactionsLast10Min || 0
        );

    const lastHour =
        Number(
            transaction.TransactionsLast1Hour || 0
        );

    let velocityStatus = "Normal";

    if (
        last10Min >= 3 ||
        lastHour >= 5
    ) {

        velocityStatus = "High";

    } else if (
        last10Min >= 1 ||
        lastHour >= 2
    ) {

        velocityStatus = "Elevated";

    } else {

        velocityStatus = "Normal";

    }


    velocitySignalElement.textContent =
        velocityStatus;


    // ======================================
    // HISTORICAL BEHAVIOR
    // ======================================

    let historyStatus = "Limited";

    if (previousAverage > 0) {

        const ratio =
            amount / previousAverage;

        if (ratio >= 3) {

            historyStatus =
                "Highly Unusual";

        } else if (ratio >= 1.5) {

            historyStatus =
                "Elevated";

        } else {

            historyStatus =
                "Consistent";

        }

    }


    historySignalElement.textContent =
        historyStatus;


    // ======================================
    // DEVICE / IDENTITY
    // ======================================

    let deviceSignals = 0;


    if (transaction.DeviceType) {

        deviceSignals++;

    }


    if (transaction.DeviceInfo) {

        deviceSignals++;

    }


    if (transaction.id_30) {

        deviceSignals++;

    }


    if (transaction.id_31) {

        deviceSignals++;

    }


    if (transaction.id_33) {

        deviceSignals++;

    }


    let deviceStatus = "Limited";


    if (deviceSignals >= 4) {

        deviceStatus =
            "Rich Signals";

    } else if (deviceSignals >= 2) {

        deviceStatus =
            "Available";

    } else {

        deviceStatus =
            "Limited";

    }


    deviceSignalElement.textContent =
        deviceStatus;


    // ======================================
    // CARD / PAYMENT
    // ======================================

    let cardSignals = 0;


    if (transaction.card1 != null) {

        cardSignals++;

    }


    if (transaction.card2 != null) {

        cardSignals++;

    }


    if (transaction.card3 != null) {

        cardSignals++;

    }


    if (transaction.card4) {

        cardSignals++;

    }


    if (transaction.card5 != null) {

        cardSignals++;

    }


    if (transaction.card6) {

        cardSignals++;

    }


    let cardStatus = "Limited";


    if (cardSignals >= 5) {

        cardStatus =
            "Rich Signals";

    } else if (cardSignals >= 3) {

        cardStatus =
            "Available";

    } else {

        cardStatus =
            "Limited";

    }


    cardSignalElement.textContent =
        cardStatus;


    // ======================================
    // ADDRESS / LOCATION
    // ======================================

    let locationSignals = 0;


    if (transaction.addr1 != null) {

        locationSignals++;

    }


    if (transaction.addr2 != null) {

        locationSignals++;

    }


    if (transaction.dist1 != null) {

        locationSignals++;

    }


    if (transaction.dist2 != null) {

        locationSignals++;

    }


    let locationStatus = "Limited";


    if (locationSignals >= 3) {

        locationStatus =
            "Available";

    } else if (locationSignals >= 1) {

        locationStatus =
            "Partial";

    } else {

        locationStatus =
            "Limited";

    }


    locationSignalElement.textContent =
        locationStatus;

}


// ==========================================
// FORM SUBMIT
// ==========================================

form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        // ======================================
        // BUTTON STATE
        // ======================================

        analyzeButton.disabled = true;

        analyzeButton.textContent =
            "Analyzing...";


        reasonsContainer.innerHTML = `
            <p class="placeholder">
                AI Risk Engine is analyzing the transaction...
            </p>
        `;


        // ======================================
        // TRANSACTION ID
        // ======================================

        const transactionId =
            generateTransactionId();


        // ======================================
        // CREATE TRANSACTION
        // ======================================

        let transaction;


        // ======================================
        // REAL DEMO CASE
        // ======================================

        if (
            selectedDemoTransaction !== null
        ) {

            transaction = {

                ...selectedDemoTransaction,

                TransactionID:
                    Number(
                        transactionId
                            .replace("TXN-", "")
                            .slice(-9)
                    )

            };

        }


        // ======================================
        // MANUAL TRANSACTION
        // ======================================

        else {

            const amount =
                Number(
                    document.getElementById(
                        "TransactionAmt"
                    ).value
                );


            const hour =
                Number(
                    document.getElementById(
                        "TransactionHour"
                    ).value
                );


            const product =
                document.getElementById(
                    "ProductCD"
                ).value;


            const cardType =
                document.getElementById(
                    "card4"
                ).value;


            const cardCategory =
                document.getElementById(
                    "card6"
                ).value;


            const deviceType =
                document.getElementById(
                    "DeviceType"
                ).value;


            const browser =
                document.getElementById(
                    "id_31"
                ).value;


            const operatingSystem =
                document.getElementById(
                    "id_30"
                ).value;


            const screenResolution =
                document.getElementById(
                    "id_33"
                ).value;


            const emailDomain =
                document.getElementById(
                    "P_emaildomain"
                ).value;


            transaction = {

                TransactionID:
                    Number(
                        transactionId
                            .replace("TXN-", "")
                            .slice(-9)
                    ),

                TransactionAmt:
                    amount,

                LogTransactionAmt:
                    Math.log(amount + 1),

                TransactionsLast10Min:
                    1,

                TransactionsLast1Hour:
                    3,

                AmountLast1Hour:
                    6500,

                PreviousTransactionCount:
                    8,

                PreviousAverageAmount:
                    900,

                PreviousMaxAmount:
                    2200,

                CurrentAmountVsPreviousAverage:
                    amount / 900,

                TransactionDT:
                    86400,

                TransactionHour:
                    hour,

                TransactionDay:
                    1,

                ProductCD:
                    product,

                card1:
                    10000,

                card2:
                    111,

                card3:
                    150,

                card4:
                    cardType,

                card5:
                    226,

                card6:
                    cardCategory,

                addr1:
                    315,

                addr2:
                    87,

                dist1:
                    10,

                dist2:
                    20,

                P_emaildomain:
                    emailDomain,

                R_emaildomain:
                    emailDomain,

                DeviceType:
                    deviceType,

                DeviceInfo:
                    "Windows",

                id_30:
                    operatingSystem,

                id_31:
                    browser,

                id_33:
                    screenResolution,

                DeviceInfoAvailableCount:
                    5,

                DeviceInfoMissing:
                    0

            };

        }


        // ======================================
        // UPDATE SIGNAL ANALYSIS
        // ======================================

        updateRiskSignals(transaction);


        // ======================================
        // DEBUG
        // ======================================

        console.log(
            "Sending transaction:",
            transaction
        );


        // ======================================
        // SEND TO SPRING BOOT
        // ======================================

        try {

            const response =
                await fetch(
                    "http://127.0.0.1:8080/api/predict",
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                transaction
                            )

                    }
                );


            // ==================================
            // API ERROR
            // ==================================

            if (!response.ok) {

                const errorText =
                    await response.text();

                throw new Error(
                    `API Error: ${response.status} ${errorText}`
                );

            }


            // ==================================
            // RESULT
            // ==================================

            const result =
                await response.json();


            console.log(
                "AI Risk Result:",
                result
            );


            displayResult(result);

        }


        catch (error) {

            console.error(error);


            reasonsContainer.innerHTML = `
                <p style="color:#c62828;">
                    Unable to connect to AI Risk Engine.
                    Make sure Spring Boot and FastAPI
                    are running.
                </p>
            `;

        }


        finally {

            analyzeButton.disabled =
                false;

            analyzeButton.textContent =
                "Analyze Transaction";

        }

    }
);


// ==========================================
// DISPLAY RESULT
// ==========================================

function displayResult(result) {

    // ================================
    // TRANSACTION ID
    // ================================

    transactionIdElement.textContent =
        result.transaction_id;


    // ================================
    // RISK SCORE
    // ================================

    riskScoreElement.textContent =
        result.risk_percentage;


    // ================================
    // RISK LEVEL
    // ================================

    riskBadgeElement.textContent =
        result.risk_level;

    riskBadgeElement.classList.remove(
        "low",
        "medium",
        "high"
    );

    riskBadgeElement.classList.add(
        result.risk_level.toLowerCase()
    );


    // ================================
    // ACTION
    // ================================

    riskActionElement.textContent =
        result.action;


    // ================================
    // SHAP EXPLANATION
    // ================================

    reasonsContainer.innerHTML = "";

    const reasons = result.reasons || [];

    if (reasons.length === 0) {

        reasonsContainer.innerHTML = `
            <div class="empty-state">
                <span>◈</span>
                <p>
                    No explanation available.
                </p>
            </div>
        `;

        return;
    }


    const shapList =
        document.createElement("div");

    shapList.className = "shap-list";


    // Find largest SHAP value for bar scaling

    const maxImpact = Math.max(
        ...reasons.map(reason =>
            Math.abs(Number(reason.shap_value || 0))
        )
    );


    reasons.forEach(function(reason) {

        const shapValue =
            Number(reason.shap_value || 0);

        const isHigher =
            reason.impact === "HIGHER_RISK";

        const arrow =
            isHigher ? "↑" : "↓";

        const width =
            maxImpact > 0
                ? Math.max(
                    8,
                    (Math.abs(shapValue) / maxImpact) * 100
                )
                : 8;


        const card =
            document.createElement("div");

        card.className = "shap-card";


        card.innerHTML = `

            <div class="shap-top">

                <div class="shap-feature">

                    <span class="shap-direction ${
                        isHigher
                            ? "positive"
                            : "negative"
                    }">

                        ${arrow}

                    </span>

                    <span>
                        ${reason.feature}
                    </span>

                </div>


                <span class="shap-value ${
                    isHigher
                        ? "positive"
                        : "negative"
                }">

                    ${shapValue > 0 ? "+" : ""}
                    ${shapValue.toFixed(4)}

                </span>

            </div>


            <div class="shap-description">

                ${
                    isHigher
                        ? "Contribution toward higher fraud risk"
                        : "Contribution toward lower fraud risk"
                }

            </div>


            <div class="shap-bar">

                <div
                    class="shap-bar-fill ${
                        isHigher
                            ? "positive"
                            : "negative"
                    }"
                    style="width:${width}%">
                </div>

            </div>

        `;


        shapList.appendChild(card);

    });


    reasonsContainer.appendChild(shapList);
}


// ==========================================
// DEMO SCENARIOS
// ==========================================

function loadDemo(type) {


    const demos = {


        // ==================================
        // LOW-RISK REAL TEST CASE
        // 21.31% → LOW → ALLOW
        // ==================================

        normal: {

            TransactionAmt:
                57.95,

            LogTransactionAmt:
                4.07669,

            TransactionsLast10Min:
                0,

            TransactionsLast1Hour:
                0,

            AmountLast1Hour:
                0,

            PreviousTransactionCount:
                68,

            PreviousAverageAmount:
                94.648088,

            PreviousMaxAmount:
                424.97,

            CurrentAmountVsPreviousAverage:
                0.612268,

            TransactionDT:
                695131,

            TransactionHour:
                1,

            TransactionDay:
                8,

            ProductCD:
                "W",

            card1:
                17131,

            card2:
                111,

            card3:
                150,

            card4:
                "mastercard",

            card5:
                224,

            card6:
                "debit",

            addr1:
                264,

            addr2:
                87,

            dist1:
                0,

            dist2:
                null,

            P_emaildomain:
                "sbcglobal.net",

            R_emaildomain:
                null,

            DeviceType:
                null,

            DeviceInfo:
                null,

            id_30:
                null,

            id_31:
                null,

            id_33:
                null,

            DeviceInfoAvailableCount:
                0,

            DeviceInfoMissing:
                1

        },


        // ==================================
        // MEDIUM-RISK REAL TEST CASE
        // 46.81% → MEDIUM → VERIFY
        // ==================================

        suspicious: {

            TransactionAmt:
                107.95,

            LogTransactionAmt:
                4.690889,

            TransactionsLast10Min:
                0,

            TransactionsLast1Hour:
                1,

            AmountLast1Hour:
                923.07,

            PreviousTransactionCount:
                3226,

            PreviousAverageAmount:
                189.434934,

            PreviousMaxAmount:
                3152.95,

            CurrentAmountVsPreviousAverage:
                0.569853,

            TransactionDT:
                7864752,

            TransactionHour:
                0,

            TransactionDay:
                91,

            ProductCD:
                "W",

            card1:
                7585,

            card2:
                553,

            card3:
                150,

            card4:
                "visa",

            card5:
                226,

            card6:
                "credit",

            addr1:
                264,

            addr2:
                87,

            dist1:
                19,

            dist2:
                null,

            P_emaildomain:
                "aol.com",

            R_emaildomain:
                null,

            DeviceType:
                null,

            DeviceInfo:
                null,

            id_30:
                null,

            id_31:
                null,

            id_33:
                null,

            DeviceInfoAvailableCount:
                0,

            DeviceInfoMissing:
                1

        },


        // ==================================
        // HIGH-RISK REAL TEST CASE
        // 87.43% → HIGH → REVIEW
        // Actual Fraud = 1
        // ==================================

        high: {

            TransactionAmt:
                9.305,

            LogTransactionAmt:
                2.332629,

            TransactionsLast10Min:
                0,

            TransactionsLast1Hour:
                4,

            AmountLast1Hour:
                163.643,

            PreviousTransactionCount:
                509,

            PreviousAverageAmount:
                263.75064,

            PreviousMaxAmount:
                2885.95,

            CurrentAmountVsPreviousAverage:
                0.03528,

            TransactionDT:
                5866246,

            TransactionHour:
                21,

            TransactionDay:
                67,

            ProductCD:
                "C",

            card1:
                15063,

            card2:
                null,

            card3:
                150,

            card4:
                "visa",

            card5:
                226,

            card6:
                "credit",

            addr1:
                null,

            addr2:
                null,

            dist1:
                null,

            dist2:
                null,

            P_emaildomain:
                "anonymous.com",

            R_emaildomain:
                "anonymous.com",

            DeviceType:
                "mobile",

            DeviceInfo:
                "hi6210sft Build/MRA58K",

            id_30:
                null,

            id_31:
                "chrome 64.0 for android",

            id_33:
                null,

            DeviceInfoAvailableCount:
                3,

            DeviceInfoMissing:
                0

        }

    };


    // ======================================
    // SELECT DEMO
    // ======================================

    const d =
        demos[type];


    if (!d) {

        console.error(
            "Unknown demo type:",
            type
        );

        return;

    }


    selectedDemoTransaction =
        d;


    // ======================================
    // DISPLAY VALUES
    // ======================================

    document.getElementById(
        "TransactionAmt"
    ).value =
        d.TransactionAmt;


    document.getElementById(
        "TransactionHour"
    ).value =
        d.TransactionHour;


    document.getElementById(
        "ProductCD"
    ).value =
        d.ProductCD;


    document.getElementById(
        "card4"
    ).value =
        d.card4;


    document.getElementById(
        "card6"
    ).value =
        d.card6;


    document.getElementById(
        "DeviceType"
    ).value =
        d.DeviceType ??
        "Not Available";


    document.getElementById(
        "id_31"
    ).value =
        d.id_31 ??
        "Not Available";


    document.getElementById(
        "id_30"
    ).value =
        d.id_30 ??
        "Not Available";


    document.getElementById(
        "id_33"
    ).value =
        d.id_33 ??
        "Not Available";


    document.getElementById(
        "P_emaildomain"
    ).value =
        d.P_emaildomain ??
        "Not Available";


    // ======================================
    // RUN DEMO WITHOUT HTML VALIDATION
    // ======================================

    form.dispatchEvent(
        new Event(
            "submit",
            {
                bubbles: true,
                cancelable: true
            }
        )
    );

}