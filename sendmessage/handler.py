import json
import logging
import time

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from aws_lambda_powertools.utilities.data_classes import event_source, APIGatewayProxyEvent
from models import WebsocketResponse, ReportData


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
    initial_connection = WebsocketResponse(status_code=202, report_data=None, message='accepted')
    client.post_to_connection(ConnectionId=connection_id, Data=initial_connection.json())
    try:
        # polygon stocks api endpoint
        base_api_endpoint = 'https://api.polygon.io/v2/aggs/ticker/'
        api_endpoint_suffix = '/range/1/day/2020-01-01/2020-12-31?apiKey=taIMgMrmnZ8SUZmdpq9_7ANRDxw3IPIx'
        # retrieve ticker from request, required field
        requested_ticker = request_body.get('ticker')
        # ticker required
        if requested_ticker is None or requested_ticker == '':
            websocket_response = WebsocketResponse(status_code=400, report_data=None, message='ticker required')
            client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
            client.delete_connection(ConnectionId=connection_id)
            return {'statusCode': 400}
        # use the ticker in api request
        logger.info('Getting stocks for ticker : ' + requested_ticker)
        stocks_api_response = requests.get(url=base_api_endpoint + requested_ticker + api_endpoint_suffix)
        logger.info(json.dumps(stocks_api_response.json()))
        # create the report
        if stocks_api_response.json().get('results') is None:
            websocket_response = WebsocketResponse(status_code=404, report_data=None, message='no results found')
            client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
            client.delete_connection(ConnectionId=connection_id)
            return {'statusCode': 404}
        report_data = create_report(stocks_api_response.json())
        # return the successful results
        websocket_response = WebsocketResponse(status_code=200, report_data=report_data, message='success')
        # --- emulate the long-running task ---
        time.sleep(31)
        client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
        client.delete_connection(ConnectionId=connection_id)
        return {"statusCode": 200}
    except Exception as e:
        websocket_response = WebsocketResponse(status_code=500, report_data=None, message=str(e))
        client.post_to_connection(ConnectionId=connection_id, Data=websocket_response.json())
        client.delete_connection(ConnectionId=connection_id)
        return {"statusCode": 500}


def create_report(stocks_response):
    min_stock = None
    max_stock = None
    min_volume = None
    max_volume = None
    rolling_low = None
    rolling_high = None

    result_list = stocks_response.get('results')
    for index, result in enumerate(result_list):
        current_result_lowest_price = result['l']
        current_result_highest_price = result['h']
        current_result_volume = result['v']
        if index == 0:
            min_stock = current_result_lowest_price
            max_stock = current_result_highest_price
            min_volume = current_result_volume
            max_volume = current_result_volume
            rolling_low = current_result_lowest_price
            rolling_high = current_result_highest_price
        else:
            if current_result_lowest_price < min_stock:
                min_stock = current_result_lowest_price
            if current_result_highest_price > max_stock:
                max_stock = current_result_highest_price
            if current_result_volume < min_volume:
                min_volume = current_result_volume
            if current_result_volume > max_volume:
                max_volume = current_result_volume
            rolling_low += current_result_lowest_price
            rolling_high += current_result_highest_price
    final_avg_low = rolling_low / len(result_list)
    final_avg_high = rolling_high / len(result_list)
    avg_stock = (final_avg_low + final_avg_high) / 2

    report_data = ReportData(avg_stock=avg_stock, min_stock=min_stock, max_stock=max_stock,
                             min_volume=min_volume, max_volume=max_volume)
    return report_data
