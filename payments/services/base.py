from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    name = "base"
    method = "base"

    @abstractmethod
    def initiate(self, payment):
        pass

    def verify_webhook(self, request):
        return True

    def handle_webhook(self, payload):
        raise NotImplementedError