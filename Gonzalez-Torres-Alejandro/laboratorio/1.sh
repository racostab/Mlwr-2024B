
import sys
import paramiko
import getpass

class SSH:
    def __init__(self):
        self.host = ''
        self.username = ''
        self.password = ''
        self.client = None

    def get_credentials(self):
        try:
            self.host = input('Nombre o IP del host: ')
            self.username = input('Usuario: ')
            self.password = getpass.getpass('Contraseña: ')
        except Exception as e:
            print(f'Error al introducir los datos: {e}')
            sys.exit(1)

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.load_system_host_keys()
            self.client.connect(hostname=self.host, username=self.username, password=self.password)
        except paramiko.AuthenticationException:
            print('Error de autenticación. Por favor, verifique sus credenciales.')
            sys.exit(1)
        except paramiko.SSHException as sshException:
            print(f'Error en la conexión SSH: {sshException}')
            sys.exit(1)
        except Exception as e:
            print(f'Ocurrió un error inesperado: {e}')
            sys.exit(1)

    def interactive_shell(self):
        try:
            with self.client.invoke_shell() as shell:
                print("Sesión interactiva SSH iniciada. Escribe 'exit' para cerrar.")
                while True:
                    command = input("$ ")
                    if command.lower() == "exit":
                        break
                    if command.strip() == '':
                        continue
                    shell.send(command + '\n')
                    while not shell.recv_ready():
                        pass
                    output = shell.recv(4096).decode('utf-8')
                    print(output)
        except Exception as e:
            print(f'Error al abrir el shell interactivo: {e}')
        finally:
            self.client.close()

    def run(self):
        self.get_credentials()
        self.connect()
        self.interactive_shell()

if __name__ == '__main__':
    ssh = SSH()
    ssh.run()
