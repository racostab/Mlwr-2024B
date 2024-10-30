import paramiko
from paramiko import ssh_exception as ex

import re
import interactiveShell

class session():
	ssh = paramiko.SSHClient()
	sftp = ''
	ip = ""
	port = ""
	def __init__(self,ip,port):
		self.ip = ip
		self.port = port
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	def __del__(self):
		self.ssh.close()

	def connectByPssw(self,user,pssw):
		try:
			self.ssh.connect(self.ip,self.port,user,pssw)
			#self.executeCommand('ip a')
			return True
		except ex.SSHException:
			return False
	def connectByKey(self,user,keyFile):
		try:
			self.ssh.connect(self.ip,self.port,user,key_filename=keyFile)
			#self.executeCommand('ip a')
			return True
		except ex.SSHException:
			return False

	def closeConnection(self):
		self.ssh.close()

	def executeCommand(self,com):
		stdin,stdout,stderr=self.ssh.exec_command(com,timeout=5)
		if(len(stderr.readlines())!=0):
			#print(stderr.readlines())
			return stderr.readlines()
		if(stdout):
			outlines=stdout.readlines()
			resp=''.join(outlines)
			#print(resp)
			return outlines
		return 'empty'

	def putFile(self,dirLocal,filename):
		try:
			self.sftp.put(dirLocal,filename)
			self.sftp.close()
			return True
		except ex.SSHException:
			return False

	def openShell(self):
		channel = self.ssh.invoke_shell()
		print("Usted ha entrado exitosamente")
		interactiveShell.interactive_shell(channel)

	def openSFTP(self):
		try:
			self.sftp = self.ssh.open_sftp()
			return True
		except ex.SSHException:
			return False

