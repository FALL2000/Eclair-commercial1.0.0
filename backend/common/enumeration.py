"""Énumérations métier canoniques (cf. docs/SPECIFICATIONS_CONSOLIDEES.md §19.3).

Utiliser exclusivement ces valeurs dans les modèles, schémas et services.
"""
from enum import Enum


class FlowType(str, Enum):
    SALE = "SALE"
    PURCHASE = "PURCHASE"


class DocStage(str, Enum):
    QUOTE = "QUOTE"
    RFQ = "RFQ"
    ORDER = "ORDER"
    DELIVERY = "DELIVERY"
    RECEIPT = "RECEIPT"
    INVOICE = "INVOICE"
    BILL = "BILL"
    CREDIT_NOTE = "CREDIT_NOTE"


class DocStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"


class PaymentMethod(str, Enum):
    CASH = "CASH"
    MTN_MOMO = "MTN_MOMO"
    ORANGE_MONEY = "ORANGE_MONEY"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"
    CLIENT_CREDIT = "CLIENT_CREDIT"


class PaymentDirection(str, Enum):
    IN = "IN"
    OUT = "OUT"


class MovementType(str, Enum):
    SALE_OUT = "SALE_OUT"
    PURCHASE_IN = "PURCHASE_IN"
    PRODUCTION_IN = "PRODUCTION_IN"
    PRODUCTION_OUT = "PRODUCTION_OUT"
    SCRAP = "SCRAP"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    RETURN_IN = "RETURN_IN"
    RETURN_OUT = "RETURN_OUT"


class ItemType(str, Enum):
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    RAW_MATERIAL = "RAW_MATERIAL"


class PartnerType(str, Enum):
    CLIENT = "CLIENT"
    SUPPLIER = "SUPPLIER"
    BOTH = "BOTH"


class DeliveryMode(str, Enum):
    CLIENT_PICKUP = "CLIENT_PICKUP"
    COMPANY_DELIVERY = "COMPANY_DELIVERY"


class DeliveryStatus(str, Enum):
    PREPARING = "PREPARING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"


class PurchaseWorkflowMode(str, Enum):
    NONE = "NONE"
    DIRECT = "DIRECT"
    FULL_B2B = "FULL_B2B"


class StockTracking(str, Enum):
    NONE = "NONE"
    SIMPLE = "SIMPLE"
    SERIAL_NUMBER = "SERIAL_NUMBER"


class ProductionMode(str, Enum):
    NONE = "NONE"
    AUTO_DEDUCT = "AUTO_DEDUCT"
    WORKSHOP_ORDER = "WORKSHOP_ORDER"


class RecipeConsumptionMode(str, Enum):
    FIXED_RECIPE = "FIXED_RECIPE"
    ACTUAL_DECLARATION = "ACTUAL_DECLARATION"


class ProductionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"


class CashSessionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
