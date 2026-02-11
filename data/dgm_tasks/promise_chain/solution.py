class Promise:
    def __init__(self, executor):
        """executor is a function(resolve, reject)"""
        pass

    def then(self, on_fulfilled=None, on_rejected=None):
        """Return new Promise. Chain callbacks."""
        pass

    def catch(self, on_rejected):
        """Shorthand for then(None, on_rejected)."""
        pass

    @staticmethod
    def resolve(value):
        """Return a resolved Promise."""
        pass

    @staticmethod
    def reject(reason):
        """Return a rejected Promise."""
        pass
