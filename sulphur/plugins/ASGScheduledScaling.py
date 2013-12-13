import boto.ec2.autoscale
import dateutil.parser
from sulphur.abstracts import CFCustomResourceHandler


class ASGScheduledScalingHandler(CFCustomResourceHandler):

    # This handler manages and hosted zone in route 53
    #
    # Required IAM permissions:
    # - autoscaling:PutScheduledUpdateGroupAction
    # - autoscaling:DeleteScheduledAction

    def create(self):

        self.response.status = 'FAILED'

        region = self.properties.get('Region')
        asg = self.properties.get('AutoScalingGroup')
        desired_capacity = self.properties.get('DesiredCapacity')
        min_size = self.properties.get('MinSize')
        max_size = self.properties.get('MaxSize')
        start_time = self.properties.get('StartTime')
        end_time = self.properties.get('EndTime')
        recurrence = self.properties.get('Recurrence')
        group_action_id = self.response.physical_resource_id

        if region not in [reg.name for reg in boto.ec2.autoscale.regions()]:
            self.response.reason = 'Region %s is not supported or invalid' % region
            return
        if desired_capacity and not desired_capacity.isdigit():
            self.response.reason = 'DesiredCapacity must be numeric'
            return
        if min_size and not min_size.isdigit():
            self.response.reason = 'MinSize must be numeric'
            return
        if max_size and not max_size.isdigit():
            self.response.reason = 'MaxSize must be numeric'
            return

        if not start_time and not recurrence:
            self.response.reason = 'Scheduled start time must be specified for non-recurrent future'
            return

        start_time_dt = None
        if start_time:
            start_time_dt = dateutil.parser.parse(start_time)

        end_time_dt = None
        if end_time:
            end_time_dt = dateutil.parser.parse(end_time)

        conn = boto.ec2.autoscale.connect_to_region(region_name=region)
        assert isinstance(conn, boto.ec2.autoscale.AutoScaleConnection)

        res = conn.create_scheduled_group_action(as_group=asg, name=group_action_id,
                                                 desired_capacity=desired_capacity,
                                                 min_size=min_size,
                                                 max_size=max_size,
                                                 start_time=start_time_dt,
                                                 end_time=end_time_dt,
                                                 recurrence=recurrence)
        if not res:
            self.response.reason = 'Unable to create Scheduled Action'
            return

        self.response.status = 'SUCCESS'

    def update(self):
        # Update uses the same API call of create so no need to duplicate code here.
        # The physical_resource_id will be used to update the existing one
        self.create()

    def delete(self):

        self.response.status = 'FAILED'

        region = self.properties.get('Region')
        asg = self.properties.get('AutoScalingGroup')
        group_action_id = self.response.physical_resource_id

        if region not in [reg.name for reg in boto.ec2.autoscale.regions()]:
            self.response.reason = 'Region %s is not supported or invalid' % region
            return

        conn = boto.ec2.autoscale.connect_to_region(region_name=region)
        assert isinstance(conn, boto.ec2.autoscale.AutoScaleConnection)

        res = conn.delete_scheduled_action(scheduled_action_name=group_action_id, autoscale_group=asg)
        if not res:
            self.response.reason = 'Unable to delete Scheduled Action'
            return

        self.response.status = 'SUCCESS'
