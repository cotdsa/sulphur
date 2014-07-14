import re
import requests
import boto.sns
import rsa

from pyasn1.codec.der.decoder import decode
from pyasn1_modules import rfc2459
from bitstring import BitArray

def load_pem(contents):
    def byte_literal(s):
        return s.encode('latin1')

    pem_start = '-----BEGIN CERTIFICATE-----'
    pem_end = '-----END CERTIFICATE-----'

    pem_lines = []
    in_pem_part = False

    for line in contents.splitlines():
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Handle start marker
        if line == pem_start:
            if in_pem_part:
                raise ValueError('Seen start marker "%s" twice' % pem_start)

            in_pem_part = True
            continue

        # Skip stuff before first marker
        if not in_pem_part:
            continue

        # Handle end marker
        if in_pem_part and line == pem_end:
            in_pem_part = False
            break

        # Load fields
        if byte_literal(':') in line:
            continue

        pem_lines.append(line)

    # Do some sanity checks
    if not pem_lines:
        raise ValueError('No PEM start marker "%s" found' % pem_start)

    if in_pem_part:
        raise ValueError('No PEM end marker "%s" found' % pem_end)

    # Base64-decode the contents
    pem = byte_literal('').join(pem_lines)
    return pem.decode('base64')

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
        try:
            decoded_cert, _ = decode(load_pem(cert.content), asn1Spec=rfc2459.Certificate())
            pubkey_bits = BitArray(list(decoded_cert['tbsCertificate']['subjectPublicKeyInfo']['subjectPublicKey']))
            rsaobj = rsa.PublicKey.load_pkcs1(pubkey_bits.bytes, format='DER')
            return rsa.verify(data, signature.decode('base64'), rsaobj)
        except Exception, e:
            raise
    return False

def subscribe_sns_topic(token, topic_arn, authenticate_on_unsubscribe=False):
    parsed_arn = parse_sns_arn(topic_arn)
    sns_conn = boto.sns.connect_to_region(parsed_arn['region'])
    sns_conn.confirm_subscription(topic=topic_arn, token=token, authenticate_on_unsubscribe=authenticate_on_unsubscribe)