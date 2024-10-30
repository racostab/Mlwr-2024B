#!/bin/bash

# Verificar si se proporciona el archivo como argumento
if [ -z "$1" ]; then
  echo "Uso: $0 <archivo>"
  exit 1
fi

archivo="$1"

# Verificar si el archivo existe
if [ ! -f "$archivo" ]; then
  echo "El archivo '$archivo' no existe."
  exit 1
fi

# Generar y mostrar los hashes
echo "Archivo: $archivo"
echo "MD5:    $(md5sum "$archivo" | awk '{print $1}')"
echo "SHA-1:  $(sha1sum "$archivo" | awk '{print $1}')"
echo "SHA-256: $(sha256sum "$archivo" | awk '{print $1}')"
