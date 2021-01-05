
class TypeMatcher:

    def __init__(self) -> None:
        self.map = {}

    def registerModelForIdentifier(self,identifier, model, overwrite=False):
        identifier = identifier.lower()
        if not overwrite:
            assert identifier not in self.map, "You can not register two ArnheimModels on the same identifier, please specifiy overwrite_default == True, or register == False in your ArnheimModel meta"
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