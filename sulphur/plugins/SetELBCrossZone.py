import boto.ec2.elb
from sulphur.abstracts import CFCustomResourceHandler

class SetELBCrossZoneHandler(CFCustomResourceHandler):

    # This handler allows you to set the CrossZoneLoadBalancing attribute of an ELB
    #
    # Required IAM permissions:
    # - elasticloadbalancing:ModifyLoadBalancerAttributes
    #
    # This module requires boto >= 2.18.0


    def create(self):

        self.response.status = 'FAILED'

        region = self.properties.get('Region')
        elb = self.properties.get('LoadBalancerName')
        value = self.properties.get('EnableCrossZoneLoadBalancing')
        if region not in [ reg.name for reg in boto.ec2.elb.regions() ]:
            self.response.reason = 'Region %s is not supported or invalid' % region
            return

        if value.lower() not in ('true', 'false'):
            self.response.reason = 'EnableCrossZoneLoadBalancing must be `true` or `false`'
            return

        b_value = True if value == 'true' else False

        conn = boto.ec2.elb.connect_to_region(region)

        if conn.modify_lb_attribute(load_balancer_name=elb, attribute='crosszoneloadbalancing', value=b_value):
            self.response.status = 'SUCCESS'
        else:
            self.response.reason = 'Unable to set CrossZoneLoadBalancing attribute'

    def update(self):
        # No need to have duplicate code here
        self.create()

