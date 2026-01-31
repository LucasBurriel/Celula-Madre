#!/bin/bash
# TEMPLATE DE VALIDACIÓN AUTOMÁTICA - Proyecto Python
# Este archivo es un EJEMPLO GENÉRICO que debe copiarse a tools/validate.sh
# durante create-plan y puede personalizarse según necesidades del proyecto.
#
# Uso durante create-plan:
#   cp examples/validation-templates/python-validation.sh tools/validate.sh
#   chmod +x tools/validate.sh
#
# Herramientas validadas (instalar si no existen):
#   - pylint/flake8 (linting)
#   - mypy (type checking)
#   - pytest (tests + coverage)
#   - bandit (security)
#   - radon (complexity)
#
# Personalización: Editar umbrales, agregar/quitar herramientas según proyecto

set -e  # Detener si algún comando falla

echo "======================================"
echo "🔍 VALIDACIÓN AUTOMÁTICA - PYTHON"
echo "======================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Función para reportar resultado
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

# Función para warnings
report_warning() {
    local check_name=$1
    echo -e "${YELLOW}⚠️  WARN${NC} - $check_name"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

echo "📋 Paso 1: Verificar estructura del proyecto"
echo "--------------------------------------"

# Verificar que existen archivos/directorios necesarios
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    report_result "Archivo de dependencias existe" 0
else
    report_result "Archivo de dependencias existe" 1
    echo "   ℹ️  Se esperaba requirements.txt o pyproject.toml"
fi

if [ -d "tests" ] || [ -d "test" ]; then
    report_result "Directorio de tests existe" 0
else
    report_warning "No se encontró directorio 'tests/' - Tests unitarios pueden estar en otro lugar"
fi

echo ""
echo "🔬 Paso 2: Análisis estático (Linting)"
echo "--------------------------------------"

# Pylint (si está instalado)
if command -v pylint &> /dev/null; then
    echo "Ejecutando pylint..."
    if pylint --rcfile=.pylintrc . --fail-under=7.0 2>&1 | tee .validation-pylint.log; then
        report_result "Pylint (score ≥7.0)" 0
    else
        report_result "Pylint (score ≥7.0)" 1
        echo "   ℹ️  Ver .validation-pylint.log para detalles"
    fi
else
    report_warning "Pylint no instalado - Saltando"
fi

# Flake8 (alternativa más ligera)
if command -v flake8 &> /dev/null; then
    echo "Ejecutando flake8..."
    if flake8 . --max-line-length=100 --exclude=venv,__pycache__,.git 2>&1 | tee .validation-flake8.log; then
        report_result "Flake8 (PEP8 compliance)" 0
    else
        report_result "Flake8 (PEP8 compliance)" 1
        echo "   ℹ️  Ver .validation-flake8.log para detalles"
    fi
else
    report_warning "Flake8 no instalado - Saltando"
fi

echo ""
echo "🔍 Paso 3: Type Checking"
echo "--------------------------------------"

# MyPy (type checking)
if command -v mypy &> /dev/null; then
    echo "Ejecutando mypy..."
    if mypy . --ignore-missing-imports 2>&1 | tee .validation-mypy.log; then
        report_result "MyPy (type checking)" 0
    else
        report_result "MyPy (type checking)" 1
        echo "   ℹ️  Ver .validation-mypy.log para detalles"
    fi
else
    report_warning "MyPy no instalado - Saltando type checking"
fi

echo ""
echo "🧪 Paso 4: Tests Unitarios"
echo "--------------------------------------"

# Pytest
if command -v pytest &> /dev/null; then
    echo "Ejecutando pytest..."
    if pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-fail-under=70 2>&1 | tee .validation-pytest.log; then
        report_result "Pytest (tests + coverage ≥70%)" 0
    else
        report_result "Pytest (tests + coverage ≥70%)" 1
        echo "   ℹ️  Ver .validation-pytest.log para detalles"
    fi
else
    report_warning "Pytest no instalado - Saltando tests"
fi

echo ""
echo "🔒 Paso 5: Security Checks"
echo "--------------------------------------"

# Bandit (security linter)
if command -v bandit &> /dev/null; then
    echo "Ejecutando bandit (security)..."
    if bandit -r . -ll -f txt 2>&1 | tee .validation-bandit.log; then
        report_result "Bandit (security issues)" 0
    else
        report_result "Bandit (security issues)" 1
        echo "   ℹ️  Ver .validation-bandit.log para detalles"
    fi
else
    report_warning "Bandit no instalado - Saltando security check"
fi

echo ""
echo "📊 Paso 6: Code Complexity"
echo "--------------------------------------"

# Radon (complexity analysis)
if command -v radon &> /dev/null; then
    echo "Analizando complejidad ciclomática..."
    # Radon CC - Complejidad ciclomática (A=mejor, F=peor)
    # Reportar archivos con complejidad > B (moderate)
    radon cc . -a -nb --min B | tee .validation-radon.log

    # Contar líneas con alta complejidad
    HIGH_COMPLEXITY=$(radon cc . -a -nb --min B | grep -c "^[[:space:]]*[A-Z]" || true)

    if [ "$HIGH_COMPLEXITY" -eq 0 ]; then
        report_result "Radon (complexity ≤ moderate)" 0
    else
        report_warning "Radon encontró $HIGH_COMPLEXITY funciones con complejidad >moderate"
        echo "   ℹ️  Ver .validation-radon.log para detalles"
    fi
else
    report_warning "Radon no instalado - Saltando análisis de complejidad"
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
