# Análisis de Malware
## Asignatura
Abraham Dominguez Melquiades
Boleta: B244548

Tipo de Alumno: Oyente

## Uso

Construcción del Laboratorio de Malware

Para contruir el docker usar el archivo Dockerfile, el cual contiene las configuraciones basicas de bash así como las herramientas de:
    -StringS
    -binwalk
    -radare2

Adicionalmente se tiene la opcion de aministracion por ssh en caso de ser necesario.

Además si se necesita copiar archivos locales de la máquina al contenedor para analizarlos o usarlos, debes usar la instrucción COPY en el Dockerfile

¿Qué hace COPY?

    - COPY scripts/ /opt/malware-analysis/scripts/: Copia la carpeta scripts/ desde el directorio local (donde está el Dockerfile) a la ruta /opt/malware-analysis/scripts/ dentro del contenedor.

    - COPY config.txt /opt/malware-analysis/config.txt: Copia el archivo config.txt desde el directorio local a la ruta /opt/malware-analysis/config.txt en el contenedor.


### Docker uso

Para la construcción del docker
    El punto al final es para indicar que esta dentro del dorectorio de trabajo
    -t malware-analysis:latest: Asigna un nombre (malware-analysis) y una etiqueta (latest)
        $docker build -t malware-analysis:latest .

Verificar que la imagen se haya creado correctamente
    Una vez que termine el proceso de construcción, verifica que la imagen se haya creado
        $docker images


Reconstruir la imagen en casod e copiar archivos
    Después de agregar las instrucciones COPY, debes reconstruir la imagen para incluir los nuevos archivos:
        $docker build -t malware-analysis:latest .




Detener el docker 
    Identificar el docker, con el ID o Name
        $sudo docker ps
    Posteriormente
        $sudo docker stop


