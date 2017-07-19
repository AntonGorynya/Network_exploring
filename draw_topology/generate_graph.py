#! /usr/bin/python3

import glob
from draw_network_graph import draw_topology
import copy

#if __name__ == "__main__":
#	from sys import argv
#	cdp_n = argv[1]
#	with open(cdp_n , 'r') as f:
#		string = f.read()

def parse_cdp_neighbors(string):
	d = {}
	d2 = {}
	number_of_hub = 0
	#> or #
	hostname = string[:max(string.find(">"),string.find("#"))].strip()
	#обрезаем
	raw_list=string[string.find("Port ID")+8:].split('\n')		
	try:
		raw_list.remove(hostname+"#")
	except:
		pass
	
	for i in raw_list[::-1]:		
		if i.find("Total cdp") >= 0:			
			raw_list=raw_list[:raw_list.index(i)-1]
		
	print(raw_list)
		
	#исправление бага если слишком длинный hostname		
	for i in range(len(raw_list)):	
		raw_list[i]=raw_list[i].split()				
		if len(raw_list[i]) == 1:
			raw_list[i].extend(raw_list[i+1].split())			
			raw_list[i+1] = "\n"		
		
		if raw_list[i] != []:
			raw_list[i] = [raw_list[i][0],raw_list[i][1]+raw_list[i][2],raw_list[i][-2]+raw_list[i][-1]]
			
			
			#проверка на наличе хабов
			try:
			
				if d[raw_list[i][1]] != None:
					print("Hub detected")
					d2.update( {str(number_of_hub):d[raw_list[i][1]]})
					d2.update( {str(number_of_hub):{delete_domain(raw_list[i][0]):raw_list[i][2]}})
					d.update( {(raw_list[i][1]):{"Hub to ":str(number_of_hub)}})
					number_of_hub = number_of_hub + 1
					
					
			except:
				
				d.update( {(raw_list[i][1]):{delete_domain(raw_list[i][0]):raw_list[i][2]}})

				
	d ={hostname:d}
	if d2 != {}:		
		d2 = {"Hub to ":d2}		
		d.update(d2)
		
	return d

def delete_domain(string):
	try:
		string.index(".")
		string = string [:string.index(".")]
	except:
		pass
	return string


	
	
def  generate_topology_from_cdp(list_of_files,save_to_file = True,topology_filename ="topology.yaml" ):
	result={}
	for sh_cdp in list_of_files:
		print("open", sh_cdp)
		with open(sh_cdp, 'r')as f:
			string = f.read()
			try:				
				result.update(parse_cdp_neighbors(string))					
			except:
				print("Unvalid string",string)
	if save_to_file:
		with open(topology_filename, 'w') as f:
			f.write(str(result))
	return result
	
def yaml_to_graph(input):	
	dict={}
	for hostname in input.keys():
		for local_int in input[hostname].keys():	
			for remote_host in input[hostname][local_int].keys(): 				
				dict.update({(hostname,local_int):(remote_host,input[hostname][local_int][remote_host])})
			
	return dict
	
		
def get_key(d,value):
	for k,v in d.items():
		if v == value:
			return k
	
def del_duplicate(cdp_neighbors_dict):	
#	cdp_neighbors_dict = yaml_to_graph(input)		
	d_copy=copy.deepcopy(cdp_neighbors_dict)
	for i,k in enumerate(cdp_neighbors_dict.keys()):	
		for j,v in enumerate(cdp_neighbors_dict.values()):
			if k == v:
				if cdp_neighbors_dict[k] == get_key(cdp_neighbors_dict, v) and j > i:
					del(d_copy[k]) 
	return d_copy

	
if __name__ == "__main__":	
	list_of_files = glob.glob('*_cdp*')	
	input = generate_topology_from_cdp(list_of_files,save_to_file = True,topology_filename ="topology.yaml" )	
	


cdp_neighbors_dict = yaml_to_graph(input)	
	
d_copy = del_duplicate(cdp_neighbors_dict)	
draw_topology(d_copy)
	
	

	
	
