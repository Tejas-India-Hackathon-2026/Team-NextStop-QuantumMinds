BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "authentication" (
	"authentication_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL UNIQUE,
	"authentication_required"	INTEGER DEFAULT 0,
	"authentication_method"	TEXT,
	"authentication_status"	TEXT DEFAULT 'NOT_REQUIRED',
	"verified_at"	TEXT,
	PRIMARY KEY("authentication_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE,
	CHECK("authentication_required" IN (0, 1)),
	CHECK("authentication_status" IN ('NOT_REQUIRED', 'PENDING', 'SUCCESS', 'FAILED'))
);
CREATE TABLE IF NOT EXISTS "behaviour_analysis" (
	"behaviour_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL UNIQUE,
	"amount_pattern_score"	REAL NOT NULL DEFAULT 0,
	"device_pattern_score"	REAL NOT NULL DEFAULT 0,
	"location_pattern_score"	REAL NOT NULL DEFAULT 0,
	"ml_fraud_probability"	REAL,
	"ml_risk_score"	REAL,
	"model_name"	TEXT,
	"model_version"	TEXT,
	"analysis_reason"	TEXT,
	PRIMARY KEY("behaviour_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE,
	CHECK("amount_pattern_score" >= 0 AND "amount_pattern_score" <= 100),
	CHECK("device_pattern_score" >= 0 AND "device_pattern_score" <= 100),
	CHECK("location_pattern_score" >= 0 AND "location_pattern_score" <= 100),
	CHECK("ml_fraud_probability" IS NULL OR ("ml_fraud_probability" >= 0 AND "ml_fraud_probability" <= 1)),
	CHECK("ml_risk_score" IS NULL OR ("ml_risk_score" >= 0 AND "ml_risk_score" <= 100))
);
CREATE TABLE IF NOT EXISTS "beneficiaries" (
	"beneficiary_id"	TEXT,
	"user_id"	TEXT NOT NULL,
	"beneficiary_name"	TEXT NOT NULL,
	"upi_id"	TEXT,
	"transaction_count"	INTEGER DEFAULT 0,
	"average_amount"	REAL DEFAULT 0,
	"last_transaction_time"	TEXT,
	"is_known"	INTEGER DEFAULT 1,
	PRIMARY KEY("beneficiary_id"),
	FOREIGN KEY("user_id") REFERENCES "users"("user_id") ON DELETE CASCADE,
	CHECK("transaction_count" >= 0),
	CHECK("average_amount" >= 0),
	CHECK("is_known" IN (0, 1))
);
CREATE TABLE IF NOT EXISTS "dynamic_questions" (
	"question_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL,
	"question"	TEXT NOT NULL,
	"expected_answer"	TEXT,
	"user_answer"	TEXT,
	"status"	TEXT DEFAULT 'PENDING',
	PRIMARY KEY("question_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE,
	CHECK("status" IN ('PENDING', 'CORRECT', 'INCORRECT'))
);
CREATE TABLE IF NOT EXISTS "final_answers" (
	"final_answer_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL UNIQUE,
	"final_decision"	TEXT NOT NULL,
	"final_message"	TEXT,
	"answered_at"	TEXT,
	PRIMARY KEY("final_answer_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE,
	CHECK("final_decision" IN ('ALLOW', 'BLOCK', 'PENDING_AUTHENTICATION'))
);
CREATE TABLE IF NOT EXISTS "independent_signals" (
	"signal_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL UNIQUE,
	"device_signal"	TEXT,
	"location_signal"	TEXT,
	"transaction_history_signal"	TEXT,
	"beneficiary_signal"	TEXT,
	"signal_result"	TEXT,
	PRIMARY KEY("signal_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "risk_analysis_data" (
	"risk_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL UNIQUE,
	"amount_flag"	INTEGER NOT NULL DEFAULT 0,
	"time_flag"	INTEGER NOT NULL DEFAULT 0,
	"frequency_flag"	INTEGER NOT NULL DEFAULT 0,
	"new_device_flag"	INTEGER NOT NULL DEFAULT 0,
	"unusual_location_flag"	INTEGER NOT NULL DEFAULT 0,
	"sudden_location_change_flag"	INTEGER NOT NULL DEFAULT 0,
	"unknown_beneficiary_flag"	INTEGER NOT NULL DEFAULT 0,
	"no_previous_transaction_flag"	INTEGER NOT NULL DEFAULT 0,
	"typical_amount_flag"	INTEGER NOT NULL DEFAULT 0,
	"risk_score"	INTEGER GENERATED ALWAYS AS (("amount_flag" * 10) + ("time_flag" * 7) + ("frequency_flag" * 12) + ("new_device_flag" * 15) + ("unusual_location_flag" * 15) + ("sudden_location_change_flag" * 6) + ("unknown_beneficiary_flag" * 12) + ("no_previous_transaction_flag" * 13) + ("typical_amount_flag" * 10)) STORED,
	"risk_level"	TEXT GENERATED ALWAYS AS (CASE WHEN (("amount_flag" * 10) + ("time_flag" * 7) + ("frequency_flag" * 12) + ("new_device_flag" * 15) + ("unusual_location_flag" * 15) + ("sudden_location_change_flag" * 6) + ("unknown_beneficiary_flag" * 12) + ("no_previous_transaction_flag" * 13) + ("typical_amount_flag" * 10)) <= 40 THEN 'LOW' WHEN(("amount_flag" * 10) + ("time_flag" * 7) + ("frequency_flag" * 12) + ("new_device_flag" * 15) + ("unusual_location_flag" * 15) + ("sudden_location_change_flag" * 6) + ("unknown_beneficiary_flag" * 12) + ("no_previous_transaction_flag" * 13) + ("typical_amount_flag" * 10)) <= 70 THEN 'MEDIUM' ELSE 'HIGH' END) STORED,
	"action"	TEXT GENERATED ALWAYS AS (CASE WHEN (("amount_flag" * 10) + ("time_flag" * 7) + ("frequency_flag" * 12) + ("new_device_flag" * 15) + ("unusual_location_flag" * 15) + ("sudden_location_change_flag" * 6) + ("unknown_beneficiary_flag" * 12) + ("no_previous_transaction_flag" * 13) + ("typical_amount_flag" * 10)) <= 40 THEN 'ALLOW' WHEN(("amount_flag" * 10) + ("time_flag" * 7) + ("frequency_flag" * 12) + ("new_device_flag" * 15) + ("unusual_location_flag" * 15) + ("sudden_location_change_flag" * 6) + ("unknown_beneficiary_flag" * 12) + ("no_previous_transaction_flag" * 13) + ("typical_amount_flag" * 10)) <= 70 THEN 'ALERT' ELSE 'BLOCK' END) STORED,
	PRIMARY KEY("risk_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE,
	CHECK("amount_flag" IN (0, 1)),
	CHECK("time_flag" IN (0, 1)),
	CHECK("frequency_flag" IN (0, 1)),
	CHECK("new_device_flag" IN (0, 1)),
	CHECK("unusual_location_flag" IN (0, 1)),
	CHECK("sudden_location_change_flag" IN (0, 1)),
	CHECK("unknown_beneficiary_flag" IN (0, 1)),
	CHECK("no_previous_transaction_flag" IN (0, 1)),
	CHECK("typical_amount_flag" IN (0, 1))
);
CREATE TABLE IF NOT EXISTS "risk_decisions" (
	"decision_id"	INTEGER,
	"transaction_id"	TEXT NOT NULL UNIQUE,
	"risk_score"	REAL NOT NULL,
	"risk_level"	TEXT NOT NULL,
	"action"	TEXT NOT NULL,
	"hold_slow"	INTEGER NOT NULL DEFAULT 0,
	"decision_reason"	TEXT,
	PRIMARY KEY("decision_id" AUTOINCREMENT),
	FOREIGN KEY("transaction_id") REFERENCES "transactions"("transaction_id") ON DELETE CASCADE,
	CHECK("risk_score" >= 0 AND "risk_score" <= 100),
	CHECK("risk_level" IN ('LOW', 'MEDIUM', 'HIGH')),
	CHECK("action" IN ('ALLOW', 'ALERT', 'BLOCK')),
	CHECK("hold_slow" IN (0, 1))
);
CREATE TABLE IF NOT EXISTS "risk_factor_definitions" (
	"factor_id"	INTEGER,
	"factor_name"	TEXT NOT NULL UNIQUE,
	"weight"	INTEGER NOT NULL,
	"description"	TEXT NOT NULL,
	PRIMARY KEY("factor_id"),
	CHECK("weight" >= 0)
);
CREATE TABLE IF NOT EXISTS "transactions" (
	"transaction_id"	TEXT,
	"user_id"	TEXT NOT NULL,
	"beneficiary_id"	TEXT,
	"amount"	REAL NOT NULL,
	"transaction_time"	TEXT NOT NULL,
	"device_id"	TEXT NOT NULL,
	"location"	TEXT NOT NULL,
	"previous_location"	TEXT,
	"status"	TEXT DEFAULT 'PENDING',
	"created_at"	TEXT DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("transaction_id"),
	FOREIGN KEY("beneficiary_id") REFERENCES "beneficiaries"("beneficiary_id"),
	FOREIGN KEY("user_id") REFERENCES "users"("user_id") ON DELETE CASCADE,
	CHECK("amount" >= 0),
	CHECK("status" IN ('PENDING', 'SUCCESS', 'FAILED', 'BLOCKED', 'HELD'))
);
CREATE TABLE IF NOT EXISTS "users" (
	"user_id"	TEXT,
	"name"	TEXT NOT NULL,
	"phone"	TEXT,
	"average_transaction"	REAL DEFAULT 0,
	"normal_start_time"	TEXT DEFAULT '08:00',
	"normal_end_time"	TEXT DEFAULT '23:00',
	"typical_daily_transactions"	INTEGER DEFAULT 0,
	"known_device"	TEXT,
	"common_location"	TEXT,
	"created_at"	TEXT DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("user_id")
);
INSERT INTO "authentication" VALUES (1,'T002',1,'Behavioural Authentication','PENDING',NULL);
INSERT INTO "authentication" VALUES (2,'T005',1,'Behavioural Authentication','PENDING',NULL);
INSERT INTO "beneficiaries" VALUES ('B001','U001','Mom','mom@upi',20,1800.0,'2026-08-19 18:30',1);
INSERT INTO "beneficiaries" VALUES ('B002','U001','Rahul','rahul@upi',15,2400.0,'2026-08-18 20:10',1);
INSERT INTO "beneficiaries" VALUES ('B003','U002','Rahul','rahul@upi',12,2000.0,'2026-08-19 19:20',1);
INSERT INTO "beneficiaries" VALUES ('B004','U003','Amit','amit@upi',8,2200.0,'2026-08-18 18:10',1);
INSERT INTO "beneficiaries" VALUES ('B005','U004','Priya','priya@upi',18,1600.0,'2026-08-19 17:45',1);
INSERT INTO "dynamic_questions" VALUES (1,'T002','Who is your most frequently used beneficiary?','Mom',NULL,'PENDING');
INSERT INTO "dynamic_questions" VALUES (2,'T005','Who is your most frequently used beneficiary?','Rahul',NULL,'PENDING');
INSERT INTO "independent_signals" VALUES (1,'T002','NEW_DEVICE','NORMAL_LOCATION','HIGH_FREQUENCY','KNOWN_BENEFICIARY','AUTHENTICATION_REQUIRED');
INSERT INTO "independent_signals" VALUES (2,'T005','NEW_DEVICE','NORMAL_LOCATION','HIGH_FREQUENCY','KNOWN_BENEFICIARY','AUTHENTICATION_REQUIRED');
INSERT INTO "risk_analysis_data" VALUES (1,'T001',0,0,0,0,0,0,0,0,0,0,'LOW','ALLOW');
INSERT INTO "risk_analysis_data" VALUES (2,'T002',1,1,1,1,0,0,0,0,0,44,'MEDIUM','ALERT');
INSERT INTO "risk_analysis_data" VALUES (3,'T003',1,1,1,1,1,1,1,1,1,100,'HIGH','BLOCK');
INSERT INTO "risk_analysis_data" VALUES (4,'T004',0,0,0,0,1,0,0,0,0,15,'LOW','ALLOW');
INSERT INTO "risk_analysis_data" VALUES (5,'T005',1,1,1,1,0,0,0,0,0,44,'MEDIUM','ALERT');
INSERT INTO "risk_analysis_data" VALUES (6,'T006',1,1,1,1,1,1,1,0,0,77,'HIGH','BLOCK');
INSERT INTO "risk_analysis_data" VALUES (7,'T007',1,0,1,0,0,0,0,0,1,32,'LOW','ALLOW');
INSERT INTO "risk_analysis_data" VALUES (8,'T008',1,1,1,1,1,1,1,1,1,100,'HIGH','BLOCK');
INSERT INTO "risk_factor_definitions" VALUES (1,'Amount',10,'Unusual transaction amount');
INSERT INTO "risk_factor_definitions" VALUES (2,'Time',7,'Transaction occurs at an unusual time');
INSERT INTO "risk_factor_definitions" VALUES (3,'Frequency',12,'Unusually high transaction frequency');
INSERT INTO "risk_factor_definitions" VALUES (4,'New Device',15,'Transaction originates from a new device');
INSERT INTO "risk_factor_definitions" VALUES (5,'Unusual Location',15,'Transaction originates from an unusual location');
INSERT INTO "risk_factor_definitions" VALUES (6,'Sudden Location Change',6,'Sudden change from previous transaction location');
INSERT INTO "risk_factor_definitions" VALUES (7,'Unknown Beneficiary',12,'Beneficiary is unknown to the user');
INSERT INTO "risk_factor_definitions" VALUES (8,'No Previous Transaction',13,'No previous transaction exists with beneficiary');
INSERT INTO "risk_factor_definitions" VALUES (9,'Typical Amount With Beneficiary',10,'Transaction amount is not typical for this beneficiary');
INSERT INTO "transactions" VALUES ('T001','U001','B001',1800.0,'2026-08-20 18:30','Android-SOUMADIP-01','Kolkata','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T002','U001','B001',8500.0,'2026-08-20 02:30','Unknown-Device-01','Kolkata','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T003','U001',NULL,25000.0,'2026-08-20 03:15','Unknown-Device-99','Delhi','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T004','U002','B003',1900.0,'2026-08-20 18:20','Android-SHUBHAM-01','Haldia','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T005','U002','B003',9500.0,'2026-08-20 02:45','Unknown-Device-02','Kolkata','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T006','U003','B004',18000.0,'2026-08-20 03:10','Unknown-Device-03','Delhi','Haldia','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T007','U004','B005',3000.0,'2026-08-20 17:30','Android-TRIDIP-01','Kolkata','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "transactions" VALUES ('T008','U004',NULL,30000.0,'2026-08-20 03:30','Unknown-Device-99','Mumbai','Kolkata','PENDING','2026-08-20 10:07:29');
INSERT INTO "users" VALUES ('U001','Soumadip Das','XXXXXXXXXX',1850.0,'08:00','23:00',3,'Android-SOUMADIP-01','Kolkata','2026-08-20 10:07:29');
INSERT INTO "users" VALUES ('U002','Shubham Paul','XXXXXXXXXX',2100.0,'08:00','23:00',4,'Android-SHUBHAM-01','Kolkata','2026-08-20 10:07:29');
INSERT INTO "users" VALUES ('U003','Shubham Mukherjee','XXXXXXXXXX',2500.0,'08:00','23:00',3,'Android-MUKHERJEE-01','Haldia','2026-08-20 10:07:29');
INSERT INTO "users" VALUES ('U004','Tridip Debroy','XXXXXXXXXX',1750.0,'08:00','23:00',3,'Android-TRIDIP-01','Kolkata','2026-08-20 10:07:29');
CREATE VIEW behaviour_engine AS

SELECT

    t.transaction_id,

    t.user_id,

    u.name AS user_name,

    t.beneficiary_id,

    b.beneficiary_name,

    t.amount,

    t.transaction_datetime,

    t.device,

    t.location,

    t.status,


    -- ========================================================
    -- BEHAVIOURAL PATTERNS
    -- ========================================================

    ba.amount_pattern_score,

    ba.device_pattern_score,

    ba.location_pattern_score,


    -- ========================================================
    -- ML OUTPUT
    -- ========================================================

    ba.ml_fraud_probability,

    ba.ml_risk_score,

    ba.model_name,

    ba.model_version,

    ba.analysis_reason


FROM behaviour_analysis ba

JOIN transactions t
    ON ba.transaction_id = t.transaction_id

JOIN users u
    ON t.user_id = u.user_id

JOIN beneficiaries b
    ON t.beneficiary_id = b.beneficiary_id;
CREATE VIEW fraud_alerts AS

SELECT

    transaction_id,

    user_name,

    amount,

    device_id,

    location,

    risk_score,

    risk_level,

    action

FROM risk_analysis

WHERE risk_level IN
(
    'MEDIUM',
    'HIGH'
)

ORDER BY risk_score DESC;
CREATE VIEW risk_analysis AS

SELECT

    t.transaction_id,

    t.user_id,

    u.name AS user_name,

    t.beneficiary_id,

    b.beneficiary_name,

    t.amount,

    t.transaction_time,

    t.device_id,

    t.location,

    t.previous_location,

    t.status,


    -- Risk factor flags

    r.amount_flag,

    r.time_flag,

    r.frequency_flag,

    r.new_device_flag,

    r.unusual_location_flag,

    r.sudden_location_change_flag,

    r.unknown_beneficiary_flag,

    r.no_previous_transaction_flag,

    r.typical_amount_flag,


    -- Final result

    r.risk_score,

    r.risk_level,

    r.action

FROM risk_analysis_data r

JOIN transactions t
    ON r.transaction_id = t.transaction_id

JOIN users u
    ON t.user_id = u.user_id

LEFT JOIN beneficiaries b
    ON t.beneficiary_id = b.beneficiary_id;
CREATE VIEW security_flow AS

SELECT

    r.transaction_id,

    r.user_name,

    r.amount,

    r.device_id,

    r.location,

    r.risk_score,

    r.risk_level,

    r.action,


    CASE

        WHEN r.risk_level = 'LOW'

            THEN 'ALLOW'


        WHEN r.risk_level = 'MEDIUM'

            THEN 'ALERT → HOLD/SLOW → AUTHENTICATION'


        WHEN r.risk_level = 'HIGH'

            THEN 'BLOCK'

    END AS security_flow,


    a.authentication_status,

    i.signal_result,

    q.status AS dynamic_question_status,

    f.final_decision

FROM risk_analysis r

LEFT JOIN authentication a
    ON r.transaction_id = a.transaction_id

LEFT JOIN independent_signals i
    ON r.transaction_id = i.transaction_id

LEFT JOIN dynamic_questions q
    ON r.transaction_id = q.transaction_id

LEFT JOIN final_answers f
    ON r.transaction_id = f.transaction_id;
COMMIT;
