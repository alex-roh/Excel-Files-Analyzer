import inspect

class Observable:
    def __init__(self):
        self._observer = None

    def attach(self, observer):
        if self._observer is None:
            self._observer = observer
        else:
            print(f"{inspect.currentframe().f_code.co_name}: Already attached to an observer.")
           
    def detach(self):
        if self._observer:
            self._observer = None
        else:
            print(f"{inspect.currentframe().f_code.co_name}: There is no observer to detach.")

    def notify(self, *args, **kwargs):
        response = self._observer.update(*args, **kwargs)
        return response if response else None
