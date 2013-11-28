from sulphur.abstracts import CFCustomResourceHandler


class TestCustomResourceHandler(CFCustomResourceHandler):

    def create(self):
        self.response.ddb.m2.xlargeata = {'Testdata': 'TEST TEST TEST'}
        self.response.status = 'SUCCESS'

    def update(self):
        self.response.data = {'Testdata': 'TEST TEST TEST'}
        self.response.status = 'SUCCESS'

    def delete(self):
        print "Deleting"
        self.response.status = 'SUCCESS'
        self.response.data = {'Asd':'ASd'}

