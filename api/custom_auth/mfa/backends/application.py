from trench.backends.application import ApplicationMessageDispatcher


class CustomApplicationMessageDispatcher(ApplicationMessageDispatcher):
    def dispatch_message(self):
        original_message = super(
            CustomApplicationMessageDispatcher, self
        ).dispatch_message()
        data = {**original_message, "secret": self.obj.secret}
        return data
