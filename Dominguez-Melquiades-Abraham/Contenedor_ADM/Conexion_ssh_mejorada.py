import sys
import paramiko
import getpass
import threading
import time

class Ssh:
    def __init__(self):
        self.HOST = ''
        self.USERNAME = ''
        self.PASSWORD = ''
        self.CLIENT = None
        self.shell = None

    def conecta(self):
        try:
            self.HOST = input('Nombre o ip del host: ')
            self.USERNAME = input('Usuario: ')
            self.PASSWORD = getpass.getpass()
        except Exception as e:
            print(f'Error al introducir alguno de los datos: {e}')
            sys.exit(1)

        try:
            # Conectamos por ssh
            self.CLIENT = paramiko.SSHClient()
            self.CLIENT.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.CLIENT.load_system_host_keys()
            self.CLIENT.connect(hostname=self.HOST, username=self.USERNAME, password=self.PASSWORD)
        except paramiko.AuthenticationException:
            print('Error de autenticación')
            sys.exit(1)
        except paramiko.SSHException as sshException:
            print(f'Error en la conexión SSH: {sshException}')
            sys.exit(1)
        except Exception as e:
            print(f'Ocurrió un error: {e}')
            sys.exit(1)

        # Abre un shell interactivo
        try:
            self.shell = self.CLIENT.invoke_shell()
            print("Sesión interactiva SSH iniciada. Escribe 'exit' para cerrar.")
            
            # Iniciar un hilo para leer la salida del shell
            threading.Thread(target=self.receive_output, daemon=True).start()
            
            # Leer comandos del usuario y enviarlos al shell
            while True:
                command = input()
                if command.lower() == "exit":
                    break
                self.shell.send(command + '\n')
        except Exception as e:
            print(f'Error al abrir el shell interactivo: {e}')
        finally:
            # Cerramos la conexión SSH
            if self.CLIENT:
                self.CLIENT.close()

    def receive_output(self):
        # Leer continuamente la salida del shell
        while True:
            if self.shell.recv_ready():
                output = self.shell.recv(4096).decode()
                print(output, end='')
            time.sleep(0.5)  # Añadir una pequeña pausa para no saturar la CPU

if __name__ == '__main__':
    ssh = Ssh()
    ssh.conecta()
