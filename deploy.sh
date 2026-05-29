#!/bin/bash
# =============================================================
# Script de despliegue de la solución Serverless en AWS
# Uso: ./deploy.sh [REGION] [PROJECT_NAME] [STAGE]
# Ejemplo: ./deploy.sh us-east-1 mis-vehiculos v1
# =============================================================

REGION=${1:-"us-east-1"}
PROJECT_NAME=${2:-"mis-vehiculos"}
STAGE=${3:-"v1"}
STACK_NAME="${PROJECT_NAME}-stack"

echo "=============================================="
echo " Desplegando: ${STACK_NAME}"
echo " Región:      ${REGION}"
echo " Stage:       ${STAGE}"
echo "=============================================="

# 1. Validar la plantilla CloudFormation
echo ""
echo "[1/4] Validando plantilla CloudFormation..."
aws cloudformation validate-template \
  --template-body file://cloudformation.yaml \
  --region "${REGION}"

if [ $? -ne 0 ]; then
  echo "ERROR: La plantilla no es válida. Revisa los errores anteriores."
  exit 1
fi
echo "  ✅ Plantilla válida."

# 2. Desplegar el stack
echo ""
echo "[2/4] Desplegando stack CloudFormation (puede tardar 2-3 minutos)..."
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides \
      ProjectName="${PROJECT_NAME}" \
      StageName="${STAGE}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${REGION}"

if [ $? -ne 0 ]; then
  echo "ERROR: El despliegue falló. Revisa los eventos del stack en la consola de AWS."
  exit 1
fi
echo "  ✅ Stack desplegado correctamente."

# 3. Obtener los outputs del stack
echo ""
echo "[3/4] Obteniendo URLs y nombres de recursos..."
API_URL=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiVehiculosUrl'].OutputValue" \
  --output text)

BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='WebsiteBucketName'].OutputValue" \
  --output text)

WEBSITE_URL=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='WebsiteUrl'].OutputValue" \
  --output text)

echo "  API URL:     ${API_URL}"
echo "  Bucket S3:   ${BUCKET_NAME}"
echo "  Website URL: ${WEBSITE_URL}"

# 4. Actualizar la URL de la API en los archivos HTML y subir al bucket S3
echo ""
echo "[4/4] Actualizando URL de la API en los HTML y subiendo a S3..."

# Reemplazar la URL hardcodeada en los HTML con la URL real del stack
sed "s|https://xjj1zk172j.execute-api.us-east-1.amazonaws.com/v[0-9]*/vehiculos|${API_URL}|g" \
  index.html > /tmp/index_deploy.html

sed "s|https://xjj1zk172j.execute-api.us-east-1.amazonaws.com/v[0-9]*/vehiculos|${API_URL}|g" \
  indexTabla.html > /tmp/indexTabla_deploy.html

# Subir los archivos HTML al bucket S3
aws s3 cp /tmp/index_deploy.html "s3://${BUCKET_NAME}/index.html" \
  --content-type "text/html" \
  --region "${REGION}"

aws s3 cp /tmp/indexTabla_deploy.html "s3://${BUCKET_NAME}/indexTabla.html" \
  --content-type "text/html" \
  --region "${REGION}"

echo "  ✅ Archivos HTML subidos al bucket S3."

# Limpiar temporales
rm -f /tmp/index_deploy.html /tmp/indexTabla_deploy.html

echo ""
echo "=============================================="
echo " ✅ DESPLIEGUE COMPLETADO"
echo "=============================================="
echo ""
echo " 🌐 Página web:    ${WEBSITE_URL}/indexTabla.html"
echo " 🔗 API vehiculos: ${API_URL}"
echo ""
echo " Prueba rápida con curl:"
echo "   curl -X GET ${API_URL}"
echo ""
echo " Para eliminar todos los recursos:"
echo "   aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}"
echo "   aws s3 rm s3://${BUCKET_NAME} --recursive"
echo "=============================================="
