import requests
import re
import json
import uuid

from os.path import dirname
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileAnalyzerMathingRegex, PluginFileLocator

from .abstracts import CFCustomResourceHandler


class ResponseObject(object):

    def __init__(self, request_type):

        self.data = {}

        self._status = 'SUCCESS'
        self._reason = ''
        self._logical_resource_id = None
        self._request_id = None
        self._stack_id = None
        self._physical_resource_id = None
        self._request_type = request_type


    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if status in ('SUCCESS', 'FAILED'):
            self._status = status
        else:
            raise AttributeError('`status` property can be only set to SUCCESS or FAILED')

    @property
    def reason(self):
        return self._reason

    @reason.setter
    def reason(self, reason):
        if self._status == 'FAILED':
            self._reason = reason
        else:
            raise AttributeError('`reason` property can be set only if set to FAILED')


    @property
    def physical_resource_id(self):
        return self._physical_resource_id

    @physical_resource_id.setter
    def physical_resource_id(self, physical_resource_id):
        if len(physical_resource_id) < 1024:
            self._physical_resource_id = physical_resource_id
        else:
            raise AttributeError('`physical_resource_id` property can be only up to 1k in size')

    def dumps(self):

        if not isinstance(self.data, dict):
            raise RuntimeError('`data` property must be a dictionary')

        response = {
            'Status': self._status,
            'StackId': self._stack_id,
            'RequestId': self._request_id,
            'LogicalResourceId': self._logical_resource_id,
        }
        if self._reason:
            response['Reason'] = self._reason
        if self._physical_resource_id:
            response['PhysicalResourceId'] = self._physical_resource_id
        if self.data and self._request_type != 'Delete':
            response['Data'] = self.data

        return json.dumps(response)

class CustomResourceHandler(object):

    def __init__(self, input_data_dict):

        self.manager = self.init_manager()

        # Store request data
        self.resource_type = input_data_dict.get('ResourceType')
        self.response_url = input_data_dict.get('ResponseURL')
        self.stack_id = input_data_dict.get('StackId')
        self.request_id = input_data_dict.get('RequestId')
        self.request_type = input_data_dict.get('RequestType')
        self.topic_arn = input_data_dict.get('TopicArn')
        self.logical_resource_id = input_data_dict.get('LogicalResourceId')
        self.physical_resource_id = input_data_dict.get('PhysicalResourceId')
        self.res_properties = input_data_dict.get('ResourceProperties')
        self.old_res_properties = input_data_dict.get('OldResourceProperties')

        self.rgx = re.compile(r'^Custom::([A-Za-z0-9]+)$')


    @staticmethod
    def init_manager():
        anl = PluginFileAnalyzerMathingRegex('custom_res_handler_plugins', r'^[A-Za-z0-9]+\.py$')
        res = PluginFileLocator(plugin_info_cls=CFCustomResourceHandler)
        res.setAnalyzers([anl])
        manager = PluginManager(plugin_locator=res, categories_filter={'CFHandlers' : CFCustomResourceHandler})
        manager.setPluginPlaces([dirname(__file__) + '/plugins'])
        manager.collectPlugins()
        return manager

    @staticmethod
    def generate_policy():

        manager = CustomResourceHandler.init_manager()
        policy_base = {
            "Id": "Sulphur-IAM-Policy",
            "Version": "2012-10-17",
            "Statement": []
        }

        policy_statement = {
            "Sid": "",
            "Effect": "Allow",
            "Action": [],
            "Resource": ["*"]
        }


        plugins = manager.getPluginsOfCategory('CFHandlers')
        for plugin in plugins:
            if plugin.plugin_object.required_iam_perms:
                plg_policy = policy_statement.copy()
                plg_policy['Sid'] = plugin.name
                plg_policy['Action'] = plugin.plugin_object.required_iam_perms
                policy_base['Statement'].append(plg_policy)
        return policy_base



    def handle(self):

        # Initialise the response object
        resp_obj = ResponseObject(self.request_type)
        resp_obj._request_id = self.request_id
        resp_obj._logical_resource_id = self.logical_resource_id
        resp_obj._physical_resource_id = self.physical_resource_id
        resp_obj._stack_id = self.stack_id
        resp_obj._request_type = self.resource_type

        mtc = self.rgx.match(self.resource_type)

        success = False
        ret_data = {}

        if not self.physical_resource_id:
            resp_obj.physical_resource_id = 'SULPH-%s-%s' % (self.logical_resource_id, str(uuid.uuid4()))

        if mtc:
            type = mtc.group(1)
            plg = self.manager.getPluginByName(type, category='CFHandlers')
            if plg:
                plg.plugin_object.activate()
                plg.plugin_object.setProperties(self.res_properties)
                plg.plugin_object.setResponse(resp_obj)
                plg.plugin_object.setOldProperties(self.old_res_properties)
                try:
                    if self.request_type == 'Create':
                        plg.plugin_object.create()
                    elif self.request_type == 'Update':
                        plg.plugin_object.update()
                    elif self.request_type == 'Delete':
                        plg.plugin_object.delete()
                    else:
                        print "Unknown operation"
                except Exception, e:
                    print str(e)
                    resp_obj.reason = str(e)
                    pass

                plg.plugin_object.deactivate()
            else:
                resp_obj.status = 'FAILED'
                resp_obj.reason = 'Sulphur: No handler could be found for resource type %s' % type
        else:
            resp_obj.status = 'FAILED'
            resp_obj.reason = 'Sulphur: Resource Type must be of form `Custom::<ResourceType>`. Found %s instead.' % self.resource_type

        # Respond to CloudFormation
        print resp_obj.dumps()
        res = requests.put(url=self.response_url, data=resp_obj.dumps(), headers={'content-type': ''})











