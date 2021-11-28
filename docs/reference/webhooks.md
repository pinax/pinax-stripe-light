# Webhooks

Stripe sends a events for just about everything that happens in its system as
a JSON payload to a webhook.

A webhook is an endpoint running your site that accepts `POST` requests. You
provide the full url to this endpoint in the settings at Stripe so it knows
where to send the payloads.

## Setup

Click onto your Stripe settings panel and then click on the Webhooks tab:

![](../user-guide/images/stripe-menu.png)

![](images/webhooks-tab.png)

From there click on add endpoint button and add the full url:

![](images/webhooks-add-url.png)

`pinax-stripe-light` ships with a webhook view and all the code necessary to process
and store events sent to your webhook.  If you install the `pinax-stripe-light` urls
like so:

```python
url(r"^payments/", include("pinax.stripe.urls")),
```

Then the full url to your webhook that you'll need to enter into the Stripe UI
pictured above is:

    https://yourdomain.com/payments/webhook/

## Security

Security is handled through signature verification of the webhook.  Stripe sends
a header that is passed along with the data and a shared secret to a function in
the stripe library to verify the payload.  It is only recorded and processed if
it passes verification.


## Signals

`pinax-stripe-light` handles certain events in the webhook processing that are
important for certain operations like syncing data or deleting cards. Every
event, though, has a corresponding signal that is sent, so you can hook into
these events in your project.  See [the signals reference](signals.md) for
details on how to wire those up.

## Events

These classes are found in `pinax.stripe.webhooks.*`:

* `AccountUpdatedWebhook` - `account.updated` - Occurs whenever an account status or property has changed.
* `AccountApplicationAuthorizedWebhook` - `account.application.authorized` - Occurs whenever a user authorizes an application. Sent to the related application only.
* `AccountApplicationDeauthorizedWebhook` - `account.application.deauthorized` - Occurs whenever a user deauthorizes an application. Sent to the related application only.
* `AccountExternalAccountCreatedWebhook` - `account.external_account.created` - Occurs whenever an external account is created.
* `AccountExternalAccountDeletedWebhook` - `account.external_account.deleted` - Occurs whenever an external account is deleted.
* `AccountExternalAccountUpdatedWebhook` - `account.external_account.updated` - Occurs whenever an external account is updated.
* `ApplicationFeeCreatedWebhook` - `application_fee.created` - Occurs whenever an application fee is created on a charge.
* `ApplicationFeeRefundedWebhook` - `application_fee.refunded` - Occurs whenever an application fee is refunded, whether from refunding a charge or from <a href='#fee_refunds'>refunding the application fee directly</a>. This includes partial refunds.
* `ApplicationFeeRefundUpdatedWebhook` - `application_fee.refund.updated` - Occurs whenever an application fee refund is updated.
* `BalanceAvailableWebhook` - `balance.available` - Occurs whenever your Stripe balance has been updated (e.g., when a charge is available to be paid out). By default, Stripe automatically transfers funds in your balance to your bank account on a daily basis.
* `BillingPortalConfigurationCreatedWebhook` - `billing_portal.configuration.created` - Occurs whenever a portal configuration is created.
* `BillingPortalConfigurationUpdatedWebhook` - `billing_portal.configuration.updated` - Occurs whenever a portal configuration is updated.
* `CapabilityUpdatedWebhook` - `capability.updated` - Occurs whenever a capability has new requirements or a new status.
* `ChargeCapturedWebhook` - `charge.captured` - Occurs whenever a previously uncaptured charge is captured.
* `ChargeExpiredWebhook` - `charge.expired` - Occurs whenever an uncaptured charge expires.
* `ChargeFailedWebhook` - `charge.failed` - Occurs whenever a failed charge attempt occurs.
* `ChargePendingWebhook` - `charge.pending` - Occurs whenever a pending charge is created.
* `ChargeRefundedWebhook` - `charge.refunded` - Occurs whenever a charge is refunded, including partial refunds.
* `ChargeSucceededWebhook` - `charge.succeeded` - Occurs whenever a new charge is created and is successful.
* `ChargeUpdatedWebhook` - `charge.updated` - Occurs whenever a charge description or metadata is updated.
* `ChargeDisputeClosedWebhook` - `charge.dispute.closed` - Occurs when a dispute is closed and the dispute status changes to <code>lost</code>, <code>warning_closed</code>, or <code>won</code>.
* `ChargeDisputeCreatedWebhook` - `charge.dispute.created` - Occurs whenever a customer disputes a charge with their bank.
* `ChargeDisputeFundsReinstatedWebhook` - `charge.dispute.funds_reinstated` - Occurs when funds are reinstated to your account after a dispute is closed. This includes <a href='/docs/disputes#disputes-on-partially-refunded-payments'>partially refunded payments</a>.
* `ChargeDisputeFundsWithdrawnWebhook` - `charge.dispute.funds_withdrawn` - Occurs when funds are removed from your account due to a dispute.
* `ChargeDisputeUpdatedWebhook` - `charge.dispute.updated` - Occurs when the dispute is updated (usually with evidence).
* `ChargeRefundUpdatedWebhook` - `charge.refund.updated` - Occurs whenever a refund is updated, on selected payment methods.
* `CheckoutSessionAsyncPaymentFailedWebhook` - `checkout.session.async_payment_failed` - Occurs when a payment intent using a delayed payment method fails.
* `CheckoutSessionAsyncPaymentSucceededWebhook` - `checkout.session.async_payment_succeeded` - Occurs when a payment intent using a delayed payment method finally succeeds.
* `CheckoutSessionCompletedWebhook` - `checkout.session.completed` - Occurs when a Checkout Session has been successfully completed.
* `CheckoutSessionExpiredWebhook` - `checkout.session.expired` - Occurs when a Checkout Session is expired.
* `CouponCreatedWebhook` - `coupon.created` - Occurs whenever a coupon is created.
* `CouponDeletedWebhook` - `coupon.deleted` - Occurs whenever a coupon is deleted.
* `CouponUpdatedWebhook` - `coupon.updated` - Occurs whenever a coupon is updated.
* `CreditNoteCreatedWebhook` - `credit_note.created` - Occurs whenever a credit note is created.
* `CreditNoteUpdatedWebhook` - `credit_note.updated` - Occurs whenever a credit note is updated.
* `CreditNoteVoidedWebhook` - `credit_note.voided` - Occurs whenever a credit note is voided.
* `CustomerCreatedWebhook` - `customer.created` - Occurs whenever a new customer is created.
* `CustomerDeletedWebhook` - `customer.deleted` - Occurs whenever a customer is deleted.
* `CustomerUpdatedWebhook` - `customer.updated` - Occurs whenever any property of a customer changes.
* `CustomerDiscountCreatedWebhook` - `customer.discount.created` - Occurs whenever a coupon is attached to a customer.
* `CustomerDiscountDeletedWebhook` - `customer.discount.deleted` - Occurs whenever a coupon is removed from a customer.
* `CustomerDiscountUpdatedWebhook` - `customer.discount.updated` - Occurs whenever a customer is switched from one coupon to another.
* `CustomerSourceCreatedWebhook` - `customer.source.created` - Occurs whenever a new source is created for a customer.
* `CustomerSourceDeletedWebhook` - `customer.source.deleted` - Occurs whenever a source is removed from a customer.
* `CustomerSourceExpiringWebhook` - `customer.source.expiring` - Occurs whenever a card or source will expire at the end of the month.
* `CustomerSourceUpdatedWebhook` - `customer.source.updated` - Occurs whenever a source's details are changed.
* `CustomerSubscriptionCreatedWebhook` - `customer.subscription.created` - Occurs whenever a customer is signed up for a new plan.
* `CustomerSubscriptionDeletedWebhook` - `customer.subscription.deleted` - Occurs whenever a customer's subscription ends.
* `CustomerSubscriptionPendingUpdateAppliedWebhook` - `customer.subscription.pending_update_applied` - Occurs whenever a customer's subscription's pending update is applied, and the subscription is updated.
* `CustomerSubscriptionPendingUpdateExpiredWebhook` - `customer.subscription.pending_update_expired` - Occurs whenever a customer's subscription's pending update expires before the related invoice is paid.
* `CustomerSubscriptionTrialWillEndWebhook` - `customer.subscription.trial_will_end` - Occurs three days before a subscription's trial period is scheduled to end, or when a trial is ended immediately (using <code>trial_end=now</code>).
* `CustomerSubscriptionUpdatedWebhook` - `customer.subscription.updated` - Occurs whenever a subscription changes (e.g., switching from one plan to another, or changing the status from trial to active).
* `CustomerTaxIdCreatedWebhook` - `customer.tax_id.created` - Occurs whenever a tax ID is created for a customer.
* `CustomerTaxIdDeletedWebhook` - `customer.tax_id.deleted` - Occurs whenever a tax ID is deleted from a customer.
* `CustomerTaxIdUpdatedWebhook` - `customer.tax_id.updated` - Occurs whenever a customer's tax ID is updated.
* `FileCreatedWebhook` - `file.created` - Occurs whenever a new Stripe-generated file is available for your account.
* `IdentityVerificationSessionCanceledWebhook` - `identity.verification_session.canceled` - Occurs whenever a VerificationSession is canceled
* `IdentityVerificationSessionCreatedWebhook` - `identity.verification_session.created` - Occurs whenever a VerificationSession is created
* `IdentityVerificationSessionProcessingWebhook` - `identity.verification_session.processing` - Occurs whenever a VerificationSession transitions to processing
* `IdentityVerificationSessionRedactedWebhook` - `identity.verification_session.redacted` - Occurs whenever a VerificationSession is redacted.
* `IdentityVerificationSessionRequiresInputWebhook` - `identity.verification_session.requires_input` - Occurs whenever a VerificationSession transitions to require user input
* `IdentityVerificationSessionVerifiedWebhook` - `identity.verification_session.verified` - Occurs whenever a VerificationSession transitions to verified
* `InvoiceCreatedWebhook` - `invoice.created` - Occurs whenever a new invoice is created. To learn how webhooks can be used with this event, and how they can affect it, see <a href='/docs/subscriptions/webhooks'>Using Webhooks with Subscriptions</a>.
* `InvoiceDeletedWebhook` - `invoice.deleted` - Occurs whenever a draft invoice is deleted.
* `InvoiceFinalizationFailedWebhook` - `invoice.finalization_failed` - Occurs whenever a draft invoice cannot be finalized. See the invoice’s <a href='/docs/api/invoices/object#invoice_object-last_finalization_error'>last finalization error</a> for details.
* `InvoiceFinalizedWebhook` - `invoice.finalized` - Occurs whenever a draft invoice is finalized and updated to be an open invoice.
* `InvoiceMarkedUncollectibleWebhook` - `invoice.marked_uncollectible` - Occurs whenever an invoice is marked uncollectible.
* `InvoicePaidWebhook` - `invoice.paid` - Occurs whenever an invoice payment attempt succeeds or an invoice is marked as paid out-of-band.
* `InvoicePaymentActionRequiredWebhook` - `invoice.payment_action_required` - Occurs whenever an invoice payment attempt requires further user action to complete.
* `InvoicePaymentFailedWebhook` - `invoice.payment_failed` - Occurs whenever an invoice payment attempt fails, due either to a declined payment or to the lack of a stored payment method.
* `InvoicePaymentSucceededWebhook` - `invoice.payment_succeeded` - Occurs whenever an invoice payment attempt succeeds.
* `InvoiceSentWebhook` - `invoice.sent` - Occurs whenever an invoice email is sent out.
* `InvoiceUpcomingWebhook` - `invoice.upcoming` - Occurs X number of days before a subscription is scheduled to create an invoice that is automatically charged&mdash;where X is determined by your <a href='https://dashboard.stripe.com/account/billing/automatic'>subscriptions settings</a>. Note: The received <code>Invoice</code> object will not have an invoice ID.
* `InvoiceUpdatedWebhook` - `invoice.updated` - Occurs whenever an invoice changes (e.g., the invoice amount).
* `InvoiceVoidedWebhook` - `invoice.voided` - Occurs whenever an invoice is voided.
* `InvoiceitemCreatedWebhook` - `invoiceitem.created` - Occurs whenever an invoice item is created.
* `InvoiceitemDeletedWebhook` - `invoiceitem.deleted` - Occurs whenever an invoice item is deleted.
* `InvoiceitemUpdatedWebhook` - `invoiceitem.updated` - Occurs whenever an invoice item is updated.
* `IssuingAuthorizationCreatedWebhook` - `issuing_authorization.created` - Occurs whenever an authorization is created.
* `IssuingAuthorizationRequestWebhook` - `issuing_authorization.request` - Represents a synchronous request for authorization, see <a href='/docs/issuing/purchases/authorizations#authorization-handling'>Using your integration to handle authorization requests</a>.
* `IssuingAuthorizationUpdatedWebhook` - `issuing_authorization.updated` - Occurs whenever an authorization is updated.
* `IssuingCardCreatedWebhook` - `issuing_card.created` - Occurs whenever a card is created.
* `IssuingCardUpdatedWebhook` - `issuing_card.updated` - Occurs whenever a card is updated.
* `IssuingCardholderCreatedWebhook` - `issuing_cardholder.created` - Occurs whenever a cardholder is created.
* `IssuingCardholderUpdatedWebhook` - `issuing_cardholder.updated` - Occurs whenever a cardholder is updated.
* `IssuingDisputeClosedWebhook` - `issuing_dispute.closed` - Occurs whenever a dispute is won, lost or expired.
* `IssuingDisputeCreatedWebhook` - `issuing_dispute.created` - Occurs whenever a dispute is created.
* `IssuingDisputeFundsReinstatedWebhook` - `issuing_dispute.funds_reinstated` - Occurs whenever funds are reinstated to your account for an Issuing dispute.
* `IssuingDisputeSubmittedWebhook` - `issuing_dispute.submitted` - Occurs whenever a dispute is submitted.
* `IssuingDisputeUpdatedWebhook` - `issuing_dispute.updated` - Occurs whenever a dispute is updated.
* `IssuingTransactionCreatedWebhook` - `issuing_transaction.created` - Occurs whenever an issuing transaction is created.
* `IssuingTransactionUpdatedWebhook` - `issuing_transaction.updated` - Occurs whenever an issuing transaction is updated.
* `MandateUpdatedWebhook` - `mandate.updated` - Occurs whenever a Mandate is updated.
* `OrderCreatedWebhook` - `order.created` - Occurs whenever an order is created.
* `OrderPaymentFailedWebhook` - `order.payment_failed` - Occurs whenever an order payment attempt fails.
* `OrderPaymentSucceededWebhook` - `order.payment_succeeded` - Occurs whenever an order payment attempt succeeds.
* `OrderUpdatedWebhook` - `order.updated` - Occurs whenever an order is updated.
* `OrderReturnCreatedWebhook` - `order_return.created` - Occurs whenever an order return is created.
* `PaymentIntentAmountCapturableUpdatedWebhook` - `payment_intent.amount_capturable_updated` - Occurs when a PaymentIntent has funds to be captured. Check the <code>amount_capturable</code> property on the PaymentIntent to determine the amount that can be captured. You may capture the PaymentIntent with an <code>amount_to_capture</code> value up to the specified amount. <a href='https://stripe.com/docs/api/payment_intents/capture'>Learn more about capturing PaymentIntents.</a>
* `PaymentIntentCanceledWebhook` - `payment_intent.canceled` - Occurs when a PaymentIntent is canceled.
* `PaymentIntentCreatedWebhook` - `payment_intent.created` - Occurs when a new PaymentIntent is created.
* `PaymentIntentPaymentFailedWebhook` - `payment_intent.payment_failed` - Occurs when a PaymentIntent has failed the attempt to create a payment method or a payment.
* `PaymentIntentProcessingWebhook` - `payment_intent.processing` - Occurs when a PaymentIntent has started processing.
* `PaymentIntentRequiresActionWebhook` - `payment_intent.requires_action` - Occurs when a PaymentIntent transitions to requires_action state
* `PaymentIntentSucceededWebhook` - `payment_intent.succeeded` - Occurs when a PaymentIntent has successfully completed payment.
* `PaymentMethodAttachedWebhook` - `payment_method.attached` - Occurs whenever a new payment method is attached to a customer.
* `PaymentMethodAutomaticallyUpdatedWebhook` - `payment_method.automatically_updated` - Occurs whenever a payment method's details are automatically updated by the network.
* `PaymentMethodDetachedWebhook` - `payment_method.detached` - Occurs whenever a payment method is detached from a customer.
* `PaymentMethodUpdatedWebhook` - `payment_method.updated` - Occurs whenever a payment method is updated via the <a href='https://stripe.com/docs/api/payment_methods/update'>PaymentMethod update API</a>.
* `PayoutCanceledWebhook` - `payout.canceled` - Occurs whenever a payout is canceled.
* `PayoutCreatedWebhook` - `payout.created` - Occurs whenever a payout is created.
* `PayoutFailedWebhook` - `payout.failed` - Occurs whenever a payout attempt fails.
* `PayoutPaidWebhook` - `payout.paid` - Occurs whenever a payout is <em>expected</em> to be available in the destination account. If the payout fails, a <code>payout.failed</code> notification is also sent, at a later time.
* `PayoutUpdatedWebhook` - `payout.updated` - Occurs whenever a payout is updated.
* `PersonCreatedWebhook` - `person.created` - Occurs whenever a person associated with an account is created.
* `PersonDeletedWebhook` - `person.deleted` - Occurs whenever a person associated with an account is deleted.
* `PersonUpdatedWebhook` - `person.updated` - Occurs whenever a person associated with an account is updated.
* `PlanCreatedWebhook` - `plan.created` - Occurs whenever a plan is created.
* `PlanDeletedWebhook` - `plan.deleted` - Occurs whenever a plan is deleted.
* `PlanUpdatedWebhook` - `plan.updated` - Occurs whenever a plan is updated.
* `PriceCreatedWebhook` - `price.created` - Occurs whenever a price is created.
* `PriceDeletedWebhook` - `price.deleted` - Occurs whenever a price is deleted.
* `PriceUpdatedWebhook` - `price.updated` - Occurs whenever a price is updated.
* `ProductCreatedWebhook` - `product.created` - Occurs whenever a product is created.
* `ProductDeletedWebhook` - `product.deleted` - Occurs whenever a product is deleted.
* `ProductUpdatedWebhook` - `product.updated` - Occurs whenever a product is updated.
* `PromotionCodeCreatedWebhook` - `promotion_code.created` - Occurs whenever a promotion code is created.
* `PromotionCodeUpdatedWebhook` - `promotion_code.updated` - Occurs whenever a promotion code is updated.
* `QuoteAcceptedWebhook` - `quote.accepted` - Occurs whenever a quote is accepted.
* `QuoteCanceledWebhook` - `quote.canceled` - Occurs whenever a quote is canceled.
* `QuoteCreatedWebhook` - `quote.created` - Occurs whenever a quote is created.
* `QuoteFinalizedWebhook` - `quote.finalized` - Occurs whenever a quote is finalized.
* `RadarEarlyFraudWarningCreatedWebhook` - `radar.early_fraud_warning.created` - Occurs whenever an early fraud warning is created.
* `RadarEarlyFraudWarningUpdatedWebhook` - `radar.early_fraud_warning.updated` - Occurs whenever an early fraud warning is updated.
* `RecipientCreatedWebhook` - `recipient.created` - Occurs whenever a recipient is created.
* `RecipientDeletedWebhook` - `recipient.deleted` - Occurs whenever a recipient is deleted.
* `RecipientUpdatedWebhook` - `recipient.updated` - Occurs whenever a recipient is updated.
* `ReportingReportRunFailedWebhook` - `reporting.report_run.failed` - Occurs whenever a requested <code>ReportRun</code> failed to complete.
* `ReportingReportRunSucceededWebhook` - `reporting.report_run.succeeded` - Occurs whenever a requested <code>ReportRun</code> completed succesfully.
* `ReportingReportTypeUpdatedWebhook` - `reporting.report_type.updated` - Occurs whenever a <code>ReportType</code> is updated (typically to indicate that a new day's data has come available).
* `ReviewClosedWebhook` - `review.closed` - Occurs whenever a review is closed. The review's <code>reason</code> field indicates why: <code>approved</code>, <code>disputed</code>, <code>refunded</code>, or <code>refunded_as_fraud</code>.
* `ReviewOpenedWebhook` - `review.opened` - Occurs whenever a review is opened.
* `SetupIntentCanceledWebhook` - `setup_intent.canceled` - Occurs when a SetupIntent is canceled.
* `SetupIntentCreatedWebhook` - `setup_intent.created` - Occurs when a new SetupIntent is created.
* `SetupIntentRequiresActionWebhook` - `setup_intent.requires_action` - Occurs when a SetupIntent is in requires_action state.
* `SetupIntentSetupFailedWebhook` - `setup_intent.setup_failed` - Occurs when a SetupIntent has failed the attempt to setup a payment method.
* `SetupIntentSucceededWebhook` - `setup_intent.succeeded` - Occurs when an SetupIntent has successfully setup a payment method.
* `SigmaScheduledQueryRunCreatedWebhook` - `sigma.scheduled_query_run.created` - Occurs whenever a Sigma scheduled query run finishes.
* `SkuCreatedWebhook` - `sku.created` - Occurs whenever a SKU is created.
* `SkuDeletedWebhook` - `sku.deleted` - Occurs whenever a SKU is deleted.
* `SkuUpdatedWebhook` - `sku.updated` - Occurs whenever a SKU is updated.
* `SourceCanceledWebhook` - `source.canceled` - Occurs whenever a source is canceled.
* `SourceChargeableWebhook` - `source.chargeable` - Occurs whenever a source transitions to chargeable.
* `SourceFailedWebhook` - `source.failed` - Occurs whenever a source fails.
* `SourceMandateNotificationWebhook` - `source.mandate_notification` - Occurs whenever a source mandate notification method is set to manual.
* `SourceRefundAttributesRequiredWebhook` - `source.refund_attributes_required` - Occurs whenever the refund attributes are required on a receiver source to process a refund or a mispayment.
* `SourceTransactionCreatedWebhook` - `source.transaction.created` - Occurs whenever a source transaction is created.
* `SourceTransactionUpdatedWebhook` - `source.transaction.updated` - Occurs whenever a source transaction is updated.
* `SubscriptionScheduleAbortedWebhook` - `subscription_schedule.aborted` - Occurs whenever a subscription schedule is canceled due to the underlying subscription being canceled because of delinquency.
* `SubscriptionScheduleCanceledWebhook` - `subscription_schedule.canceled` - Occurs whenever a subscription schedule is canceled.
* `SubscriptionScheduleCompletedWebhook` - `subscription_schedule.completed` - Occurs whenever a new subscription schedule is completed.
* `SubscriptionScheduleCreatedWebhook` - `subscription_schedule.created` - Occurs whenever a new subscription schedule is created.
* `SubscriptionScheduleExpiringWebhook` - `subscription_schedule.expiring` - Occurs 7 days before a subscription schedule will expire.
* `SubscriptionScheduleReleasedWebhook` - `subscription_schedule.released` - Occurs whenever a new subscription schedule is released.
* `SubscriptionScheduleUpdatedWebhook` - `subscription_schedule.updated` - Occurs whenever a subscription schedule is updated.
* `TaxRateCreatedWebhook` - `tax_rate.created` - Occurs whenever a new tax rate is created.
* `TaxRateUpdatedWebhook` - `tax_rate.updated` - Occurs whenever a tax rate is updated.
* `TopupCanceledWebhook` - `topup.canceled` - Occurs whenever a top-up is canceled.
* `TopupCreatedWebhook` - `topup.created` - Occurs whenever a top-up is created.
* `TopupFailedWebhook` - `topup.failed` - Occurs whenever a top-up fails.
* `TopupReversedWebhook` - `topup.reversed` - Occurs whenever a top-up is reversed.
* `TopupSucceededWebhook` - `topup.succeeded` - Occurs whenever a top-up succeeds.
* `TransferCreatedWebhook` - `transfer.created` - Occurs whenever a transfer is created.
* `TransferFailedWebhook` - `transfer.failed` - Occurs whenever a transfer failed.
* `TransferPaidWebhook` - `transfer.paid` - Occurs after a transfer is paid. For Instant Payouts, the event will typically be sent within 30 minutes.
* `TransferReversedWebhook` - `transfer.reversed` - Occurs whenever a transfer is reversed, including partial reversals.
* `TransferUpdatedWebhook` - `transfer.updated` - Occurs whenever a transfer's description or metadata is updated.
