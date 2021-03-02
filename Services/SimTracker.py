class SimTracker():

    def __init__(self):
        self.snapshots = []
        self.listeners = []

    def add_shapshot(self, snapshot):
        self.snapshots.append(snapshot)
        self.post_update()

    def add_listener(self, listener):
        self.listeners.append(listener)

    def post_update(self):
        for listener in self.listeners:
            listener.notify()
