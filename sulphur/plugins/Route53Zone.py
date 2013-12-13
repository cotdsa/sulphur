import boto.route53
from boto.route53.zone import Zone
from sulphur.abstracts import CFCustomResourceHandler

class Route53ZoneHandler(CFCustomResourceHandler):

    # This handler manages and hosted zone in route 53
    #
    # Required IAM permissions:
    # - route53:CreateHostedZone


    def create(self):

        self.response.status = 'FAILED'


        zone_name = self.properties.get('ZoneName')

        if not zone_name.endswith('.'):
            self.response.reason = 'ZoneName must end with a dot character'
            return

        conn = boto.route53.Route53Connection()

        resp = conn.create_hosted_zone(domain_name=zone_name)
        zone = Zone(self, resp['CreateHostedZoneResponse']['HostedZone'])
        delegation_set = resp['DelegationSet']['NameServers']

        self.response.physical_resource_id = zone.id
        self.response.data = {
            'DelegationSet': delegation_set
        }
        self.response.status = 'SUCCESS'


