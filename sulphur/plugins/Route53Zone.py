import boto.route53
from boto.route53.zone import Zone
from sulphur.abstracts import CFCustomResourceHandler

class Route53ZoneHandler(CFCustomResourceHandler):

    # This handler manages and hosted zone in route 53
    #
    # Required IAM permissions:
    # - route53:CreateHostedZone
    # - route53:DeleteHostedZone


    def create(self):

        self.response.status = 'FAILED'


        zone_name = self.properties.get('ZoneName')

        if not zone_name.endswith('.'):
            self.response.reason = 'ZoneName must end with a dot character'
            return

        conn = boto.route53.Route53Connection()

        resp = conn.create_hosted_zone(domain_name=zone_name)
        zone = Zone(self, resp['CreateHostedZoneResponse']['HostedZone'])
        delegation_set = resp['CreateHostedZoneResponse']['DelegationSet']['NameServers']

        self.response.physical_resource_id = zone.id
        self.response.data = {
            'DelegationSet': delegation_set
        }
        self.response.status = 'SUCCESS'

    def update(self):
        # Documentation states:
        #
        # You can update custom resources that require a replacement of the underlying physical resource.
        # When you update a custom resource in an AWS CloudFormation template,
        # AWS CloudFormation sends an update request to that custom resource.
        # If a custom resource requires a replacement,
        # the new custom resource must send a response with the new physical ID.
        # When AWS CloudFormation receives the response, it compares the PhysicalResourceId between the old and new custom resources.
        # If they are different, AWS CloudFormation recognizes the update as a replacement and sends a delete request to the old resource.
        #
        # In this case we just need to call create() and CF will issue the delete automatically
        self.create()

    def delete(self):

        self.response.status = 'FAILED'
        zone_id = self.response.physical_resource_id

        conn = boto.route53.Route53Connection()

        conn.delete_hosted_zone(hosted_zone_id=zone_id)
        self.response.status = 'SUCCESS'


