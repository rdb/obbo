class EndState:
    def __init__(self, universe):
        universe.cleanup()

    def update(self, _dt):
        pass
