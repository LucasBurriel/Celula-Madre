#!/bin/bash
# TEMPLATE DE VALIDACIÓN AUTOMÁTICA - Proyecto Node.js/TypeScript
# Este archivo es un EJEMPLO GENÉRICO que debe copiarse a tools/validate.sh
# durante create-plan y puede personalizarse según necesidades del proyecto.
#
# Uso durante create-plan:
#   cp examples/validation-templates/nodejs-validation.sh tools/validate.sh
#   chmod +x tools/validate.sh
#
# Herramientas validadas:
#   - ESLint (linting)
#   - TypeScript (type checking, si aplica)
#   - Jest/Mocha/Vitest (tests)
#   - npm run build (build process)
#
# Personalización: Editar scripts en package.json según necesidades del proyecto

set -e

echo "======================================"
echo "🔍 VALIDACIÓN AUTOMÁTICA - NODE.JS"
echo "======================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

report_result() {
    local check_name=$1
    local exit_code=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC} - $check_name"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ FAIL${NC} - $check_name"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

report_warning() {
    local check_name=$1
    echo -e "${YELLOW}⚠️  WARN${NC} - $check_name"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

echo "📋 Paso 1: Verificar estructura"
echo "--------------------------------------"

if [ -f "package.json" ]; then
    report_result "package.json existe" 0
else
    report_result "package.json existe" 1
    exit 1
fi

if [ -d "node_modules" ]; then
    report_result "Dependencias instaladas" 0
else
    report_warning "node_modules no encontrado - Ejecutar 'npm install'"
fi

echo ""
echo "🔬 Paso 2: Linting (ESLint)"
echo "--------------------------------------"

if [ -f "node_modules/.bin/eslint" ] || command -v eslint &> /dev/null; then
    echo "Ejecutando ESLint..."
    if npm run lint 2>&1 | tee .validation-eslint.log; then
        report_result "ESLint" 0
    else
        report_result "ESLint" 1
    fi
else
    report_warning "ESLint no configurado"
fi

echo ""
echo "🔍 Paso 3: Type Checking (TypeScript)"
echo "--------------------------------------"

if [ -f "tsconfig.json" ]; then
    if [ -f "node_modules/.bin/tsc" ] || command -v tsc &> /dev/null; then
        echo "Ejecutando TypeScript compiler..."
        if npm run type-check 2>&1 | tee .validation-tsc.log; then
            report_result "TypeScript type check" 0
        else
            report_result "TypeScript type check" 1
        fi
    else
        report_warning "TypeScript no instalado"
    fi
else
    echo "No es proyecto TypeScript - Saltando type check"
fi

echo ""
echo "🧪 Paso 4: Tests (Jest/Mocha/Vitest)"
echo "--------------------------------------"

if npm run test 2>&1 | tee .validation-test.log; then
    report_result "Tests unitarios" 0
else
    report_result "Tests unitarios" 1
fi

echo ""
echo "🏗️  Paso 5: Build"
echo "--------------------------------------"

if npm run build 2>&1 | tee .validation-build.log; then
    report_result "Build process" 0
else
    report_result "Build process" 1
fi

echo ""
echo "======================================"
echo "📈 RESUMEN DE VALIDACIÓN"
echo "======================================"
echo ""
echo "Total de checks:    $TOTAL_CHECKS"
echo -e "${GREEN}Pasados:${NC}           $PASSED_CHECKS"
echo -e "${RED}Fallidos:${NC}          $FAILED_CHECKS"
echo -e "${YELLOW}Warnings:${NC}          $WARNING_CHECKS"
echo ""

# Calcular porcentaje de éxito
if [ $TOTAL_CHECKS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo "Tasa de éxito: $SUCCESS_RATE%"
    echo ""
fi

# Determinar status general
if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✅ VALIDACIÓN COMPLETA - SIN ERRORES${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  VALIDACIÓN COMPLETA - CON WARNINGS${NC}"
        echo "Revisar warnings antes de continuar"
        exit 0
    fi
else
    echo -e "${RED}❌ VALIDACIÓN FALLIDA${NC}"
    echo ""
    echo "Se encontraron $FAILED_CHECKS errores críticos."
    echo "Corregir antes de continuar con la implementación."
    echo ""
    echo "Logs de validación guardados en:"
    echo "  - .validation-*.log"
    exit 1
fi
