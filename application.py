import flask
import json

from sulphur.misc import verify_signature, build_signature_string, subscribe_sns_topic
from sulphur.handler import CustomResourceHandler

application = flask.Flask(__name__)

#Set application.debug=true to enable tracebacks on Beanstalk log output.
#Make sure to remove this line before deploying to production.
application.debug = True


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
    if not verify_signature(cert_url=json_data['SigningCertURL'],
                            signature=json_data['Signature'],
                            data=build_signature_string(json_data)):
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
