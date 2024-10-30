#!/bin/bash

# Verificar si se proporciona el archivo como argumento
if [ -z "$1" ]; then
  echo "Uso: $0 archivo_para_analizar"
  exit 1
fi

archivo="$1"

# Verificar si el archivo existe
if [ ! -f "$archivo" ]; then
  echo "El archivo '$archivo' no existe."
  exit 1
fi

# Nombre de archivo de salida
output_file="analisis_$(basename "$archivo" .${archivo##*.}).txt"

echo "Ejecutando análisis con Radare2 (r2) en el archivo: $archivo"
echo "Resultado se guardará en: $output_file"

# Ejecutar Radare2 con opción 'aaa' y guardar la salida en el archivo de texto
r2 -A "$archivo" -c "aaa; afl; pdf" > "$output_file"

echo "Análisis completado. Los resultados están en '$output_file'"
