from yapsy.IPlugin import IPlugin

class CFCustomResourceHandler(IPlugin):
    properties = None
    response = None
    old_properties = None

    required_iam_perms = []

    def activate(self):
        super(CFCustomResourceHandler, self).activate()


    def setProperties(self, properties):
        self.properties = properties

    def setResponse(self, response):
        self.response = response

    def setOldProperties(self, old_properties):
        self.old_properties = old_properties

    def create(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass