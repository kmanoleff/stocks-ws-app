import json
import logging
import time

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from aws_lambda_powertools.utilities.data_classes import event_source, APIGatewayProxyEvent
from models import WebsocketResponse


@event_source(data_class=APIGatewayProxyEvent)
def lambda_handler(event, context):
    logger.info(json.dumps(event.__dict__))
    # values from the event
    domain_name = event.request_context.domain_name
    stage = event.request_context.stage
    connection_id = event.request_context.connection_id
    request_body = json.loads(event.body)
    # create client, return initial accepted response
    client = boto3.client('apigatewaymanagementapi', endpoint_url='https://' + domain_name + '/' + stage)
    initial_connection = WebsocketResponse()
    initial_connection.statusCode = 202
    initial_connection.message = {'accepted': True}
    client.post_to_connection(ConnectionId=connection_id, Data=initial_connection.json())

    websocket_response = WebsocketResponse()
    try:
        # polygon stocks api endpoint
        base_api_endpoint = 'https://api.polygon.io/v2/aggs/ticker/'
        api_endpoint_suffix = '/range/1/day/2022-03-25/2022-03-27?apiKey=taIMgMrmnZ8SUZmdpq9_7ANRDxw3IPIx'
        # retrieve ticker from request, required field
        requested_ticker = request_body.get('ticker')
        # ticker required
        if requested_ticker is None or requested_ticker == '':
            websocket_response.statusCode = 400
            websocket_response.message = {'error': 'ticker is required'}
            client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
            client.delete_connection(ConnectionId=connection_id)
            return {'statusCode': 400}
        # use the ticker in api request
        logger.info('Getting stocks for ticker : ' + requested_ticker)
        stocks_api_response = requests.get(url=base_api_endpoint + requested_ticker + api_endpoint_suffix)
        logger.info(json.dumps(stocks_api_response.json()))
        # return the successful results
        websocket_response.statusCode = 200
        websocket_response.message = stocks_api_response.json()
        # --- emulate the long-running task ---
        time.sleep(31)
        client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
        client.delete_connection(ConnectionId=connection_id)
        return {"statusCode": 200}
    except Exception as e:
        websocket_response.statusCode = 500
        websocket_response.message = {'error': str(e)}
        client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
        client.delete_connection(ConnectionId=connection_id)
        return {"statusCode": 500}
