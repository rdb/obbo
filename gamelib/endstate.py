class EndState:
    def __init__(self, universe):
        universe.cleanup()

    def cleanup(self):
        pass

    def update(self, _dt):
        base.change_state('MainMenu')
