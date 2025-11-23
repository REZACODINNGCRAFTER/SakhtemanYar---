from dataclasses import dataclass
from typing import Union, List


# ---------------------------------------------------------
# Result Models
# ---------------------------------------------------------

@dataclass(frozen=True)
class BillValidationResult:
    bill_number: str
    payment_id: str
    fee: int
    bill_type: int


@dataclass(frozen=True)
class BillValidationError:
    code: int
    message: str


# ---------------------------------------------------------
# Iran Bill Validator — Improved Version
# ---------------------------------------------------------

class IranBillValidator:
    BILL_LENGTH = 13
    MIN_PAYMENT_ID = 7

    ERR_BILL = BillValidationError(-1, "Invalid bill number")
    ERR_PAYMENT = BillValidationError(-2, "Invalid payment ID")

    WEIGHTS = [
        2, 3, 4, 5, 6, 7, 2, 3, 4, 5, 6, 7,
        2, 3, 4, 5, 6, 7, 2, 3, 4, 5, 6, 7,
        2, 3
    ]

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    @classmethod
    def validate(cls, bill_number: str, payment_id: str) -> Union[BillValidationResult, BillValidationError]:

        if not cls._is_numeric(bill_number):
            return cls.ERR_BILL

        if not cls._is_numeric(payment_id):
            return cls.ERR_PAYMENT

        if len(bill_number) != cls.BILL_LENGTH:
            return cls.ERR_BILL

        if len(payment_id) < cls.MIN_PAYMENT_ID:
            return cls.ERR_PAYMENT

        padded_payment = payment_id.zfill(cls.BILL_LENGTH)

        bill_digits = cls._to_digits(bill_number)
        payment_digits = cls._to_digits(padded_payment)

        if len(bill_digits) != cls.BILL_LENGTH:
            return cls.ERR_BILL

        if len(payment_digits) != cls.BILL_LENGTH:
            return cls.ERR_PAYMENT

        bill_type = bill_digits[11]
        last = cls.BILL_LENGTH - 1

        # ------------------------------
        # 1) Bill checksum
        # ------------------------------
        if not cls._validate_checksum(bill_digits, last, 1, 12, bill_digits[last]):
            return cls.ERR_BILL

        # ------------------------------
        # 2) Payment checksum
        # ------------------------------
        if not cls._validate_checksum(payment_digits, last, 2, 11, payment_digits[last - 1]):
            return cls.ERR_PAYMENT

        # ------------------------------
        # 3) Combined checksum
        # ------------------------------
        combined = bill_number + padded_payment[5:12]
        combined_digits = cls._to_digits(combined)

        if len(combined_digits) != 20:
            return cls.ERR_PAYMENT

        if not cls._validate_checksum(combined_digits, 19, 0, 20, payment_digits[last]):
            return cls.ERR_PAYMENT

        # ------------------------------
        # 4) Fee calculation
        # ------------------------------
        amount = cls._safe_int(padded_payment[:8])
        if amount <= 0:
            return cls.ERR_PAYMENT

        fee = amount * 1000

        return BillValidationResult(
            bill_number=bill_number,
            payment_id=padded_payment,
            fee=fee,
            bill_type=bill_type,
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _safe_int(value: str) -> int:
        try:
            return int(value)
        except Exception:
            return 0

    @staticmethod
    def _is_numeric(value: str) -> bool:
        return value.isdigit()

    @classmethod
    def _to_digits(cls, s: str) -> List[int]:
        try:
            return [int(ch) for ch in s]
        except Exception:
            return []

    @classmethod
    def _checksum(cls, digits: List[int], reverse_index: int, start: int, length: int) -> int:
        # جلوگیری از خارج شدن ایندکس
        if reverse_index - (start + length - 1) < 0:
            return -1

        total = 0
        for i in range(length):
            idx = reverse_index - (start + i)
            total += digits[idx] * cls.WEIGHTS[i]

        result = 11 - (total % 11)
        return 0 if result > 9 else result

    @classmethod
    def _validate_checksum(cls, digits: List[int], reverse_index: int, start: int, length: int, target: int) -> bool:
        checksum_value = cls._checksum(digits, reverse_index, start, length)
        if checksum_value < 0:   # در صورت خطا در محاسبات
            return False
        return checksum_value == target
        
        
        
        result = IranBillValidator.validate("7721217800141", "5479201")

if isinstance(result, BillValidationResult):
    print("VALID:", result)
else:
    print("ERROR:", result)
