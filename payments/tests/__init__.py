TRANSFER_CREATED_TEST_DATA = {
    "created": 1348360173,
    "data": {
        "object": {
            "amount": 455,
            "currency": "usd",
            "date": 1348876800,
            "description": None,
            "id": "tr_XXXXXXXXXXXX",
            "object": "transfer",
            "other_transfers": [],
            "status": "paid",
            "summary": {
                "adjustment_count": 0,
                "adjustment_fee_details": [],
                "adjustment_fees": 0,
                "adjustment_gross": 0,
                "charge_count": 1,
                "charge_fee_details": [{
                    "amount": 45,
                    "application": None,
                    "currency": "usd",
                    "description": None,
                    "type": "stripe_fee"
                }],
                "charge_fees": 45,
                "charge_gross": 500,
                "collected_fee_count": 0,
                "collected_fee_gross": 0,
                "currency": "usd",
                "net": 455,
                "refund_count": 0,
                "refund_fees": 0,
                "refund_gross": 0,
                "validation_count": 0,
                "validation_fees": 0
            }
        }
    },
    "id": "evt_XXXXXXXXXXXX",
    "livemode": True,
    "object": "event",
    "pending_webhooks": 1,
    "type": "transfer.created"
}

TRANSFER_CREATED_TEST_DATA2 = {
    "created": 1348360173,
    "data": {
        "object": {
            "amount": 1455,
            "currency": "usd",
            "date": 1348876800,
            "description": None,
            "id": "tr_XXXXXXXXXXX2",
            "object": "transfer",
            "other_transfers": [],
            "status": "paid",
            "summary": {
                "adjustment_count": 0,
                "adjustment_fee_details": [],
                "adjustment_fees": 0,
                "adjustment_gross": 0,
                "charge_count": 1,
                "charge_fee_details": [{
                    "amount": 45,
                    "application": None,
                    "currency": "usd",
                    "description": None,
                    "type": "stripe_fee"
                }],
                "charge_fees": 45,
                "charge_gross": 1500,
                "collected_fee_count": 0,
                "collected_fee_gross": 0,
                "currency": "usd",
                "net": 1455,
                "refund_count": 0,
                "refund_fees": 0,
                "refund_gross": 0,
                "validation_count": 0,
                "validation_fees": 0
            }
        }
    },
    "id": "evt_XXXXXXXXXXXY",
    "livemode": True,
    "object": "event",
    "pending_webhooks": 1,
    "type": "transfer.created"
}

TRANSFER_PENDING_TEST_DATA = {
    "created": 1375603198,
    "data": {
        "object": {
            "account": {
                "bank_name": "BANK OF AMERICA, N.A.",
                "country": "US",
                "fingerprint": "xxxxxxxxxx",
                "last4": "4444",
                "object": "bank_account",
                "validated": False
            },
            "amount": 941,
            "currency": "usd",
            "date": 1375747200,
            "description": "STRIPE TRANSFER",
            "fee": 0,
            "fee_details": [],
            "id": "tr_adlkj2l3kj23",
            "livemode": True,
            "object": "transfer",
            "recipient": None,
            "statement_descriptor": None,
            "status": "pending"
        }
    },
    "id": "evt_2l3kj232k223",
    "livemode": True,
    "object": "event",
    "pending_webhooks": 1,
    "request": None,
    "type": "transfer.created"
}
