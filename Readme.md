# Proyecto AWS Academy: API Gateway + Lambda + DynamoDB

## Video de youtube

Prueba de creación de una función lambda en python que introduzca datos en una base datos NoSQL DynamoDB y que sea publica utilizando AWS API Gateway mediante una API Rest.

Al final lo probaremos con una página web simple habilitando CORS para ello. Debería publicarse ese index.html finalmente en un bucket de S3 con la URL a ese archivo pública.
[https://youtu.be/Z1Av9KAjx88](https://youtu.be/Z1Av9KAjx88)

## Pasos

* Crear una función Lambda en Python.
* Crear una tabla DynamoDB para almacenar los datos de los vehículos.
* Configurar la función Lambda para interactuar con DynamoDB.
* Crear un API REST en API Gateway y conectar la función Lambda a las rutas correspondientes.
* Habilitar CORS en API Gateway para permitir solicitudes desde la página web.
* Probar la API utilizando herramientas como Postman o Curl.
* Crear una página web simple que consuma la API REST para mostrar y gestionar los vehículos.
* Publicar la página web en un bucket de S3 y asegurarse de que sea accesible públicamente. (No está en el vídeo).
* Ver los logs de la función Lambda en CloudWatch para depuración y monitoreo.
* Opcional: Añadir autenticación a la API REST utilizando AWS IAM o Amazon Cognito para mayor seguridad.

## CORS

Hay que habilitar CORS en el API Gateway para que la página web pueda hacer peticiones a la API sin problemas de seguridad desde otros orígenes que no sean la propia API.

## Función Lambda para CORS

```python
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
```

## Test desde la página de lambda

```json
#Test Event: Crear vehiculo
{
    "httpMethod": "POST",
    "path": "/vehiculos",
    "body": "{\"tipo\":\"Scooter\",\"disponible\":\"True\",\"matricula\":\"ABC-123\",\"combustible\":\"Gasolina\"}"
}
#Test Event: Crear vehiculo
{
    "httpMethod": "POST",
    "path": "/vehiculos",
    "body": "{\"tipo\":\"Coche\",\"disponible\":\"True\",\"matricula\":\"AFC-333\",\"combustible\":\"Eléctrico\"}"
}


#Test Event: Actualizar vehiculo
{
    "httpMethod": "PUT",
    "path": "/vehiculos",
    "body": "{\"id\":\"REPLACE_WITH_vehiculo_ID\",\"disponible\":\"False\"}"
}

#Test Event: Listar vehiculos
{
    "httpMethod": "GET",
    "path": "/vehiculos"
}

```

## Pruebas con Curl. (/vehiculos). Se pueden hacere desde AWS CloudShell o desde tu terminal local linux (si tienes instalado curl)

### Listar todos los vehículos (GET)

```Bash
curl -X GET https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/vehiculos

```

### Crear un nuevo vehículo (POST)

```Bash
curl -X POST https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/vehiculos \
     -H "Content-Type: application/json" \
     -d '{"tipo": "Scooter", "modelo": "X-200", "available": "True"}'

curl -X POST https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/vehiculos \
     -H "Content-Type: application/json" \
     -d '{"tipo": "Avion", "modelo": "X-200", "available": "True", "matricula": "XYZ-789", "combustible": "Jet Fuel"}'
```

### Actualizar un vehículo (PUT)

Nota: Debes usar un id que ya exista en tu base de datos dynamodb.

```Bash
curl -X PUT https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/vehiculos \
     -H "Content-Type: application/json" \
     -d '{"id": "REPLAZA_CON_ID", "available": "False", "nota": "En mantenimiento"}'

curl -X PUT https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/vehiculos \
     -H "Content-Type: application/json" \
     -d '{"id": "33c79a34-c", "available": "False", "nota": "En mantenimiento", "modelo": "Cestna 172"}'
     
```

## 2. Se podría modificar la función lambda para añadir ---> Localización (/localizacion) o cualquier otra cosa

### Listar todas las localizaciones (GET)

```Bash
curl -X GET https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/localizacion
```

### Crear una nueva localización (POST)

```Bash
curl -X POST https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/localizacion \
     -H "Content-Type: application/json" \
     -d '{"Nombre": "Entrada Principal", "vehiculos_disponibles": "5"}'
```

### Actualizar una localización (PUT)

```Bash
curl -X PUT https://TU_API_ID.execute-api.REGION.amazonaws.com/v1/localizacion \
     -H "Content-Type: application/json" \
     -d '{"id": "REPLAZA_CON_ID", "vehiculos_disponibles": "2"}'
```

## MIRAR CLOUDWATCH PARA VER LOS LOGS DE LAS FUNCIONES LAMBDA

Log management: AWS CloudWatch Logs

/aws/lambda/MisVehiculos

## Presentación en Google NotebookLM

[Serverless CRUD API Con AWS Lambda y DynamoDB en NotebookLM](https://notebooklm.google.com/notebook/30003c98-3907-462b-a05e-bdfdcec3afe9/artifact/d1033aa9-e3b5-4905-a045-f92e22659369?utm_source=nlm_web_share&utm_medium=google_oo&utm_campaign=art_share_1&utm_content=&utm_smc=nlm_web_share_google_oo_art_share_1_)