import sshsession as ssh

session = ''

def start():
	print("Ingrese su informacion de acceso al servidor:")
	ip = input("Direccion IP: ")
	port = input("Puerto: ")
	usr = input("Usuario: ")
	passw = ''
	keydir = ''
	session = ssh.session(ip,port)
	verif = False
	while(not verif):
		print("Como desea autenticarse?\n"
		+"1: Por Contraseña\n"
		+"2: Por Llave privada\n"
		+"default: Salir")
		op = input()
		if(str(op) == '1'):
			passw = input("Contraseña: ")
			if(passw == 'salir'):
				return
			verif = session.connectByPssw(usr,passw)
		elif(str(op) == '2'):
			print("Ingrese la direccion completa a su llave")
			keydir = input("Ubicacion de la llave: ")
			if(keydir == 'salir'):
				return
			verif = session.connectByKey(usr,keydir)
		if(not verif):
			print("No se pudo iniciar sesion\nVerifique sus claves de acceso")

	print("Hecho!")
	while(True):
		print("Que desea hacer a continuacion?\n"
			+"1: Enviar un archivo por sftp\n"
			+"2: Abrir una terminal interactiva\n"
			+"default: Salir")
		op = input()
		if(str(op) == '1'):
			session.openSFTP()
			print("Ingrese la direccion completa de su archivo")
			fileLocal = input("Ubicacion del archivo:")
			print("Ingrese el nombre que se usara para guardar su archivo")
			fileRemote = input("Ubicacion del archivo:")
			session.putFile(fileLocal,fileRemote)
			print("Hecho!")
			continue
		elif(str(op) == '2'):
			session.openShell()
			return
		return