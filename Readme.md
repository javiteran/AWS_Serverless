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


---

## Despliegue con AWS CloudFormation

Se incluye una plantilla `cloudformation.yaml` que despliega **toda la solución de forma automática** con un solo comando.

### Recursos que crea la plantilla

| Recurso | Tipo AWS | Descripción |
|---------|----------|-------------|
| `VehiculosTable` | `AWS::DynamoDB::Table` | Tabla con PK `record_type` + SK `id`. Point-in-Time Recovery activado |
| `LambdaExecutionRole` | `AWS::IAM::Role` | Rol con permisos mínimos: CloudWatch Logs + DynamoDB CRUD |
| `VehiculosLambda` | `AWS::Lambda::Function` | Python 3.12 con el código de `lambda_API_REST_Vehiculos.py` |
| `VehiculosApi` | `AWS::ApiGateway::RestApi` | API REST con endpoints `GET /`, `GET/POST/PUT /vehiculos` |
| `VehiculosOptionsMethod` | `AWS::ApiGateway::Method` | CORS Preflight (OPTIONS) en `/vehiculos` con mock integration |
| `ApiStage` | `AWS::ApiGateway::Stage` | Stage configurable (`v1` por defecto) con métricas CloudWatch |
| `LambdaApiGatewayPermission` | `AWS::Lambda::Permission` | Permiso para que API Gateway invoque la Lambda |
| `WebsiteBucket` | `AWS::S3::Bucket` | Hosting web estático con `indexTabla.html` como página principal |
| `WebsiteBucketPolicy` | `AWS::S3::BucketPolicy` | Política pública de lectura para el bucket |
| `LambdaLogGroup` | `AWS::Logs::LogGroup` | CloudWatch Log Group con retención de 30 días |

### Parámetros de la plantilla

| Parámetro | Valor por defecto | Descripción |
|-----------|-------------------|-------------|
| `ProjectName` | `mis-vehiculos` | Prefijo usado en el nombre de todos los recursos |
| `StageName` | `v1` | Nombre del stage de API Gateway (`v1`, `v2`, `prod`, `dev`) |
| `DynamoDBBillingMode` | `PAY_PER_REQUEST` | Modo de facturación de DynamoDB |

### Despliegue con el script automatizado

El archivo `deploy.sh` automatiza todo el proceso: valida la plantilla, despliega el stack, obtiene las URLs, actualiza la URL de la API en los HTML y sube los archivos al bucket S3.

```bash
# Despliegue básico (región us-east-1, stage v1)
./deploy.sh

# Con parámetros personalizados: [REGION] [PROJECT_NAME] [STAGE]
./deploy.sh eu-west-1 mis-vehiculos prod
```

### Despliegue manual con AWS CLI

```bash
# 1. Validar la plantilla
aws cloudformation validate-template \
  --template-body file://cloudformation.yaml \
  --region us-east-1

# 2. Desplegar el stack
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name mis-vehiculos-stack \
  --parameter-overrides ProjectName=mis-vehiculos StageName=v1 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# 3. Obtener las URLs generadas
aws cloudformation describe-stacks \
  --stack-name mis-vehiculos-stack \
  --region us-east-1 \
  --query "Stacks[0].Outputs"

# 4. Subir los archivos HTML al bucket S3 (sustituye TU_BUCKET por el nombre real)
aws s3 cp index.html s3://TU_BUCKET/index.html --content-type "text/html"
aws s3 cp indexTabla.html s3://TU_BUCKET/indexTabla.html --content-type "text/html"
```

### Outputs del stack

Una vez desplegado, el stack expone estos valores:

| Output | Descripción |
|--------|-------------|
| `ApiUrl` | URL base de la API REST |
| `ApiVehiculosUrl` | Endpoint `/vehiculos` listo para usar |
| `DynamoDBTableName` | Nombre de la tabla DynamoDB creada |
| `LambdaFunctionName` | Nombre de la función Lambda |
| `WebsiteBucketName` | Nombre del bucket S3 |
| `WebsiteUrl` | URL pública del sitio web estático |
| `WebsiteUrlTabla` | URL directa a `indexTabla.html` |

### Eliminar todos los recursos

Cuando ya no necesites la solución, elimina el stack y vacía el bucket antes:

```bash
# Vaciar el bucket S3 primero (obligatorio antes de borrar el stack)
aws s3 rm s3://mis-vehiculos-web-TU_ACCOUNT_ID --recursive

# Eliminar el stack completo (borra Lambda, DynamoDB, API Gateway, IAM Role, etc.)
aws cloudformation delete-stack \
  --stack-name mis-vehiculos-stack \
  --region us-east-1
```

### Archivos del proyecto

```
AWS_Serverless/
├── cloudformation.yaml          # Plantilla CloudFormation (infraestructura completa)
├── deploy.sh                    # Script de despliegue automatizado
├── lambda_API_REST_Vehiculos.py # Código fuente de la función Lambda (con CORS)
├── lambda_API_REST.py           # Versión original de la Lambda (sin CORS)
├── index.html                   # Página web de prueba básica
├── indexTabla.html              # Panel de gestión de vehículos (tabla)
└── doc/                         # Documentación y diagramas de arquitectura
```


---

## Despliegue en AWS Academy (cloudformation-academy.yaml)

AWS Academy restringe la creación y modificación de recursos IAM. La plantilla `cloudformation-academy.yaml` está adaptada para funcionar dentro de esas restricciones.

### Diferencias respecto a la plantilla estándar

| Aspecto | `cloudformation.yaml` | `cloudformation-academy.yaml` |
|---------|----------------------|-------------------------------|
| Rol IAM | Crea `LambdaExecutionRole` con permisos mínimos | **No crea ningún rol IAM** |
| Rol de la Lambda | `!GetAtt LambdaExecutionRole.Arn` | `!Sub "arn:aws:iam::${AWS::AccountId}:role/${LabRoleName}"` |
| `CAPABILITY_NAMED_IAM` | Necesario | **No necesario** |
| Logs en API Gateway | `MethodSettings` con `LoggingLevel: INFO` | Eliminado (requiere rol de cuenta IAM) |
| Point-in-Time Recovery | Activado en DynamoDB | Eliminado (puede fallar en algunas cuentas Academy) |
| Exports en Outputs | Sí (`Export: Name:`) | Eliminados (pueden colisionar entre laboratorios) |
| Retención de logs Lambda | 30 días | 7 días (los labs se reinician frecuentemente) |

### Despliegue en AWS Academy

El ARN del `LabRole` se construye automáticamente usando `${AWS::AccountId}`, por lo que **no necesitas buscarlo ni introducirlo manualmente**. El parámetro `LabRoleName` tiene el valor `LabRole` por defecto, que es el nombre estándar en todos los laboratorios de AWS Academy.

```bash
# Despliegue estándar, sin tocar parámetros IAM
aws cloudformation deploy \
  --template-file cloudformation-academy.yaml \
  --stack-name mis-vehiculos-academy \
  --parameter-overrides \
      ProjectName=mis-vehiculos \
      StageName=v1 \
  --region us-east-1
```

> **Sin `--capabilities CAPABILITY_NAMED_IAM`** porque esta plantilla no crea recursos IAM.

Si tu laboratorio usa un nombre de rol diferente a `LabRole`, pásalo como parámetro:

```bash
aws cloudformation deploy \
  --template-file cloudformation-academy.yaml \
  --stack-name mis-vehiculos-academy \
  --parameter-overrides \
      ProjectName=mis-vehiculos \
      StageName=v1 \
      LabRoleName=NombreDetuRol \
  --region us-east-1
```

### Subir los HTML al bucket S3 tras el despliegue

```bash
# Obtener el nombre del bucket creado
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name mis-vehiculos-academy \
  --query "Stacks[0].Outputs[?OutputKey=='WebsiteBucketName'].OutputValue" \
  --output text)

# Obtener la URL de la API para actualizar los HTML
API_URL=$(aws cloudformation describe-stacks \
  --stack-name mis-vehiculos-academy \
  --query "Stacks[0].Outputs[?OutputKey=='ApiVehiculosUrl'].OutputValue" \
  --output text)

echo "Bucket: $BUCKET"
echo "API:    $API_URL"

# Subir los archivos HTML (actualiza la URL de la API antes si es necesario)
aws s3 cp index.html s3://$BUCKET/index.html --content-type "text/html"
aws s3 cp indexTabla.html s3://$BUCKET/indexTabla.html --content-type "text/html"
```

### Eliminar el stack en AWS Academy

```bash
# Vaciar el bucket primero (S3 no permite borrar buckets con contenido)
aws s3 rm s3://mis-vehiculos-web-ACCOUNT_ID --recursive

# Eliminar el stack
aws cloudformation delete-stack \
  --stack-name mis-vehiculos-academy \
  --region us-east-1
```
