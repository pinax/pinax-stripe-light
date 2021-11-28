# Stripe API Version: 2020-08-27
from .base import Webhook


class AccountUpdatedWebhook(Webhook):
    name = "account.updated"
    description = "Occurs whenever an account status or property has changed."


class AccountApplicationAuthorizedWebhook(Webhook):
    name = "account.application.authorized"
    description = "Occurs whenever a user authorizes an application. Sent to the related application only."


class AccountApplicationDeauthorizedWebhook(Webhook):
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
    description = "Occurs whenever an application fee is refunded, whether from refunding a charge or from <a href='#fee_refunds'>refunding the application fee directly</a>. This includes partial refunds."


class ApplicationFeeRefundUpdatedWebhook(Webhook):
    name = "application_fee.refund.updated"
    description = "Occurs whenever an application fee refund is updated."


class BalanceAvailableWebhook(Webhook):
    name = "balance.available"
    description = "Occurs whenever your Stripe balance has been updated (e.g., when a charge is available to be paid out). By default, Stripe automatically transfers funds in your balance to your bank account on a daily basis."


class BillingPortalConfigurationCreatedWebhook(Webhook):
    name = "billing_portal.configuration.created"
    description = "Occurs whenever a portal configuration is created."


class BillingPortalConfigurationUpdatedWebhook(Webhook):
    name = "billing_portal.configuration.updated"
    description = "Occurs whenever a portal configuration is updated."


class CapabilityUpdatedWebhook(Webhook):
    name = "capability.updated"
    description = "Occurs whenever a capability has new requirements or a new status."


class ChargeCapturedWebhook(Webhook):
    name = "charge.captured"
    description = "Occurs whenever a previously uncaptured charge is captured."


class ChargeExpiredWebhook(Webhook):
    name = "charge.expired"
    description = "Occurs whenever an uncaptured charge expires."


class ChargeFailedWebhook(Webhook):
    name = "charge.failed"
    description = "Occurs whenever a failed charge attempt occurs."


class ChargePendingWebhook(Webhook):
    name = "charge.pending"
    description = "Occurs whenever a pending charge is created."


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
    description = "Occurs when a dispute is closed and the dispute status changes to <code>lost</code>, <code>warning_closed</code>, or <code>won</code>."


class ChargeDisputeCreatedWebhook(Webhook):
    name = "charge.dispute.created"
    description = "Occurs whenever a customer disputes a charge with their bank."


class ChargeDisputeFundsReinstatedWebhook(Webhook):
    name = "charge.dispute.funds_reinstated"
    description = "Occurs when funds are reinstated to your account after a dispute is closed. This includes <a href='/docs/disputes#disputes-on-partially-refunded-payments'>partially refunded payments</a>."


class ChargeDisputeFundsWithdrawnWebhook(Webhook):
    name = "charge.dispute.funds_withdrawn"
    description = "Occurs when funds are removed from your account due to a dispute."


class ChargeDisputeUpdatedWebhook(Webhook):
    name = "charge.dispute.updated"
    description = "Occurs when the dispute is updated (usually with evidence)."


class ChargeRefundUpdatedWebhook(Webhook):
    name = "charge.refund.updated"
    description = "Occurs whenever a refund is updated, on selected payment methods."


class CheckoutSessionAsyncPaymentFailedWebhook(Webhook):
    name = "checkout.session.async_payment_failed"
    description = "Occurs when a payment intent using a delayed payment method fails."


class CheckoutSessionAsyncPaymentSucceededWebhook(Webhook):
    name = "checkout.session.async_payment_succeeded"
    description = "Occurs when a payment intent using a delayed payment method finally succeeds."


class CheckoutSessionCompletedWebhook(Webhook):
    name = "checkout.session.completed"
    description = "Occurs when a Checkout Session has been successfully completed."


class CheckoutSessionExpiredWebhook(Webhook):
    name = "checkout.session.expired"
    description = "Occurs when a Checkout Session is expired."


class CouponCreatedWebhook(Webhook):
    name = "coupon.created"
    description = "Occurs whenever a coupon is created."


class CouponDeletedWebhook(Webhook):
    name = "coupon.deleted"
    description = "Occurs whenever a coupon is deleted."


class CouponUpdatedWebhook(Webhook):
    name = "coupon.updated"
    description = "Occurs whenever a coupon is updated."


class CreditNoteCreatedWebhook(Webhook):
    name = "credit_note.created"
    description = "Occurs whenever a credit note is created."


class CreditNoteUpdatedWebhook(Webhook):
    name = "credit_note.updated"
    description = "Occurs whenever a credit note is updated."


class CreditNoteVoidedWebhook(Webhook):
    name = "credit_note.voided"
    description = "Occurs whenever a credit note is voided."


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
    description = "Occurs whenever a coupon is removed from a customer."


class CustomerDiscountUpdatedWebhook(Webhook):
    name = "customer.discount.updated"
    description = "Occurs whenever a customer is switched from one coupon to another."


class CustomerSourceCreatedWebhook(Webhook):
    name = "customer.source.created"
    description = "Occurs whenever a new source is created for a customer."


class CustomerSourceDeletedWebhook(Webhook):
    name = "customer.source.deleted"
    description = "Occurs whenever a source is removed from a customer."


class CustomerSourceExpiringWebhook(Webhook):
    name = "customer.source.expiring"
    description = "Occurs whenever a card or source will expire at the end of the month."


class CustomerSourceUpdatedWebhook(Webhook):
    name = "customer.source.updated"
    description = "Occurs whenever a source's details are changed."


class CustomerSubscriptionCreatedWebhook(Webhook):
    name = "customer.subscription.created"
    description = "Occurs whenever a customer is signed up for a new plan."


class CustomerSubscriptionDeletedWebhook(Webhook):
    name = "customer.subscription.deleted"
    description = "Occurs whenever a customer's subscription ends."


class CustomerSubscriptionPendingUpdateAppliedWebhook(Webhook):
    name = "customer.subscription.pending_update_applied"
    description = "Occurs whenever a customer's subscription's pending update is applied, and the subscription is updated."


class CustomerSubscriptionPendingUpdateExpiredWebhook(Webhook):
    name = "customer.subscription.pending_update_expired"
    description = "Occurs whenever a customer's subscription's pending update expires before the related invoice is paid."


class CustomerSubscriptionTrialWillEndWebhook(Webhook):
    name = "customer.subscription.trial_will_end"
    description = "Occurs three days before a subscription's trial period is scheduled to end, or when a trial is ended immediately (using <code>trial_end=now</code>)."


class CustomerSubscriptionUpdatedWebhook(Webhook):
    name = "customer.subscription.updated"
    description = "Occurs whenever a subscription changes (e.g., switching from one plan to another, or changing the status from trial to active)."


class CustomerTaxIdCreatedWebhook(Webhook):
    name = "customer.tax_id.created"
    description = "Occurs whenever a tax ID is created for a customer."


class CustomerTaxIdDeletedWebhook(Webhook):
    name = "customer.tax_id.deleted"
    description = "Occurs whenever a tax ID is deleted from a customer."


class CustomerTaxIdUpdatedWebhook(Webhook):
    name = "customer.tax_id.updated"
    description = "Occurs whenever a customer's tax ID is updated."


class FileCreatedWebhook(Webhook):
    name = "file.created"
    description = "Occurs whenever a new Stripe-generated file is available for your account."


class IdentityVerificationSessionCanceledWebhook(Webhook):
    name = "identity.verification_session.canceled"
    description = "Occurs whenever a VerificationSession is canceled"


class IdentityVerificationSessionCreatedWebhook(Webhook):
    name = "identity.verification_session.created"
    description = "Occurs whenever a VerificationSession is created"


class IdentityVerificationSessionProcessingWebhook(Webhook):
    name = "identity.verification_session.processing"
    description = "Occurs whenever a VerificationSession transitions to processing"


class IdentityVerificationSessionRedactedWebhook(Webhook):
    name = "identity.verification_session.redacted"
    description = "Occurs whenever a VerificationSession is redacted."


class IdentityVerificationSessionRequiresInputWebhook(Webhook):
    name = "identity.verification_session.requires_input"
    description = "Occurs whenever a VerificationSession transitions to require user input"


class IdentityVerificationSessionVerifiedWebhook(Webhook):
    name = "identity.verification_session.verified"
    description = "Occurs whenever a VerificationSession transitions to verified"


class InvoiceCreatedWebhook(Webhook):
    name = "invoice.created"
    description = "Occurs whenever a new invoice is created. To learn how webhooks can be used with this event, and how they can affect it, see <a href='/docs/subscriptions/webhooks'>Using Webhooks with Subscriptions</a>."


class InvoiceDeletedWebhook(Webhook):
    name = "invoice.deleted"
    description = "Occurs whenever a draft invoice is deleted."


class InvoiceFinalizationFailedWebhook(Webhook):
    name = "invoice.finalization_failed"
    description = "Occurs whenever a draft invoice cannot be finalized. See the invoice’s <a href='/docs/api/invoices/object#invoice_object-last_finalization_error'>last finalization error</a> for details."


class InvoiceFinalizedWebhook(Webhook):
    name = "invoice.finalized"
    description = "Occurs whenever a draft invoice is finalized and updated to be an open invoice."


class InvoiceMarkedUncollectibleWebhook(Webhook):
    name = "invoice.marked_uncollectible"
    description = "Occurs whenever an invoice is marked uncollectible."


class InvoicePaidWebhook(Webhook):
    name = "invoice.paid"
    description = "Occurs whenever an invoice payment attempt succeeds or an invoice is marked as paid out-of-band."


class InvoicePaymentActionRequiredWebhook(Webhook):
    name = "invoice.payment_action_required"
    description = "Occurs whenever an invoice payment attempt requires further user action to complete."


class InvoicePaymentFailedWebhook(Webhook):
    name = "invoice.payment_failed"
    description = "Occurs whenever an invoice payment attempt fails, due either to a declined payment or to the lack of a stored payment method."


class InvoicePaymentSucceededWebhook(Webhook):
    name = "invoice.payment_succeeded"
    description = "Occurs whenever an invoice payment attempt succeeds."


class InvoiceSentWebhook(Webhook):
    name = "invoice.sent"
    description = "Occurs whenever an invoice email is sent out."


class InvoiceUpcomingWebhook(Webhook):
    name = "invoice.upcoming"
    description = "Occurs X number of days before a subscription is scheduled to create an invoice that is automatically charged&mdash;where X is determined by your <a href='https://dashboard.stripe.com/account/billing/automatic'>subscriptions settings</a>. Note: The received <code>Invoice</code> object will not have an invoice ID."


class InvoiceUpdatedWebhook(Webhook):
    name = "invoice.updated"
    description = "Occurs whenever an invoice changes (e.g., the invoice amount)."


class InvoiceVoidedWebhook(Webhook):
    name = "invoice.voided"
    description = "Occurs whenever an invoice is voided."


class InvoiceitemCreatedWebhook(Webhook):
    name = "invoiceitem.created"
    description = "Occurs whenever an invoice item is created."


class InvoiceitemDeletedWebhook(Webhook):
    name = "invoiceitem.deleted"
    description = "Occurs whenever an invoice item is deleted."


class InvoiceitemUpdatedWebhook(Webhook):
    name = "invoiceitem.updated"
    description = "Occurs whenever an invoice item is updated."


class IssuingAuthorizationCreatedWebhook(Webhook):
    name = "issuing_authorization.created"
    description = "Occurs whenever an authorization is created."


class IssuingAuthorizationRequestWebhook(Webhook):
    name = "issuing_authorization.request"
    description = "Represents a synchronous request for authorization, see <a href='/docs/issuing/purchases/authorizations#authorization-handling'>Using your integration to handle authorization requests</a>."


class IssuingAuthorizationUpdatedWebhook(Webhook):
    name = "issuing_authorization.updated"
    description = "Occurs whenever an authorization is updated."


class IssuingCardCreatedWebhook(Webhook):
    name = "issuing_card.created"
    description = "Occurs whenever a card is created."


class IssuingCardUpdatedWebhook(Webhook):
    name = "issuing_card.updated"
    description = "Occurs whenever a card is updated."


class IssuingCardholderCreatedWebhook(Webhook):
    name = "issuing_cardholder.created"
    description = "Occurs whenever a cardholder is created."


class IssuingCardholderUpdatedWebhook(Webhook):
    name = "issuing_cardholder.updated"
    description = "Occurs whenever a cardholder is updated."


class IssuingDisputeClosedWebhook(Webhook):
    name = "issuing_dispute.closed"
    description = "Occurs whenever a dispute is won, lost or expired."


class IssuingDisputeCreatedWebhook(Webhook):
    name = "issuing_dispute.created"
    description = "Occurs whenever a dispute is created."


class IssuingDisputeFundsReinstatedWebhook(Webhook):
    name = "issuing_dispute.funds_reinstated"
    description = "Occurs whenever funds are reinstated to your account for an Issuing dispute."


class IssuingDisputeSubmittedWebhook(Webhook):
    name = "issuing_dispute.submitted"
    description = "Occurs whenever a dispute is submitted."


class IssuingDisputeUpdatedWebhook(Webhook):
    name = "issuing_dispute.updated"
    description = "Occurs whenever a dispute is updated."


class IssuingTransactionCreatedWebhook(Webhook):
    name = "issuing_transaction.created"
    description = "Occurs whenever an issuing transaction is created."


class IssuingTransactionUpdatedWebhook(Webhook):
    name = "issuing_transaction.updated"
    description = "Occurs whenever an issuing transaction is updated."


class MandateUpdatedWebhook(Webhook):
    name = "mandate.updated"
    description = "Occurs whenever a Mandate is updated."


class OrderCreatedWebhook(Webhook):
    name = "order.created"
    description = "Occurs whenever an order is created."


class OrderPaymentFailedWebhook(Webhook):
    name = "order.payment_failed"
    description = "Occurs whenever an order payment attempt fails."


class OrderPaymentSucceededWebhook(Webhook):
    name = "order.payment_succeeded"
    description = "Occurs whenever an order payment attempt succeeds."


class OrderUpdatedWebhook(Webhook):
    name = "order.updated"
    description = "Occurs whenever an order is updated."


class OrderReturnCreatedWebhook(Webhook):
    name = "order_return.created"
    description = "Occurs whenever an order return is created."


class PaymentIntentAmountCapturableUpdatedWebhook(Webhook):
    name = "payment_intent.amount_capturable_updated"
    description = "Occurs when a PaymentIntent has funds to be captured. Check the <code>amount_capturable</code> property on the PaymentIntent to determine the amount that can be captured. You may capture the PaymentIntent with an <code>amount_to_capture</code> value up to the specified amount. <a href='https://stripe.com/docs/api/payment_intents/capture'>Learn more about capturing PaymentIntents.</a>"


class PaymentIntentCanceledWebhook(Webhook):
    name = "payment_intent.canceled"
    description = "Occurs when a PaymentIntent is canceled."


class PaymentIntentCreatedWebhook(Webhook):
    name = "payment_intent.created"
    description = "Occurs when a new PaymentIntent is created."


class PaymentIntentPaymentFailedWebhook(Webhook):
    name = "payment_intent.payment_failed"
    description = "Occurs when a PaymentIntent has failed the attempt to create a payment method or a payment."


class PaymentIntentProcessingWebhook(Webhook):
    name = "payment_intent.processing"
    description = "Occurs when a PaymentIntent has started processing."


class PaymentIntentRequiresActionWebhook(Webhook):
    name = "payment_intent.requires_action"
    description = "Occurs when a PaymentIntent transitions to requires_action state"


class PaymentIntentSucceededWebhook(Webhook):
    name = "payment_intent.succeeded"
    description = "Occurs when a PaymentIntent has successfully completed payment."


class PaymentMethodAttachedWebhook(Webhook):
    name = "payment_method.attached"
    description = "Occurs whenever a new payment method is attached to a customer."


class PaymentMethodAutomaticallyUpdatedWebhook(Webhook):
    name = "payment_method.automatically_updated"
    description = "Occurs whenever a payment method's details are automatically updated by the network."


class PaymentMethodDetachedWebhook(Webhook):
    name = "payment_method.detached"
    description = "Occurs whenever a payment method is detached from a customer."


class PaymentMethodUpdatedWebhook(Webhook):
    name = "payment_method.updated"
    description = "Occurs whenever a payment method is updated via the <a href='https://stripe.com/docs/api/payment_methods/update'>PaymentMethod update API</a>."


class PayoutCanceledWebhook(Webhook):
    name = "payout.canceled"
    description = "Occurs whenever a payout is canceled."


class PayoutCreatedWebhook(Webhook):
    name = "payout.created"
    description = "Occurs whenever a payout is created."


class PayoutFailedWebhook(Webhook):
    name = "payout.failed"
    description = "Occurs whenever a payout attempt fails."


class PayoutPaidWebhook(Webhook):
    name = "payout.paid"
    description = "Occurs whenever a payout is <em>expected</em> to be available in the destination account. If the payout fails, a <code>payout.failed</code> notification is also sent, at a later time."


class PayoutUpdatedWebhook(Webhook):
    name = "payout.updated"
    description = "Occurs whenever a payout is updated."


class PersonCreatedWebhook(Webhook):
    name = "person.created"
    description = "Occurs whenever a person associated with an account is created."


class PersonDeletedWebhook(Webhook):
    name = "person.deleted"
    description = "Occurs whenever a person associated with an account is deleted."


class PersonUpdatedWebhook(Webhook):
    name = "person.updated"
    description = "Occurs whenever a person associated with an account is updated."


class PlanCreatedWebhook(Webhook):
    name = "plan.created"
    description = "Occurs whenever a plan is created."


class PlanDeletedWebhook(Webhook):
    name = "plan.deleted"
    description = "Occurs whenever a plan is deleted."


class PlanUpdatedWebhook(Webhook):
    name = "plan.updated"
    description = "Occurs whenever a plan is updated."


class PriceCreatedWebhook(Webhook):
    name = "price.created"
    description = "Occurs whenever a price is created."


class PriceDeletedWebhook(Webhook):
    name = "price.deleted"
    description = "Occurs whenever a price is deleted."


class PriceUpdatedWebhook(Webhook):
    name = "price.updated"
    description = "Occurs whenever a price is updated."


class ProductCreatedWebhook(Webhook):
    name = "product.created"
    description = "Occurs whenever a product is created."


class ProductDeletedWebhook(Webhook):
    name = "product.deleted"
    description = "Occurs whenever a product is deleted."


class ProductUpdatedWebhook(Webhook):
    name = "product.updated"
    description = "Occurs whenever a product is updated."


class PromotionCodeCreatedWebhook(Webhook):
    name = "promotion_code.created"
    description = "Occurs whenever a promotion code is created."


class PromotionCodeUpdatedWebhook(Webhook):
    name = "promotion_code.updated"
    description = "Occurs whenever a promotion code is updated."


class QuoteAcceptedWebhook(Webhook):
    name = "quote.accepted"
    description = "Occurs whenever a quote is accepted."


class QuoteCanceledWebhook(Webhook):
    name = "quote.canceled"
    description = "Occurs whenever a quote is canceled."


class QuoteCreatedWebhook(Webhook):
    name = "quote.created"
    description = "Occurs whenever a quote is created."


class QuoteFinalizedWebhook(Webhook):
    name = "quote.finalized"
    description = "Occurs whenever a quote is finalized."


class RadarEarlyFraudWarningCreatedWebhook(Webhook):
    name = "radar.early_fraud_warning.created"
    description = "Occurs whenever an early fraud warning is created."


class RadarEarlyFraudWarningUpdatedWebhook(Webhook):
    name = "radar.early_fraud_warning.updated"
    description = "Occurs whenever an early fraud warning is updated."


class RecipientCreatedWebhook(Webhook):
    name = "recipient.created"
    description = "Occurs whenever a recipient is created."


class RecipientDeletedWebhook(Webhook):
    name = "recipient.deleted"
    description = "Occurs whenever a recipient is deleted."


class RecipientUpdatedWebhook(Webhook):
    name = "recipient.updated"
    description = "Occurs whenever a recipient is updated."


class ReportingReportRunFailedWebhook(Webhook):
    name = "reporting.report_run.failed"
    description = "Occurs whenever a requested <code>ReportRun</code> failed to complete."


class ReportingReportRunSucceededWebhook(Webhook):
    name = "reporting.report_run.succeeded"
    description = "Occurs whenever a requested <code>ReportRun</code> completed succesfully."


class ReportingReportTypeUpdatedWebhook(Webhook):
    name = "reporting.report_type.updated"
    description = "Occurs whenever a <code>ReportType</code> is updated (typically to indicate that a new day's data has come available)."


class ReviewClosedWebhook(Webhook):
    name = "review.closed"
    description = "Occurs whenever a review is closed. The review's <code>reason</code> field indicates why: <code>approved</code>, <code>disputed</code>, <code>refunded</code>, or <code>refunded_as_fraud</code>."


class ReviewOpenedWebhook(Webhook):
    name = "review.opened"
    description = "Occurs whenever a review is opened."


class SetupIntentCanceledWebhook(Webhook):
    name = "setup_intent.canceled"
    description = "Occurs when a SetupIntent is canceled."


class SetupIntentCreatedWebhook(Webhook):
    name = "setup_intent.created"
    description = "Occurs when a new SetupIntent is created."


class SetupIntentRequiresActionWebhook(Webhook):
    name = "setup_intent.requires_action"
    description = "Occurs when a SetupIntent is in requires_action state."


class SetupIntentSetupFailedWebhook(Webhook):
    name = "setup_intent.setup_failed"
    description = "Occurs when a SetupIntent has failed the attempt to setup a payment method."


class SetupIntentSucceededWebhook(Webhook):
    name = "setup_intent.succeeded"
    description = "Occurs when an SetupIntent has successfully setup a payment method."


class SigmaScheduledQueryRunCreatedWebhook(Webhook):
    name = "sigma.scheduled_query_run.created"
    description = "Occurs whenever a Sigma scheduled query run finishes."


class SkuCreatedWebhook(Webhook):
    name = "sku.created"
    description = "Occurs whenever a SKU is created."


class SkuDeletedWebhook(Webhook):
    name = "sku.deleted"
    description = "Occurs whenever a SKU is deleted."


class SkuUpdatedWebhook(Webhook):
    name = "sku.updated"
    description = "Occurs whenever a SKU is updated."


class SourceCanceledWebhook(Webhook):
    name = "source.canceled"
    description = "Occurs whenever a source is canceled."


class SourceChargeableWebhook(Webhook):
    name = "source.chargeable"
    description = "Occurs whenever a source transitions to chargeable."


class SourceFailedWebhook(Webhook):
    name = "source.failed"
    description = "Occurs whenever a source fails."


class SourceMandateNotificationWebhook(Webhook):
    name = "source.mandate_notification"
    description = "Occurs whenever a source mandate notification method is set to manual."


class SourceRefundAttributesRequiredWebhook(Webhook):
    name = "source.refund_attributes_required"
    description = "Occurs whenever the refund attributes are required on a receiver source to process a refund or a mispayment."


class SourceTransactionCreatedWebhook(Webhook):
    name = "source.transaction.created"
    description = "Occurs whenever a source transaction is created."


class SourceTransactionUpdatedWebhook(Webhook):
    name = "source.transaction.updated"
    description = "Occurs whenever a source transaction is updated."


class SubscriptionScheduleAbortedWebhook(Webhook):
    name = "subscription_schedule.aborted"
    description = "Occurs whenever a subscription schedule is canceled due to the underlying subscription being canceled because of delinquency."


class SubscriptionScheduleCanceledWebhook(Webhook):
    name = "subscription_schedule.canceled"
    description = "Occurs whenever a subscription schedule is canceled."


class SubscriptionScheduleCompletedWebhook(Webhook):
    name = "subscription_schedule.completed"
    description = "Occurs whenever a new subscription schedule is completed."


class SubscriptionScheduleCreatedWebhook(Webhook):
    name = "subscription_schedule.created"
    description = "Occurs whenever a new subscription schedule is created."


class SubscriptionScheduleExpiringWebhook(Webhook):
    name = "subscription_schedule.expiring"
    description = "Occurs 7 days before a subscription schedule will expire."


class SubscriptionScheduleReleasedWebhook(Webhook):
    name = "subscription_schedule.released"
    description = "Occurs whenever a new subscription schedule is released."


class SubscriptionScheduleUpdatedWebhook(Webhook):
    name = "subscription_schedule.updated"
    description = "Occurs whenever a subscription schedule is updated."


class TaxRateCreatedWebhook(Webhook):
    name = "tax_rate.created"
    description = "Occurs whenever a new tax rate is created."


class TaxRateUpdatedWebhook(Webhook):
    name = "tax_rate.updated"
    description = "Occurs whenever a tax rate is updated."


class TopupCanceledWebhook(Webhook):
    name = "topup.canceled"
    description = "Occurs whenever a top-up is canceled."


class TopupCreatedWebhook(Webhook):
    name = "topup.created"
    description = "Occurs whenever a top-up is created."


class TopupFailedWebhook(Webhook):
    name = "topup.failed"
    description = "Occurs whenever a top-up fails."


class TopupReversedWebhook(Webhook):
    name = "topup.reversed"
    description = "Occurs whenever a top-up is reversed."


class TopupSucceededWebhook(Webhook):
    name = "topup.succeeded"
    description = "Occurs whenever a top-up succeeds."


class TransferCreatedWebhook(Webhook):
    name = "transfer.created"
    description = "Occurs whenever a transfer is created."


class TransferFailedWebhook(Webhook):
    name = "transfer.failed"
    description = "Occurs whenever a transfer failed."


class TransferPaidWebhook(Webhook):
    name = "transfer.paid"
    description = "Occurs after a transfer is paid. For Instant Payouts, the event will typically be sent within 30 minutes."


class TransferReversedWebhook(Webhook):
    name = "transfer.reversed"
    description = "Occurs whenever a transfer is reversed, including partial reversals."


class TransferUpdatedWebhook(Webhook):
    name = "transfer.updated"
    description = "Occurs whenever a transfer's description or metadata is updated."
