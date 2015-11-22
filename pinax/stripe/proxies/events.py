from .. import models

from .customers import CustomerProxy


class EventProxy(models.Event):

    class Meta:
        proxy = True

    @property
    def message(self):
        return self.validated_message

    def link_customer(self):
        cus_id = None
        customer_crud_events = [
            "customer.created",
            "customer.updated",
            "customer.deleted"
        ]
        if self.kind in customer_crud_events:
            cus_id = self.message["data"]["object"]["id"]
        else:
            cus_id = self.message["data"]["object"].get("customer", None)

        if cus_id is not None:
            try:
                self.customer = CustomerProxy.objects.get(stripe_id=cus_id)
                self.save()
            except models.Customer.DoesNotExist:
                pass
