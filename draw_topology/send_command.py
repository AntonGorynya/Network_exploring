#! /usr/bin/python3
# -*- coding: utf-8 -*-

import netmiko
import yaml
import getpass
import os
import time
import subprocess
import argparse
import multiprocessing
from queue import Queue
import sys


with open('ip_list.txt', 'r') as f:
	ip_list = f.read().rstrip().split('\n')

commands = [ 'interface  loopback 0',
             'no shutdown']

print("Hello!")
username = input('Username: ')
password = getpass.getpass('Password: ')
enable_password = getpass.getpass('Enable password: ')


def create_net_dict(ip_list):
	device_dict = {'cisco':[]}
	for ip in ip_list:
		device_dict['cisco'].append({'ip':ip})
	for device_type in device_dict.keys():
		for device in device_dict[device_type]:
			device.update({'username':username})
			device.update({'password':password})
			device.update({'secret':enable_password})
			device.update({'device_type':'cisco_ios_telnet'})
			device.update({'global_delay_factor': 3})
	return(device_dict)


def send_show_command(device, show_command):
	try:
		ssh = netmiko.ConnectHandler(**device)
		ssh.enable()
		result = ssh.send_command(show_command)
		print("Connected to {}".format(device['ip']))
		#немного костылей
		hostname = ssh.send_command('show running-config | include hostname')[9::]	
		with open('{}_{}_{}.txt'.format(device['ip'],hostname,show_command.replace(" ","_")),'w') as f:
		# >\n - тк лень переписывать имеющие функции для show cdp neighbor
			f.write(hostname+">\n"+result)
	except:
		print("unable to connect to {}".format(device['ip']))	
	return result


def send_config_commands(device, config_commands, output=True):
	try:
		ssh = netmiko.ConnectHandler(**device)
		print("Connected to {}".format(device['ip']))
		ssh.enable()
		result = ssh.send_config_set(config_commands)
		if result.count('Incomplete command'):
			print ('Error during executing "%s" on %s: Incomplete command' % (config_commands, device['ip']))
		elif result.count('Ambiguous command'):
			print ('Error during executing "%s" on %s: Ambiguous command' % (config_commands, device['ip']))
		elif result.count('Invalid input'):
			print ('Error during executing "%s" on %s: Invalid input' % (config_commands, device['ip']))
		else:
			with open('{}_config.txt'.format(device['ip']),'w') as f:
				f.write(result)
			if output:
				print({device['ip']: result})
	except:
		print("unable to connect to {}".format(device['ip']))


def send_commands_from_file(device, filename, output=True):
	try:
		ssh = netmiko.ConnectHandler(**device)
		ssh.enable()
		result = ssh.send_config_from_file(filename)

		if result.count('Incomplete command'):
			print ('Error during executing "%s" on %s: Incomplete command in file' % (filename, device['ip']))
		elif result.count('Ambiguous command'):
			print ('Error during executing "%s" on %s: Ambiguous command' % (filename, device['ip']))
		elif result.count('Invalid input'):
			print ('Error during executing "%s" on %s: Invalid input' % (filename, device['ip']))
		else:
			with open('{}_config_from_file.txt'.format(device['ip']),'w') as f:
				f.write(result)
			if output:
				print({device['ip']: result})
	except:
		print("unable to connect to {}".format(device['ip']))


def send_commands(device, show='', config=[],  filename=''):
	if config:
		return send_config_commands(device, config, output=False)
	if show:
		show = input('Show command:')
		return send_show_command(device, show)
	if filename:
		return send_commands_from_file(device, filename, output=True)


def ping(ip, count):
# что бы не было бага
	responce = 1
	responce = os.system("ping -c {} ".format(count) + ip)
	return responce

def createParser():
	parser = argparse.ArgumentParser(description = '--> Send commands to Cisco devices <--')
	parser.add_argument("-s", action="store_true", help = "send show command")
	parser.add_argument("-c", action="store_true", help = "send config command")
	parser.add_argument("-f", action="store_true", help = "send config command from file")
	return parser

def conn_processes(function, devices, command , limit = 2):
	processes = []
	queue = multiprocessing.Queue()
	results = []
	w_min = 0	
	while True:
		print("new round")

		for device in devices[w_min:min(w_min+limit,len(devices))]:
			p = multiprocessing.Process(target = function, args = (device,queue, [command] ))
			p.start()
			processes.append(p)

		for p in processes:
			p.join()  
	
		for p in processes:
			results.append(queue.get())
			
		print("Round end ")
		processes = []
		
		if w_min+limit <=  len(devices)  :
			w_min = w_min+limit
	
		else:
			break

	return results




	
parser = createParser()	
namespace = parser.parse_args(sys.argv[1:])

device_dict = create_net_dict(ip_list)




if __name__ == "__main__":
	for device_type in device_dict.keys():						
		if namespace.c:				
			print( conn_processes(send_commands, device_dict[device_type], ["",commands,""]) )
		if namespace.s:				
			print( conn_processes(send_commands, device_dict[device_type], [True,"",""]) )
		if namespace.f:				
			print( conn_processes(send_commands, device_dict[device_type], ["","",'config.txt']) )
