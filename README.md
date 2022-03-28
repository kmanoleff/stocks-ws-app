# Stocks WebSocket App

AWS serverless microservice to retrieve stock information

# Infrastructure
Application uses [SAM](https://aws.amazon.com/serverless/sam/) to build and deploy the serverless application

Lambda function code written in [Python](https://www.python.org/downloads/).

**StocksWebSocket**
- Builds a resource of type `AWS::ApiGatewayV2::Api`
- Defines the protocol as WEBSOCKET and uses the `action` field of the request body for route selection
- Defines 3 `AWS::ApiGatewayV2::Route`s : `ConnectRoute` , `DisconnectRoute` , and `SendRoute`

**OnConnectFunction**
- `AWS::Serverless::Function` that is invoked on the `ConnectRoute` for establishing the WebSocket connection
- Function handler is defined in `onconnect/handler.lambda_handler`

**OnDisconnectFunction**
- `AWS::Serverless::Function` that is invoked on the `DisconnectRoute` for disconnecting the WebSocket connection
- Function handler is defined in `ondisconnect/handler.lambda_handler`

**SendMessageFunction**
- `AWS::Serverless::Function` that is invoked on the `SendRoute` for sending and receiving messages on the established 
WebSocket connection
- Function handler is defined in `sendmessage/handler.lambda_handler`
- The `RouteKey` `stocksaction` of the incoming message routes to this Lambda function
- Example 
```
{
    "action": "stocksaction",
    "ticker": "MSFT"
}
```
- The `ticker` field is a required field for the company to return the stocks data for
- The Lambda function will then make an external API call to 
[Polygon IO API](https://polygon.io/stocks?gclid=CjwKCAjwloCSBhAeEiwA3hVo_SiRY1dM645fBntGSOrsm8XkVLFUiCrSo0D1OpgzhOa_SPex-CNx7hoCFAAQAvD_BwE)
to retrieve the stock data
- The `create_report` function will iterate through the list of stocks results and generate a report with the following schema
```
"reportData": {
    "avgStock": float,
    "minStock": float,
    "maxStock": float,
    "minVolume": float,
    "maxVolume": float
}
```

- The function code includes a line of code `time.sleep(31)` to emulate a long running task which
would take longer than the API Gateway limit

# Testing
This application is hosted on my personal AWS account.  You can test this function with [Postman](https://www.postman.com) :

- Fire up Postman and Select New > WebSocket Request
- In the upper left of the request tab, select Raw for a raw WebSocket request
- Plug in the server URL that's hosted on my AWS - `wss://snouvi2jd3.execute-api.us-east-1.amazonaws.com/Prod`
- Paste the following in Compose Message.  This will retrieve the stocks for Microsoft (MSFT) :
```
{
    "action": "stocksaction",
    "ticker": "MSFT"
}
```
- Click Connect.  You should see a message saying you are connected to the WebSocket.
- Click Send.  First you should see a message that your message was accepted with status code `202`
- After about 30 seconds (the sleep timer mentioned above to emulate a long-running task), you should
see a message with the stock data returned from the external API.
- After response is posted back to the client the backend will disconnect the WebSocket connection

# SAM Deploy
Can be deployed to your own AWS account with SAM CLI using

`sam build`

`sam deploy`
