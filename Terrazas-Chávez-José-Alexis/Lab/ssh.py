import paramiko  #Se importa libreria paramiko para establecer la conexion de este script de Python a una MV con un SO linux y una distribución Kali Linux a través de SHH

# Configuración de la conexión SSH
host = "192.168.105.249"  # Reemplaza con la IP de la VM
port = 22  # Puerto SSH (normalmente 22)
username = "admin"  # El suario en Kali Linux
password =  "admin"  # La contraseña del ususario

# Inicializar el cliente SSH
client = paramiko.SSHClient()

# Auto aceptar las llaves de host desconocidas
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Conectar a la máquina remota con las credenciales e identificadores.
    client.connect(host, port, username=username, password=password)

    # Ejecutar un comando remoto (ejemplo: 'ls')
    stdin, stdout, stderr = client.exec_command("ls")
    
    # Imprimir el resultado del comando
    print("Salida del comando:")
    print(stdout.read().decode())

    # Cerrar la conexión
    client.close()

except Exception as e: #En caso de mala conexión se colocara el error
    print(f"Error al conectarse por SSH: {str(e)}")
