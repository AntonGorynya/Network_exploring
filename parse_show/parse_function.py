#! /usr/bin/python3
# -*- coding: utf-8 -*-


import glob
import sqlite3
import re
#import pyparsing
from pyparsing import Word, nums, alphas
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import argparse
import sys
import os


work_directory = os.getcwd()
db_file = 'baltika.db'
schema_filename = 'baltika_schema.sql'
db_exists = os.path.exists(db_file)


def create_db():
	with sqlite3.connect(db_file) as conn:
		if not db_exists:
			with open(schema_filename, 'r') as f:
				shema = f.read()
			conn.executescript(shema)
		else:
			print('Database exists')

#для cisco			
def add_arp(db_file,filename):
	#hostname = filename[0:filename.find("_x_")]
	regex = re.compile('(?P<protocol>\w+?) +(?P<ip>.*?) +.+ +(?P<mac>.+?) +ARPA +(?P<vlan>\w+)')
	query = " INSERT  into arp (mac, ip, vlan, hostname) values(?, ?, ?, ?)"
	
	con = sqlite3.connect(db_file)
	with open(filename , 'r') as f:
		data = f.read().strip().split('\n')
		#data = f.readlines()
			
		hostname = data[0][:max(data[0].find(">"),data[0].find("#"))].strip()		
		for line in data[2::]:
			if (regex.search(line) !=None):				
				mac = regex.search(line).group("mac")
				ip = regex.search(line).group("ip")
				vlan = regex.search(line).group("vlan")					
				try:				
					con.execute(query,tuple([mac,ip,vlan,hostname]))	
				except:
					print("Arledy exist",mac, ip, vlan)
			else:
				print("invalid line ", line)
	con.commit()



def add_mac(db_file,filename):
	regex = re.compile(' +\w+? +(?P<mac>\w+\.\w+\.\w+) +\w+? +(?P<port>[\w/]+)')
	query = " INSERT  into L2 (hostname,mac, port) values(?, ?, ?)"
	con = sqlite3.connect(db_file)
	with open(filename , 'r') as f:
		#hostname = filename[0:filename.find("_x_")]
		data = f.read().strip().split('\n')	
		hostname = data[0][:max(data[0].find(">"),data[0].find("#"))].strip()
		for line in data:	
			if (regex.search(line) !=None):			
				mac = regex.search(line).group("mac")
				port = regex.search(line).group("port")			
				try:
					con.execute(query,tuple([hostname,mac,port]))	
				except:
					print("Arledy exist",mac, port)
			else:
				print("There is not mac ", line)
	con.commit()

def add_speed(db_file,filename):
	con = sqlite3.connect(db_file)		
	#hostname = filename[0:filename.find("_x_")]
	with open(filename,'r') as f: 
		data = f.read().strip().split('\n')	
		hostname = data[0][:max(data[0].find(">"),data[0].find("#"))].strip()		
		#ниже идет какой-то костыль
		for row in data:
			port = row.split()			
			#Начиная со статуса
			row_list = row[29::].split()
			if row_list != [] and len(row_list) > 3:
				port = port[0]
				speed = row_list[3]
				int_type = row_list[4]
				query = "UPDATE  L2 set speed = '{}' WHERE hostname = '{}' AND port = '{}'".format(speed,hostname,port)	
				con.execute(query)				
				#print(query)
	con.commit()
			

	
	
	
#	вывод
def write_to_exel(db_file,dest_filename = 'empty_book.xlsx'):
	with sqlite3.connect(db_file) as conn:
	#Позволяет далее обращаться к данным в колонках, по имени колонки	
		conn.row_factory = sqlite3.Row
	
	#создаем exel
	wb = Workbook()
	ws1 = wb.active
	ws1.title = "Title"
	
	ws1.append(['hostname','port', 'mac', 'ip' ,'speed'])
		
	for row in conn.execute("select * from L2"):
		exel_row = [row['hostname'],row['port'], row['mac'], row['ip'] ,row['speed']]
		for cell in exel_row:			
			if cell == None:
				exel_row[exel_row.index(cell)] = "None"
		ws1.append(exel_row)
		#print("{:12} {:15} {:15} {:15}".format(row['hostname'],row['port'],row['mac'],row['ip']))			
	
	wb.save(filename = dest_filename)
	

def get_all_data(db_file):
	with sqlite3.connect(db_file) as conn:
	#Позволяет далее обращаться к данным в колонках, по имени колонки	
		conn.row_factory = sqlite3.Row
	print('-' * 60)
	print('hostname','port', 'mac', 'ip' ,'speed')
	for row in conn.execute("select * from L2"):
		print(row['hostname'],row['port'], row['mac'], row['ip'] ,row['speed'])
		#print("{:12} {:15} {:15} {:15}".format(row['hostname'],row['port'],row['mac'],row['ip']))			
	print('-' * 60)	
	for row in conn.execute("select * from arp"):
		print("{:15} {:15} {:8} {:12}".format(row['mac'],row['ip'], row['vlan'], row['hostname']))	
		#print ("{:7} {:15} ".format(row['hostname'], row['location']))
	print('-' * 60)			
	

def convert_mac(mac_address):
	regex = re.compile('[\w]+')
	mac = "".join(regex.findall(mac_address)).lower()
	mac = mac[0:4]+"."+mac[4:8]+"."+mac[8:12]
	return mac

#из arp_monitor
def add_ip(db_file,filename):	
	#из arp_monitor
	regex = re.compile('(?P<ip>.+?)	+(?P<mac>.+?)	.*')
	con = sqlite3.connect(db_file)	
	current_mac = con.execute('select mac from L2').fetchall()	
	with open(filename, 'r') as f:		
		data = f.read().strip().split('\n')		
		for line in data:						
			mac = regex.search(line).group('mac').lower()			
			mac=mac.split('-')			
			mac='.'.join([mac[0]+mac[1],mac[2]+mac[3],mac[4]+mac[5]])			
			ip = regex.search(line).group("ip")
			#кортеж из 1 элемента
			if (mac, ) in current_mac:				
				query = "UPDATE  L2 set ip = '{}' where mac = '{}' ".format(ip,mac)	
				#print(query)
				con.execute(query)
			else:
				print("Mac {} is not in table. There is {}".format(mac, ip))
				
				
	#из arp db
	row = con.execute(("select * from arp").format(mac)).fetchall() 
	query_L2 = " INSERT  into L2 (hostname,mac, port, ip) values(?, ?, ?, ?)"
	for couple in row:		
		mac = couple[0] 
		ip = couple[1]
		vlan = couple[2]
		hostname =couple[3]
#		print("Mac =",mac , "IP=",ip , "port=",vlan)
		if (mac, ) in current_mac:				
			query = "UPDATE  L2 set ip = '{}' where mac = '{}' ".format(ip,mac)				
			con.execute(query)
		else:			
			con.execute(query_L2,tuple([hostname,mac,vlan,ip]))						
					
	con.commit()

# d-link
def dlink_add_mac(db_file,filename):
	query = " INSERT  into L2 (hostname,mac, port) values(?, ?, ?)"
	regex = re.compile('\w+	+(?P<port>\w+)	+(?P<mac>.+?)	+(?P<vlan>.+?)')
	con = sqlite3.connect(db_file)	
	with open(filename,'r') as f:	
		data = f.read().strip().split('\n')
		hostname = data[0][:max(data[0].find(">"),data[0].find("#"))].strip()
		for line in data:	
			try:
				mac = regex.search(line).group("mac")				
				port = regex.search(line).group("port")
				vlan = regex.search(line).group("vlan")	
				con.execute(query,tuple([hostname,mac,port]))
			except:
				print("invalid line ",line)
				
	con.commit()
	

		

#Nortel		
		
def nortel_add_speed(db_file,filename):	
	flag =False
	con = sqlite3.connect(db_file)	
	with open(filename,'r') as f: 
		data = f.read().strip().split('\n')		
		regex = re.compile('\d+ +.*')	
		hostname = data[0][:max(data[0].find(">"),data[0].find("#"))].strip()		
		for row in data:			
			if (regex.search(row) !=None):			
				flag = True				
			if flag == True:
				try:
					port = row.split()[0]
					speed = row.split()[6]
					query = "UPDATE  L2 set speed = '{}' WHERE hostname = '{}' AND port = '{}'".format(speed,hostname,port)	
					con.execute(query)											
				except:
					print("invalid line ",row)
					pass

			
	con.commit()
			
def nortel_add_mac(db_file,filename):
	flag =False
	flag2 = False
	query = " INSERT  into L2 (hostname,mac, port) values(?, ?, ?)"
	con = sqlite3.connect(db_file)		
	with open(filename,'r') as f: 
		data = f.read().strip().split('\n')	
		
		regex = re.compile('\w+-\w+ .+')
		hostname = data[0][:max(data[0].find(">"),data[0].find("#"))].strip()
		for row in data:			
			if (regex.search(row) !=None):	
				if len(row.split()) == 6:
					flag = True
				elif len(row.split()) == 4:
					flag2 = True
				
			if flag == True:	
			#61
			#00-0E-8C-DC-20-A3  Port: 25      00-0E-8C-DC-21-84  Port: 25
			#00-18-B0-F8-6A-60                00-1B-1B-0F-E8-52  Port: 25			
				mac = row[0:17].strip()
				port = row[25:30].strip()
				mac2 = row[31:50].strip()
				port2 = row[58:60].strip()
				try:
					con.execute(query,tuple([hostname,mac,port]))
					if mac2 != "":
						con.execute(query,tuple([hostname,mac2,port2]))
				except:
					print("Arledy exist",mac, port)	
					
			if flag2 == True:	
				#00-0e-8c-dc-21-84  25           00-0e-8c-dc-9f-46  23
				#00-0f-6a-88-e1-c0               00-1b-1b-0f-e8-52  25			
				mac = row[0:17].strip()
				port = row[19:30].strip()
				mac2 = row[31:50].strip()
				port2 = row[52:60].strip()	
				
				try:
					con.execute(query,tuple([hostname,mac,port]))
					if mac2 != "":
						con.execute(query,tuple([hostname,mac2,port2]))
				except:
					print("Arledy exist",mac, port)	
							
				

	con.commit()


#3-com
def IIIcom_add_mac(db_file,filename):
	regex = re.compile('(?P<mac>.+?) +\w+? +(?P<port>[\w+/].+) +\w+?')
	query = " INSERT  into L2 (hostname,mac, port) values(?, ?, ?)"
	con = sqlite3.connect(db_file)
	with open(filename , 'r') as f:
		#hostname = filename[0:filename.find("_x_")]
		data = f.read().strip().split('\n')	
		#<5500-EI>
		hostname = data[0][1:max(data[0].find(">"),data[0].find("#"))].strip()		
		for row in data:			
		#0007-e909-4598  1         Learned        GigabitEthernet1/0/28    AGING
			if (regex.search(row) !=None):			
				flag = True
				pass
			if flag == True:				
				row = row.split()	
				mac = row[0]
				port= row[3]
				try:
					con.execute(query,tuple([hostname,mac,port]))
				except:
					print("Arledy exist",mac, port)		

	con.commit()
	
def IIIcom_add_speed(db_file,filename):	
	flag =False
	con = sqlite3.connect(db_file)	
	with open(filename,'r') as f: 
		data = f.read().strip().split('\n')		
		regex = re.compile('(?P<port>[\w+/].+) +\w+? +\w+? +\w+? +\w+? +\d+?')	
#		Interface   Link     Speed  Duplex Type   PVID Description
#--------------------------------------------------------------------------------
#Aux1/0/0    UP       --     --     --     --
#Eth1/0/1    DOWN     A      A      access 1
		hostname = data[0][1:max(data[0].find(">"),data[0].find("#"))].strip()
		for row in data:
			if (regex.search(row) !=None):			
				flag = True
				pass
			if flag == True:
				try:
					port = row.split()[0]
					speed = row.split()[2]+row.split()[3]
					query = "UPDATE  L2 set speed = '{}' WHERE hostname = '{}' AND port = '{}'".format(speed,hostname,port)	
					con.execute(query)											
				except:
					print("invalid line ",row)
					pass					
	con.commit()
	
		


	
def createParser():	
	parser = argparse.ArgumentParser(description = '--> Parse files <--')
	parser.add_argument("-cdb", action="store_true", help = "create db")
	parser.add_argument("-wd", default="", action="store" , help = "work directory")
	parser.add_argument("-get_all", action="store_true", help = "get all data from db")
	parser.add_argument("-xlsname",default="empty", action="store", help = "exel name")	
	parser.add_argument("-w2x", action="store_true", help = "write to exel")
	parser.add_argument("-c", action="store_true", help = "Cisco write to db")	
	parser.add_argument("-n", action="store_true", help = "Nortel")
	parser.add_argument("-IIIcom", action="store_true", help = "3com")
	parser.add_argument("-d", action="store_true", help = "d-link")	
	parser.add_argument("-arp", action="store_true", help = "arp_monitor")	
	return parser
	
parser = createParser()
namespace = parser.parse_args(sys.argv[1:])

if namespace.wd:
	work_directory = work_directory+'/'+namespace.wd
print("Start work at ", work_directory)

list_of_arp = glob.glob(work_directory+'*_arp*')
list_of_mac = glob.glob(work_directory+'*mac*')
list_of_status = glob.glob(work_directory+'*status*')
host_arp_file = work_directory+'/arp.txt'



if namespace.cdb:
	print("creating DB...")
	create_db()
	
if namespace.c:	
	for filename_mac in list_of_mac:	
		add_mac(db_file,filename_mac)
	for filename_status in list_of_status:
		add_speed(db_file,filename_status)
	for filename_arp in list_of_arp:
		add_arp(db_file,filename_arp)		

if namespace.w2x:
	print("creating exel....")		
	write_to_exel(db_file,namespace.xlsname+".xlsx")
	print(namespace.xlsname+".xlsx created")
	
if namespace.n:
	for mac_file in list_of_mac:
		nortel_add_mac(db_file,mac_file)
	for status_file in list_of_status:	
		nortel_add_speed(db_file,status_file)
		
if namespace.IIIcom:
	for mac_file in list_of_mac:
		IIIcom_add_mac(db_file,mac_file)
	for status_file in list_of_status:
		IIIcom_add_speed(db_file,status_file)

if namespace.d:
	for mac_file in list_of_mac:
		dlink_add_mac(db_file,mac_file)

if namespace.get_all:
	get_all_data(db_file)
	
if namespace.c or namespace.n or namespace.IIIcom or namespace.d:	
#преобразуем везде маки	
	with sqlite3.connect(db_file) as conn:
	#Позволяет далее обращаться к данным в колонках, по имени колонки	
		conn.row_factory = sqlite3.Row
		for row in conn.execute("select * from L2"):
			query = "UPDATE  L2 set mac = '{}' WHERE mac = '{}'".format(convert_mac(row['mac']),row['mac'])
			conn.execute(query)
		conn.commit()

if namespace.arp:
	print("add ip addresses from arp table ...")
	#добавляем ip из arp monitor	
	add_ip(db_file,host_arp_file)