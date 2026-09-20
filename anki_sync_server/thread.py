from threading import Thread


class ThreadWithReturnValue(Thread):
    """Thread with a return value.

    Source:
    https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread
    """

    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None
    ):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
        self._exception = None

    def run(self):
        if self._target is not None:
            try:
                self._return = self._target(*self._args, **self._kwargs)
            except Exception as e:
                # Store exception to propagate to join()
                # Note: KeyboardInterrupt and SystemExit inherit from BaseException,
                # not Exception, so they will not be caught here
                self._exception = e

    def join(self, *args):
        Thread.join(self, *args)
        if self._exception is not None:
            raise self._exception
        return self._return
