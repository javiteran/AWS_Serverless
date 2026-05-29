# AWS SDK for Python (Boto3) - https://aws.amazon.com/sdk-for-python/
# This Lambda function serves as a REST API for managing vehicles and their locations.

### EN ESTA NO ESTA HABILITADO CORS, SI SE REQUIERE HABILITARLO SE DEBE AGREGAR LOS HEADERS CORRESPONDIENTES EN LAS RESPUESTAS
import json
import os
import boto3
import uuid
from datetime import datetime

# Initialize DynamoDB client
# Boto3 - DynamoDB - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    """
    Lambda handler for processing API Gateway requests
    """
    http_method = event['httpMethod']
    path = event['path']
    
    # Route the request based on path and method
    if path == '/vehiculos':
        if http_method == 'GET':
            return listar_vehiculos()
        elif http_method == 'POST':
            return crear_vehiculo(json.loads(event['body']) if 'body' in event else {})
        elif http_method == 'PUT':
            return actualiza_vehiculo(json.loads(event['body']) if 'body' in event else {})
    elif path == '/localizacion':
        if http_method == 'GET':
            return listar_localizacion()
        elif http_method == 'POST':
            return crear_localizacion(json.loads(event['body']) if 'body' in event else {})
        elif http_method == 'PUT':
            return actualiza_localizacion(json.loads(event['body']) if 'body' in event else {})
    elif path == '/':
        if http_method == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Mis Vehiculos'})
    }

    # Default response for unhandled routes
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not Found'})
    }

# vehiculo handlers
def crear_vehiculo(data):
    if not data:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing request body'})
        }
    
    item = {
        'id': str(uuid.uuid4())[:10],
        'record_type': 'vehiculo',
        'createdAt': datetime.now().isoformat(),
        **data
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'body': json.dumps(item)
    }

def actualiza_vehiculo(data):
    if not data or 'id' not in data:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing id in request body'})
        }
    
    item_id = data['id']
    actualiza_expression = 'SET updatedAt = :updatedAt'
    expression_values = {
        ':updatedAt': datetime.now().isoformat()
    }
    
    # Build update expression dynamically
    for key, value in data.items():
        if key != 'id':
            actualiza_expression += f', {key} = :{key}'
            expression_values[f':{key}'] = value
    
    table.update_item(
        Key={
            'id': item_id,
            'record_type': 'vehiculo'
        },
        UpdateExpression=actualiza_expression,
        ExpressionAttributeValues=expression_values,
        ReturnValues='ALL_NEW'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'id': item_id, 'message': 'vehiculo updated successfully'})
    }

def listar_vehiculos():
    response = table.query(
        KeyConditionExpression='record_type = :record_type_val',
        ExpressionAttributeValues={':record_type_val': 'vehiculo'}
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(response.get('Items', []))
    }

# localizacion handlers
def crear_localizacion(data):
    if not data:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing request body'})
        }
    
    item = {
        'id': str(uuid.uuid4())[:10],
        'record_type': 'localizacion',
        'createdAt': datetime.now().isoformat(),
        **data
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'body': json.dumps(item)
    }

def actualiza_localizacion(data):
    if not data or 'id' not in data:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing id in request body'})
        }
    
    item_id = data['id']
    actualiza_expression = 'SET updatedAt = :updatedAt'
    expression_values = {
        ':updatedAt': datetime.now().isoformat()
    }
    
    # Build update expression dynamically
    for key, value in data.items():
        if key != 'id':
            actualiza_expression += f', {key} = :{key}'
            expression_values[f':{key}'] = value
    
    table.update_item(
        Key={
            'id': item_id,
            'record_type': 'localizacion'
        },
        UpdateExpression=actualiza_expression,
        ExpressionAttributeValues=expression_values,
        ReturnValues='ALL_NEW'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'id': item_id, 'message': 'localizacion updated successfully'})
    }

def listar_localizacion():
    response = table.query(
        KeyConditionExpression='record_type = :record_type_val',
        ExpressionAttributeValues={':record_type_val': 'localizacion'}
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(response.get('Items', []))
    }

'''
Test Event: Create localizacion
{
    "httpMethod": "POST",
    "path": "/localizacion",
    "body": "{\"Nombre\":\"Visitor entrance\",\"vehiculos_disponibles\":\"3\"}"
}

Test Event: Create vehiculo
{
    "httpMethod": "POST",
    "path": "/vehiculos",
    "body": "{\"tipo\":\"Scooter\",\"disponible\":\"True\"}"
}

Test Event: Update localizacion
{
    "httpMethod": "PUT",
    "path": "/localizacion",
    "body": "{\"id\":\"REPLACE_WITH_localizacion_ID\",\"vehiculos_disponibles\":\"2\"}"
}

Test Event: Update vehiculo
{
    "httpMethod": "PUT",
    "path": "/vehiculos",
    "body": "{\"id\":\"REPLACE_WITH_vehiculo_ID\",\"disponible\":\"False\"}"
}
'''