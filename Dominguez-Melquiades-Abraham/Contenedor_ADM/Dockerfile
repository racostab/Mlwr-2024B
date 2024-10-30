# Usar una imagen base de Ubuntu
FROM ubuntu:20.04

# Evitar interacciones durante la instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar e instalar bash, SSH y otras herramientas básicas
RUN apt-get update && apt-get install -y \
    bash \
    #openssh-server -> esto es opcional, es una forma de aministración
    openssh-server \
    build-essential \
    wget \
    curl \
    git \
    nano \
    python3 \
    python3-pip \
    unzip \
    passwd

# Instalar herramientas específicas para análisis de malware estático, incluyendo strings, file y exiftool
RUN apt-get install -y \
    binwalk \
    radare2 \
    strace \
    binutils \
    file \
    exiftool

# Copiar los scripts al contenedor
COPY Scripts/analizar_r2.sh /usr/local/bin/analizar_r2.sh
COPY Scripts/analizar_malware.sh /usr/local/bin/analizar_malware.sh
COPY Scripts/generar_hashes.sh /usr/local/bin/generar_hashes.sh

# Dar permisos de ejecución a los scripts
RUN chmod +x /usr/local/bin/analizar_r2.sh /usr/local/bin/analizar_malware.sh /usr/local/bin/generar_hashes.sh

# Configurar SSH (opcional)
RUN mkdir /var/run/sshd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Crear el usuario analista y configurar la contraseña (opcional para SSH)
RUN useradd -m -s /bin/bash analista
RUN echo "analista:analista" | chpasswd

# Exponer el puerto SSH (opcional para SSH)
EXPOSE 22

# Comando por defecto para iniciar SSH y abrir bash (bash no es opcional)
CMD service ssh start && /bin/bash
