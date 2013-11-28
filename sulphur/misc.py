import re
import requests
import base64
import boto.sns
import OpenSSL.crypto

def parse_sns_arn(arn):
    regex = re.compile(r"arn:aws:sns:(?P<region>[a-z0-9-]+):(?P<account_id>[0-9]+):(?P<sns_id>.+)")
    r = regex.search(arn)
    if not r:
        raise ValueError("Argument '%s' doesn't appear to be a valid Amazon SNS ARN", arn)

    return r.groupdict()

def build_signature_string(data_dict):
    verify_string = ''
    verify_string += "Message\n%s\n" % data_dict['Message']
    verify_string += "MessageId\n%s\n" % data_dict['MessageId']
    if data_dict['Type'] == 'Notification':
        if data_dict.get('Subject', False):
            verify_string += "Subject\n%s\n" % data_dict['Subject']
        verify_string += "Timestamp\n%s\n" % data_dict['Timestamp']

    if data_dict['Type'] == 'SubscriptionConfirmation' or data_dict['Type'] == 'UnsubscribeConfirmation':
        verify_string += "SubscribeURL\n%s\n" % data_dict['SubscribeURL']
        verify_string += "Timestamp\n%s\n" % data_dict['Timestamp']
        verify_string += "Token\n%s\n" % data_dict['Token']

    verify_string += "TopicArn\n%s\n" % data_dict['TopicArn']
    verify_string += "Type\n%s\n" % data_dict['Type']

    return verify_string

def verify_signature(cert_url, signature, data):
    cert = requests.get(cert_url)
    if cert.status_code == 200:
        x509obj = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert.content)
        ds = base64.b64decode(signature)
        try:
            OpenSSL.crypto.verify(x509obj, ds, data, 'sha1')
            return True
        except OpenSSL.crypto.Error:
            raise
    return False

def subscribe_sns_topic(token, topic_arn, authenticate_on_unsubscribe=False):
    parsed_arn = parse_sns_arn(topic_arn)
    sns_conn = boto.sns.connect_to_region(parsed_arn['region'])
    sns_conn.confirm_subscription(topic=topic_arn, token=token, authenticate_on_unsubscribe=authenticate_on_unsubscribe)