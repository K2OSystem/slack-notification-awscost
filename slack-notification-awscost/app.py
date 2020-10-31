import json
import logging
import os
from datetime import datetime, timedelta

import boto3
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Slack の設定
SLACK_POST_URL = os.environ['SLACK_POST_URL']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
SLACK_TOKEN = os.environ['SLACK_TOKEN']

client = boto3.client('cloudwatch', region_name='us-east-1')

get_metric_statistics = client.get_metric_statistics(
    Namespace='AWS/Billing',
    MetricName='EstimatedCharges',
    Dimensions=[
        {
            'Name': 'Currency',
            'Value': 'USD'
        }
    ],
    StartTime=datetime.today() - timedelta(days=1),
    EndTime=datetime.today(),
    Period=86400,
    Statistics=['Maximum']
)

print('get_metric_statistics', get_metric_statistics)
cost = get_metric_statistics['Datapoints'][0]['Maximum']
date = get_metric_statistics['Datapoints'][0]['Timestamp'].strftime('%Y-%m-%d')


def build_message(cost):
    if float(cost) >= 10.0:
        color = "#ff0000" # red
    elif float(cost) > 0.0:
        color = "warning" # yellow
    else:
        color = "good" # green

    text = "{}までのAWS料金は、${}です。".format(date, cost)

    atachments = {"text":text, "color":color}
    
    return atachments


def lambda_handler(event, context):

    content = build_message(cost)

    # SlackにPOST
    try:
        headers = {'Authorization': 'Bearer {}'.format(SLACK_TOKEN)}
        slack_message = {'channel': SLACK_CHANNEL, 'attachments': [content]}
        # slack通知
        requests.post(SLACK_POST_URL, headers=headers, json=slack_message)

        logger.info("Message posted to {}".format(slack_message['channel']))

    except requests.exceptional.RequestException as e:
        logger.error("Request failed: {}".format(e))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "success",
        }),
    }
