from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from ml_service import predict_transaction


app = FastAPI(
    title="AI Risk Manager API",
    description="Fraud risk scoring API",
    version="1.0"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# REQUEST MODEL
# ==========================================

class TransactionRequest(BaseModel):

    TransactionID: int

    TransactionAmt: float
    LogTransactionAmt: float

    TransactionsLast10Min: float
    TransactionsLast1Hour: float
    AmountLast1Hour: float

    PreviousTransactionCount: float
    PreviousAverageAmount: float
    PreviousMaxAmount: float
    CurrentAmountVsPreviousAverage: float

    TransactionDT: float
    TransactionHour: int
    TransactionDay: int

    ProductCD: str

    card1: float
    card2: Optional[float] = None
    card3: float
    card4: str
    card5: float
    card6: str

    addr1: Optional[float] = None
    addr2: Optional[float] = None

    dist1: Optional[float] = None
    dist2: Optional[float] = None

    P_emaildomain: str
    R_emaildomain: Optional[str] = None

    DeviceType: Optional[str] = None
    DeviceInfo: Optional[str] = None

    id_30: Optional[str] = None
    id_31: Optional[str] = None
    id_33: Optional[str] = None

    DeviceInfoAvailableCount: float
    DeviceInfoMissing: float


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model_loaded": True
    }


# ==========================================
# PREDICTION
# ==========================================

@app.post("/predict")
def predict(transaction: TransactionRequest):

    return predict_transaction(
        transaction.model_dump()
    )