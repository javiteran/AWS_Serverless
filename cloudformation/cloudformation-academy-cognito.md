# Autenticación con AWS Cognito

Documentación de la variante de la solución que añade gestión de usuarios mediante **AWS Cognito**.
Plantilla: `cloudformation/cloudformation-academy-cognito.yaml`

---

## Arquitectura

```
Usuario
  │
  ▼
login.html  ──►  Cognito Hosted UI  (registro / login)
                        │
                        │  redirige con id_token en la URL
                        ▼
              indexTabla.html / altavehiculo.html
                        │
                        │  Authorization: <id_token>
                        ▼
              API Gateway  ──►  CognitoAuthorizer (valida JWT)
                        │
                        ▼
                  Lambda  ──►  DynamoDB
```

---

## Recursos AWS que crea la plantilla

| Recurso | Tipo AWS | Descripción |
|---------|----------|-------------|
| `UserPool` | `AWS::Cognito::UserPool` | Almacena los usuarios. Login por email con verificación automática |
| `UserPoolClient` | `AWS::Cognito::UserPoolClient` | Cliente público para SPA. Flujo `implicit`, tokens con validez de 1 hora |
| `UserPoolDomain` | `AWS::Cognito::UserPoolDomain` | Activa la Hosted UI de Cognito (login/registro gestionado por AWS) |
| `CognitoAuthorizer` | `AWS::ApiGateway::Authorizer` | Valida el JWT en el header `Authorization` antes de invocar la Lambda |
| `VehiculosTable` | `AWS::DynamoDB::Table` | Tabla con PK `record_type` + SK `id` |
| `VehiculosLambda` | `AWS::Lambda::Function` | API REST Python 3.12. Lee el email del usuario autenticado desde el contexto |
| `VehiculosApi` | `AWS::ApiGateway::RestApi` | API REST. GET/POST/PUT protegidos. OPTIONS libre (preflight CORS) |
| `ApiStage` | `AWS::ApiGateway::Stage` | Stage configurable (`v1` por defecto) |
| `WebsiteBucket` | `AWS::S3::Bucket` | Hosting web estático. Página de error: `login.html` |
| `WebsiteBucketPolicy` | `AWS::S3::BucketPolicy` | Acceso público de lectura |
| `LambdaLogGroup` | `AWS::Logs::LogGroup` | CloudWatch Logs con retención de 7 días |
| `S3UploaderLambda` | `AWS::Lambda::Function` | Lambda auxiliar que sube los HTML al bucket durante el despliegue |
| `UploadWebFiles` | `Custom::S3Upload` | Custom Resource que invoca `S3UploaderLambda` con los HTML y parámetros Cognito inyectados |

---

## Archivos web generados automáticamente

La plantilla sube estos 5 archivos al bucket S3 durante el despliegue, con todos los parámetros (URL de la API, Client ID, dominio Cognito) ya inyectados mediante `!Sub`:

| Archivo | Descripción |
|---------|-------------|
| `login.html` | Página de bienvenida. Redirige a la Hosted UI de Cognito al hacer clic |
| `auth.js` | Módulo compartido de autenticación. Gestiona tokens, sesión y logout |
| `index.html` | Probador de API. Protegido: redirige a login si no hay sesión activa |
| `indexTabla.html` | Panel de vehículos con tabla. Protegido. Muestra el email del usuario en la navbar |
| `altavehiculo.html` | Formulario de alta (POST). Protegido. Incluye el token en cada petición |

---

## Flujo de autenticación

```
1. Usuario visita cualquier página protegida
2. auth.js llama a AUTH.requireAuth()
3. Si no hay token válido → redirige a login.html
4. login.html redirige a la Hosted UI de Cognito
5. Usuario se registra o inicia sesión
6. Cognito redirige a indexTabla.html con el token en el hash de la URL
7. auth.js guarda el token en sessionStorage
8. Todas las llamadas a la API incluyen: Authorization: <id_token>
9. API Gateway valida el token con CognitoAuthorizer
10. Si el token es válido → invoca la Lambda
11. La Lambda lee el email del usuario desde el contexto del authorizer
```

---

## Diferencias respecto a la versión sin Cognito

| Aspecto | `cloudformation-academy.yaml` | `cloudformation-academy-cognito.yaml` |
|---------|-------------------------------|---------------------------------------|
| Autenticación | Ninguna (API pública) | Cognito User Pool + Hosted UI |
| Endpoints protegidos | No | GET, POST, PUT `/vehiculos` |
| Header requerido | No | `Authorization: <id_token>` |
| Página de login | No existe | `login.html` con Hosted UI |
| Módulo de auth | No existe | `auth.js` compartido por todos los HTML |
| Datos de auditoría | No | `createdBy` y `updatedBy` con email del usuario |
| Página de error S3 | `index.html` | `login.html` |
| Archivos subidos al S3 | 3 HTML | 4 HTML + 1 JS |

---

## Parámetros de la plantilla

| Parámetro | Valor por defecto | Descripción |
|-----------|-------------------|-------------|
| `ProjectName` | `mis-vehiculos` | Prefijo usado en todos los recursos |
| `StageName` | `v1` | Stage de API Gateway (`v1`, `v2`, `prod`, `dev`) |
| `DynamoDBBillingMode` | `PAY_PER_REQUEST` | Modo de facturación de DynamoDB |
| `LabRoleName` | `LabRole` | Nombre del rol IAM de AWS Academy |

---

## Despliegue

```bash
aws cloudformation deploy \
  --template-file cloudformation/cloudformation-academy-cognito.yaml \
  --stack-name mis-vehiculos-cognito \
  --parameter-overrides ProjectName=mis-vehiculos StageName=v1 \
  --region us-east-1
```

> Sin `--capabilities CAPABILITY_NAMED_IAM` — la plantilla no crea roles IAM propios.

---

## Outputs del stack

| Output | Descripción |
|--------|-------------|
| `ApiUrl` | URL base de la API REST |
| `ApiVehiculosUrl` | Endpoint `/vehiculos` (requiere token en `Authorization`) |
| `CognitoUserPoolId` | ID del User Pool |
| `CognitoClientId` | ID del User Pool Client |
| `CognitoHostedUiUrl` | URL base de la Hosted UI de Cognito |
| `WebsiteLoginUrl` | URL de `login.html` — punto de entrada de la aplicación |
| `WebsiteUrl` | URL de `indexTabla.html` |
| `WebsiteUrlAltaVehiculo` | URL de `altavehiculo.html` |
| `DynamoDBTableName` | Nombre de la tabla DynamoDB |
| `LambdaFunctionName` | Nombre de la función Lambda |
| `WebsiteBucketName` | Nombre del bucket S3 |
| `LabRoleUsed` | ARN del LabRole utilizado |

---

## Política de contraseñas configurada

| Requisito | Valor |
|-----------|-------|
| Longitud mínima | 8 caracteres |
| Mayúsculas | Requeridas |
| Minúsculas | Requeridas |
| Números | Requeridos |
| Símbolos | No requeridos |

Se puede modificar en el recurso `UserPool > Policies > PasswordPolicy` de la plantilla.

---

## Eliminar todos los recursos

```bash
# Vaciar el bucket S3 primero
aws s3 rm s3://mis-vehiculos-web-TU_ACCOUNT_ID --recursive

# Eliminar el stack (borra Cognito, Lambda, DynamoDB, API Gateway, S3, etc.)
aws cloudformation delete-stack \
  --stack-name mis-vehiculos-cognito \
  --region us-east-1
```

> Al eliminar el stack se borra el User Pool y **todos los usuarios registrados se pierden**.

---

## Notas sobre AWS Academy

- El dominio de Cognito se construye como `{ProjectName}-{AccountId}` para garantizar unicidad sin crear recursos IAM.
- La Hosted UI usa HTTPS por defecto. Las URLs de callback del bucket S3 usan HTTP (limitación del hosting estático de S3 sin CloudFront).
- Si necesitas HTTPS en la web, añade una distribución CloudFront delante del bucket S3 y actualiza las `CallbackURLs` del `UserPoolClient`.
