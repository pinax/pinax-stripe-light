from .base import Webhook


class AccountUpdatedWebhook(Webhook):
    name = "account.updated"
    description = "Occurs whenever an account status or property has changed."


class AccountApplicationDeauthorizeWebhook(Webhook):
    name = "account.application.deauthorized"
    description = "Occurs whenever a user deauthorizes an application. Sent to the related application only."


class AccountExternalAccountCreatedWebhook(Webhook):
    name = "account.external_account.created"
    description = "Occurs whenever an external account is created."


class AccountExternalAccountDeletedWebhook(Webhook):
    name = "account.external_account.deleted"
    description = "Occurs whenever an external account is deleted."


class AccountExternalAccountUpdatedWebhook(Webhook):
    name = "account.external_account.updated"
    description = "Occurs whenever an external account is updated."


class ApplicationFeeCreatedWebhook(Webhook):
    name = "application_fee.created"
    description = "Occurs whenever an application fee is created on a charge."


class ApplicationFeeRefundedWebhook(Webhook):
    name = "application_fee.refunded"
    description = "Occurs whenever an application fee is refunded, whether from refunding a charge or from refunding the application fee directly, including partial refunds."


class ApplicationFeeRefundUpdatedWebhook(Webhook):
    name = "application_fee.refund.updated"
    description = "Occurs whenever an application fee refund is updated."


class BalanceAvailableWebhook(Webhook):
    name = "balance.available"
    description = "Occurs whenever your Stripe balance has been updated (e.g. when a charge collected is available to be paid out). By default, Stripe will automatically transfer any funds in your balance to your bank account on a daily basis."


class BitcoinReceiverCreatedWebhook(Webhook):
    name = "bitcoin.receiver.created"
    description = "Occurs whenever a receiver has been created."


class BitcoinReceiverFilledWebhook(Webhook):
    name = "bitcoin.receiver.filled"
    description = "Occurs whenever a receiver is filled (that is, when it has received enough bitcoin to process a payment of the same amount)."


class BitcoinReceiverUpdatedWebhook(Webhook):
    name = "bitcoin.receiver.updated"
    description = "Occurs whenever a receiver is updated."


class BitcoinReceiverTransactionCreatedWebhook(Webhook):
    name = "bitcoin.receiver.transaction.created"
    description = "Occurs whenever bitcoin is pushed to a receiver."


class ChargeCapturedWebhook(Webhook):
    name = "charge.captured"
    description = "Occurs whenever a previously uncaptured charge is captured."


class ChargeFailedWebhook(Webhook):
    name = "charge.failed"
    description = "Occurs whenever a failed charge attempt occurs."


class ChargeRefundedWebhook(Webhook):
    name = "charge.refunded"
    description = "Occurs whenever a charge is refunded, including partial refunds."


class ChargeSucceededWebhook(Webhook):
    name = "charge.succeeded"
    description = "Occurs whenever a new charge is created and is successful."


class ChargeUpdatedWebhook(Webhook):
    name = "charge.updated"
    description = "Occurs whenever a charge description or metadata is updated."


class ChargeDisputeClosedWebhook(Webhook):
    name = "charge.dispute.closed"
    description = "Occurs when the dispute is resolved and the dispute status changes to won or lost."


class ChargeDisputeCreatedWebhook(Webhook):
    name = "charge.dispute.created"
    description = "Occurs whenever a customer disputes a charge with their bank (chargeback)."


class ChargeDisputeFundsReinstatedWebhook(Webhook):
    name = "charge.dispute.funds_reinstated"
    description = "Occurs when funds are reinstated to your account after a dispute is won."


class ChargeDisputeFundsWithdrawnWebhook(Webhook):
    name = "charge.dispute.funds_withdrawn"
    description = "Occurs when funds are removed from your account due to a dispute."


class ChargeDisputeUpdatedWebhook(Webhook):
    name = "charge.dispute.updated"
    description = "Occurs when the dispute is updated (usually with evidence)."


class CouponCreatedWebhook(Webhook):
    name = "coupon.created"
    description = "Occurs whenever a coupon is created."


class CouponDeletedWebhook(Webhook):
    name = "coupon.deleted"
    description = "Occurs whenever a coupon is deleted."


class CouponUpdatedWebhook(Webhook):
    name = "coupon.updated"
    description = "Occurs whenever a coupon is updated."


class CustomerCreatedWebhook(Webhook):
    name = "customer.created"
    description = "Occurs whenever a new customer is created."


class CustomerDeletedWebhook(Webhook):
    name = "customer.deleted"
    description = "Occurs whenever a customer is deleted."


class CustomerUpdatedWebhook(Webhook):
    name = "customer.updated"
    description = "Occurs whenever any property of a customer changes."


class CustomerDiscountCreatedWebhook(Webhook):
    name = "customer.discount.created"
    description = "Occurs whenever a coupon is attached to a customer."


class CustomerDiscountDeletedWebhook(Webhook):
    name = "customer.discount.deleted"
    description = "Occurs whenever a customer's discount is removed."


class CustomerDiscountUpdatedWebhook(Webhook):
    name = "customer.discount.updated"
    description = "Occurs whenever a customer is switched from one coupon to another."


class CustomerSourceCreatedWebhook(Webhook):
    name = "customer.source.created"
    description = "Occurs whenever a new source is created for the customer."


class CustomerSourceDeletedWebhook(Webhook):
    name = "customer.source.deleted"
    description = "Occurs whenever a source is removed from a customer."


class CustomerSourceUpdatedWebhook(Webhook):
    name = "customer.source.updated"
    description = "Occurs whenever a source's details are changed."


class CustomerSubscriptionCreatedWebhook(Webhook):
    name = "customer.subscription.created"
    description = "Occurs whenever a customer with no subscription is signed up for a plan."


class CustomerSubscriptionDeletedWebhook(Webhook):
    name = "customer.subscription.deleted"
    description = "Occurs whenever a customer ends their subscription."


class CustomerSubscriptionTrialWillEndWebhook(Webhook):
    name = "customer.subscription.trial_will_end"
    description = "Occurs three days before the trial period of a subscription is scheduled to end."


class CustomerSubscriptionUpdatedWebhook(Webhook):
    name = "customer.subscription.updated"
    description = "Occurs whenever a subscription changes. Examples would include switching from one plan to another, or switching status from trial to active."


class InvoiceCreatedWebhook(Webhook):
    name = "invoice.created"
    description = "Occurs whenever a new invoice is created. If you are using webhooks, Stripe will wait one hour after they have all succeeded to attempt to pay the invoice; the only exception here is on the first invoice, which gets created and paid immediately when you subscribe a customer to a plan. If your webhooks do not all respond successfully, Stripe will continue retrying the webhooks every hour and will not attempt to pay the invoice. After 3 days, Stripe will attempt to pay the invoice regardless of whether or not your webhooks have succeeded. See how to respond to a webhook."


class InvoicePaymentFailedWebhook(Webhook):
    name = "invoice.payment_failed"
    description = "Occurs whenever an invoice attempts to be paid, and the payment fails. This can occur either due to a declined payment, or because the customer has no active card. A particular case of note is that if a customer with no active card reaches the end of its free trial, an invoice.payment_failed notification will occur."


class InvoicePaymentSucceededWebhook(Webhook):
    name = "invoice.payment_succeeded"
    description = "Occurs whenever an invoice attempts to be paid, and the payment succeeds."


class InvoiceUpdatedWebhook(Webhook):
    name = "invoice.updated"
    description = "Occurs whenever an invoice changes (for example, the amount could change)."


class InvoiceItemCreatedWebhook(Webhook):
    name = "invoiceitem.created"
    description = "Occurs whenever an invoice item is created."


class InvoiceItemDeletedWebhook(Webhook):
    name = "invoiceitem.deleted"
    description = "Occurs whenever an invoice item is deleted."


class InvoiceItemUpdatedWebhook(Webhook):
    name = "invoiceitem.updated"
    description = "Occurs whenever an invoice item is updated."


class OrderCreatedWebhook(Webhook):
    name = "order.created"
    description = "Occurs whenever an order is created."


class OrderPaymentFailedWebhook(Webhook):
    name = "order.payment_failed"
    description = "Occurs whenever payment is attempted on an order, and the payment fails."


class OrderPaymentSucceededWebhook(Webhook):
    name = "order.payment_succeeded"
    description = "Occurs whenever payment is attempted on an order, and the payment succeeds."


class OrderUpdatedWebhook(Webhook):
    name = "order.updated"
    description = "Occurs whenever an order is updated."


class PaymentCreatedWebhook(Webhook):
    name = "payment.created"
    description = "A payment has been received by a Connect account via Transfer from the platform account."


class PlanCreatedWebhook(Webhook):
    name = "plan.created"
    description = "Occurs whenever a plan is created."


class PlanDeletedWebhook(Webhook):
    name = "plan.deleted"
    description = "Occurs whenever a plan is deleted."


class PlanUpdatedWebhook(Webhook):
    name = "plan.updated"
    description = "Occurs whenever a plan is updated."


class ProductCreatedWebhook(Webhook):
    name = "product.created"
    description = "Occurs whenever a product is created."


class ProductUpdatedWebhook(Webhook):
    name = "product.updated"
    description = "Occurs whenever a product is updated."


class RecipientCreatedWebhook(Webhook):
    name = "recipient.created"
    description = "Occurs whenever a recipient is created."


class RecipientDeletedWebhook(Webhook):
    name = "recipient.deleted"
    description = "Occurs whenever a recipient is deleted."


class RecipientUpdatedWebhook(Webhook):
    name = "recipient.updated"
    description = "Occurs whenever a recipient is updated."


class SKUCreatedWebhook(Webhook):
    name = "sku.created"
    description = "Occurs whenever a SKU is created."


class SKUUpdatedWebhook(Webhook):
    name = "sku.updated"
    description = "Occurs whenever a SKU is updated."


class TransferCreatedWebhook(Webhook):
    name = "transfer.created"
    description = "Occurs whenever a new transfer is created."


class TransferFailedWebhook(Webhook):
    name = "transfer.failed"
    description = "Occurs whenever Stripe attempts to send a transfer and that transfer fails."


class TransferPaidWebhook(Webhook):
    name = "transfer.paid"
    description = "Occurs whenever a sent transfer is expected to be available in the destination bank account. If the transfer failed, a transfer.failed webhook will additionally be sent at a later time. Note to Connect users: this event is only created for transfers from your connected Stripe accounts to their bank accounts, not for transfers to the connected accounts themselves."


class TransferReversedWebhook(Webhook):
    name = "transfer.reversed"
    description = "Occurs whenever a transfer is reversed, including partial reversals."


class TransferUpdatedWebhook(Webhook):
    name = "transfer.updated"
    description = "Occurs whenever the description or metadata of a transfer is updated."


class PingWebhook(Webhook):
    name = "ping"
    description = "May be sent by Stripe at any time to see if a provided webhook URL is working."
