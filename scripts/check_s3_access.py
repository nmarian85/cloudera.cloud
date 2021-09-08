import boto3
from datetime import datetime, timedelta
import time
import json


client = boto3.client("logs")


# query = "fields @timestamp, @message"
# query += " | parse @message \"username: * ClinicID: * nodename: *\" as username, ClinicID, nodename"
# query += " | filter ClinicID = 7667 and username='simran+test@abc.com'"

query = "fields @message"
query += " | filter isPresent(errorCode) and errorCode != 'NoSuchKey' and requestParameters.bucketName != 'ecb-aws-s3-config-do-not-delete'"
query += " | sort @timestamp desc"
query += " | limit 200"


# log_group = "devo-lab-cloudtrail-s3-data-events"
# log_group = "devo-lab-cloudtrail-s3-data-events"
log_group = "devo-cdp-cloudtrail-s3-data-events"
# log_group = "devo-cdp-cloudtrail-service-events"
# log_group = '/aws/lambda/NAME_OF_YOUR_LAMBDA_FUNCTION'


start_query_response = client.start_query(
    logGroupName=log_group,
    startTime=int((datetime.today() - timedelta(hours=12)).timestamp()),
    endTime=int(datetime.now().timestamp()),
    queryString=query,
)


query_id = start_query_response["queryId"]


response = None


while response is None or response["status"] == "Running":
    print("Waiting for query to complete ...")
    time.sleep(1)
    response = client.get_query_results(queryId=query_id)


events = [json.loads(msg[0]["value"]) for msg in response["results"]]


for event in events:
    print(event["errorCode"] + " " + event["eventName"] + " " + event["userIdentity"]["arn"])


with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=4)
