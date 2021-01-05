


from bergen.registries.arnheim import get_current_arnheim


class BaseExtender:
    extension = None

    def getSettings(self):
        return get_current_arnheim().getExtensionSettings(self.extension)



    pass