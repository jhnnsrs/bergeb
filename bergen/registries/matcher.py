
class TypeMatcher:

    def __init__(self) -> None:
        self.map = {}

    def registerModelForIdentifier(self,identifier, model, overwrite=False):
        identifier = identifier.lower()
        if identifier in self.map: 
            assert overwrite is True, "Attempting to overwrite, please provide overwrite in Call"
            print(f"Overwriting {self.map[identifier]} with {model} for {identifier}")
        self.map[identifier] = model

    def getModelForIdentifier(self, identifier):
        identifier = identifier.lower()
        assert identifier in self.map, f"Nothing stored for for identifier {identifier}, please provide a valid Model and store it"
        return self.map[identifier]




CURRENT_MATCHER = None

def get_current_matcher():
    global CURRENT_MATCHER
    if CURRENT_MATCHER is None:
        CURRENT_MATCHER = TypeMatcher()
   
    return CURRENT_MATCHER