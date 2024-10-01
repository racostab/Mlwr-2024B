import sys
import paramiko
import getpass

class Ssh:
    def __init__(self):
        self.HOST = ''
        self.USERNAME = ''
        self.PASSWORD = ''
        self.CLIENT = None

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
            shell = self.CLIENT.invoke_shell()
            print("Sesión interactiva SSH iniciada. Escribe 'exit' para cerrar.")
            while True:
                command = input("$ ")
                if command.lower() == "exit":
                    break
                stdin, stdout, stderr = self.CLIENT.exec_command(command)
                print(stdout.read().decode())
        except Exception as e:
            print(f'Error al abrir el shell interactivo: {e}')
        finally:
            # Cerramos la conexión SSH
            if self.CLIENT:
                self.CLIENT.close()

if __name__ == '__main__':
    ssh = Ssh()
    ssh.conecta()
19