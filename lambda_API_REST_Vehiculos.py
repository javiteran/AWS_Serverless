# AWS SDK for Python (Boto3) - https://aws.amazon.com/sdk-for-python/
# This Lambda function serves as a REST API for managing vehicles and their locations.
import json
import os
import boto3
import uuid
from datetime import datetime

# Inicializar cliente de DynamoDB
# Boto3 - DynamoDB - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

# CONFIGURACIÓN DE CABECERAS PARA CORS
HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
}

def lambda_handler(event, context):
    """
    Lambda handler for processing API Gateway requests
    Controlador Lambda para procesar solicitudes de API Gateway

    """
    # Manejar peticiones OPTIONS (Preflight) automáticas del navegador
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': HEADERS,
            'body': json.dumps('OK')
        }

    http_method = event['httpMethod']
    path = event['path']
    
    # Route the request based on path and method
    # Enrutar la solicitud en función de la ruta y el método
    # Ruta vehiculos
    if path == '/vehiculos':
        if http_method == 'GET':
            return listar_vehiculos()
        elif http_method == 'POST':
            return crear_vehiculo(json.loads(event['body']) if 'body' in event else {})
        elif http_method == 'PUT':
            return actualiza_vehiculo(json.loads(event['body']) if 'body' in event else {})
    # Ruta base
    elif path == '/':
        if http_method == 'GET':
            return {
                'statusCode': 200,
                'headers': HEADERS,
                'body': json.dumps({'message': 'Mis Vehiculos- Página principal'})
            }

    # Default response for unhandled routes
    # Respuesta predeterminada para rutas no gestionadas. (404 No encontrado)
    return {
        'statusCode': 404,
        'headers': HEADERS,
        'body': json.dumps({'error': 'Not Found'})
    }

# vehiculo handlers
# Controladores de vehiculo
# "record_type=vehiculo" se utiliza para diferenciar los vehiculos la tabla de DynamoDB
# Si hay más tipos de registros (por ejemplo, localizacion), se pueden diferenciar usando el campo "record_type"
def crear_vehiculo(data):
    ''' Crea un nuevo vehiculo en la tabla de DynamoDB. Requiere un cuerpo de solicitud con los datos del vehiculo.
        * el id se genera automáticamente utilizando uuid4 y se trunca a los primeros 10 caracteres para mayor legibilidad.
        * el campo "createdAt" se establece con la fecha y hora actual en formato ISO 8601.
        * el record_type se establece como "vehiculo" para diferenciarlo de otros tipos de registros en la tabla.
        * el resto de los campos se agregan dinámicamente al item utilizando el operador de desempaquetado **data.
    '''
    if not data:
        return {
            'statusCode': 400,
            'headers': HEADERS,
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
        'headers': HEADERS,
        'body': json.dumps(item)
    }


def actualiza_vehiculo(data):
    ''' Actualiza un vehiculo existente en la tabla de DynamoDB. Requiere el campo "id" en el cuerpo de la solicitud.'''
    if not data or 'id' not in data:
        return {
            'statusCode': 400,
            'headers': HEADERS,
            'body': json.dumps({'error': 'Missing id in request body'})
        }
    
    item_id = data['id']
    actualiza_expression = 'SET updatedAt = :updatedAt'
    expression_values = {
        ':updatedAt': datetime.now().isoformat()
    }
    
    # Build update expression dynamically
    # Construir la expresión de actualización dinámicamente para incluir solo los campos que se están actualizando (excluyendo "id")
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
        'headers': HEADERS,
        'body': json.dumps({'id': item_id, 'message': 'vehiculo updated successfully'})
    }

def listar_vehiculos():
    ''' Lista todos los vehiculos en la tabla de DynamoDB. Filtra por "record_type=vehiculo" para obtener solo los registros de vehiculos.'''
    response = table.query(
        KeyConditionExpression='record_type = :record_type_val',
        ExpressionAttributeValues={':record_type_val': 'vehiculo'}
    )
    
    return {
        'statusCode': 200,
        'headers': HEADERS,
        'body': json.dumps(response.get('Items', []))
    }


'''
Test Event: Crear vehiculo
{
    "httpMethod": "POST",
    "path": "/vehiculos",
    "body": "{\"tipo\":\"Scooter\",\"disponible\":\"True\",\"matricula\":\"ABC-123\",\"combustible\":\"Gasolina\"}"
}
Test Event: Crear vehiculo
{
    "httpMethod": "POST",
    "path": "/vehiculos",
    "body": "{\"tipo\":\"Coche\",\"disponible\":\"True\",\"matricula\":\"AFC-333\",\"combustible\":\"Eléctrico\"}"
}


Test Event: Actualizar vehiculo
{
    "httpMethod": "PUT",
    "path": "/vehiculos",
    "body": "{\"id\":\"REPLACE_WITH_vehiculo_ID\",\"disponible\":\"False\"}"
}

Test Event: Listar vehiculos
{
    "httpMethod": "GET",
    "path": "/vehiculos"
}
'''