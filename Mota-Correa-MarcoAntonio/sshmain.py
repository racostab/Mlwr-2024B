import sshGUI
import sshCLI

op = ''
print("Como desea continuar?\n"
	+"1: Por Terminal\n"
	+"2: Por Interfaz grafica (Limitado)\n"
	+"default: Salir")

op = input()

if(str(op) == '1'):
	sshCLI.start()
elif(str(op) == '2'):
	app = sshGUI.App()
	sshGUI.masterFrame(app)
	app.mainloop()
