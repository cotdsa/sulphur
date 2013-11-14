import flask
import pprint
import json

from sulphur.misc import verify_signature, build_signature_string, subscribe_sns_topic
from sulphur.handler import CustomResourceHandler

application = flask.Flask(__name__)

#Set application.debug=true to enable tracebacks on Beanstalk log output.
#Make sure to remove this line before deploying to production.
application.debug=True

@application.route('/', methods=['GET', 'POST'])
def index():
    # Parse the notification type
    message_type = flask.request.headers.get('x-amz-sns-message-type', None)
    if not message_type:
        # This doesn't look like a valid SNS message
        flask.abort(403)

    # Try to parse JSON data
    json_data = flask.request.get_json(force=True)
    if not json_data:
        # Nope, something is wrong
        flask.abort(403)

    # Verify the authenticity of the message
    if not verify_signature(cert_url=json_data['SigningCertURL'], signature=json_data['Signature'], data=build_signature_string(json_data)):
        # Signature is not valid. not good
        flask.abort(403)

    if message_type == 'SubscriptionConfirmation':
        # Handle the subscription request
        subscribe_sns_topic(token=json_data['Token'], topic_arn=json_data['TopicArn'])

    if message_type == 'Notification':
        subj = json_data.get('Subject', None)
        mesg = json_data.get('Message', None)
        if subj == 'AWS CloudFormation custom resource request':
            # Decode json message
            cf_data = json.loads(mesg)
            sulphur = CustomResourceHandler(cf_data)
            sulphur.handle()

    return 'ok'




if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
    create_msg = {u'LogicalResourceId': u'myUserResource',
 u'RequestId': u'2c06d1c2-0fb5-4bbb-bf3b-f0da8925975f',
 u'RequestType': u'Create',
 u'ResourceProperties': {u'ServiceToken': u'arn:aws:sns:us-west-2:352964764186:sulphur',
                         u'key1': u'string',
                         u'key2': [u'list'],
                         u'key3': {u'key4': u'map'}},
 u'ResourceType': u'Custom::TestCustomResource',
 u'ResponseURL': u'https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A352964764186%3Astack/vodka-custom2/27cc59f0-4ccc-11e3-a1b8-50e2414b0a18%7CmyUserResource%7C59761679-fd4f-47bc-91da-36a76dbadc92?Expires=1384406314&AWSAccessKeyId=AKIAI4KYMPPRGIACET5Q&Signature=DWXAIPp8DLJOV9NvW4tZuFwTl5k%3D',
 u'StackId': u'arn:aws:cloudformation:us-west-2:352964764186:stack/vodka-custom/e4f18150-4c3f-11e3-8ed4-500160d4da44',
 u'TopicArn': u'arn:aws:sns:us-west-2:352964764186:sulphur'}

    delete_msg = {u'LogicalResourceId': u'myUserResource',
 u'PhysicalResourceId': u'vodka-custom2-myUserResource-PQ7FXQWIE1Q4',
 u'RequestId': u'81b5a797-c117-40e9-967e-fe39de578848',
 u'RequestType': u'Delete',
 u'ResourceProperties': {u'ServiceToken': u'arn:aws:sns:us-west-2:352964764186:sulphur',
                         u'key1': u'string',
                         u'key2': [u'list'],
                         u'key3': {u'key4': u'map'}},
 u'ResourceType': u'Custom::TestCustomResource',
 u'ResponseURL': u'https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A352964764186%3Astack/vodka-custom2/27cc59f0-4ccc-11e3-a1b8-50e2414b0a18%7CmyUserResource%7C59761679-fd4f-47bc-91da-36a76dbadc92?Expires=1384406314&AWSAccessKeyId=AKIAI4KYMPPRGIACET5Q&Signature=DWXAIPp8DLJOV9NvW4tZuFwTl5k%3D',
 u'StackId': u'arn:aws:cloudformation:us-west-2:352964764186:stack/vodka-custom/e4f18150-4c3f-11e3-8ed4-500160d4da44',
 u'TopicArn': u'arn:aws:sns:us-west-2:352964764186:sulphur'}

    #sulphur = CustomResourceHandler(delete_msg)
    #sulphur.handle()