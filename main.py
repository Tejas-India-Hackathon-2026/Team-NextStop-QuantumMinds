# services/transaction_pipeline.py

class SecureFlowPipeline:

    def __init__(
        self,
        upi_validator,
        duplicate_detector,
        rule_engine,
        time_analyzer,
        beneficiary_analyzer
    ):

        self.upi_validator = upi_validator
        self.duplicate_detector = duplicate_detector
        self.rule_engine = rule_engine
        self.time_analyzer = time_analyzer
        self.beneficiary_analyzer = beneficiary_analyzer

    def process(self, transaction):

        # 1. Validate UPI information
        upi_result = self.upi_validator(
            transaction["sender_upi"],
            transaction["receiver_upi"]
        )

        if not upi_result["valid"]:

            return {
                "status": "REJECTED",
                "stage": "UPI_VALIDATION",
                "reason": "Invalid UPI information."
            }

        # 2. Duplicate transaction check
        duplicate = self.duplicate_detector(
            transaction["user_id"],
            transaction["receiver_upi"],
            transaction["amount"]
        )

        if duplicate:

            return {
                "status": "REJECTED",
                "stage": "DUPLICATE_CHECK",
                "reason":
                    "Possible duplicate transaction."
            }

        # 3. Time analysis
        time_result = self.time_analyzer(
            transaction["transaction_hour"],
            transaction["normal_hours"]
        )

        # 4. Rule analysis
        rule_result = self.rule_engine(
            transaction
        )

        # 5. Beneficiary analysis
        beneficiary_result = self.beneficiary_analyzer(
            transaction["beneficiary_id"],
            transaction["known_beneficiaries"],
            transaction["beneficiary_age_days"]
        )

        return {
            "status": "ANALYZED",

            "time_analysis":
                time_result,

            "rule_analysis":
                rule_result,

            "beneficiary_analysis":
                beneficiary_result
        }