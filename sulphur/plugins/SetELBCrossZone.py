import boto.ec2.elb
from sulphur.abstracts import CFCustomResourceHandler

class SetELBCrossZoneHandler(CFCustomResourceHandler):

    def create(self):

        self.response.status = 'FAILED'

        region = self.properties.get('Region')
        elb = self.properties.get('LoadBalancerName')
        value = self.properties.get('EnableCrossZoneLoadBalancing')

        if region not in boto.ec2.elb.regions():
            self.response.reason = 'Region %s is not supported or invalid' % region
            return

        if value.lower() not in ('true', 'false'):
            self.response.reason = 'EnableCrossZoneLoadBalancing must be `true` or `false`'
            return

        conn = boto.ec2.elb.connect_to_region(region)

        params = {
            'LoadBalancerName': elb,
            'LoadBalancerAttributes.CrossZoneLoadBalancing.Enabled': value
        }

        if conn.get_status('ModifyLoadBalancerAttributes', params):
            self.response.status = 'SUCCESS'
        else:
            self.response.reason = 'Unable to set CrossZoneLoadBalancing attribute'

    def update(self):
        # No need to have duplicate code here
        self.create()

