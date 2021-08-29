# coding: utf-8
import netmiko as netm
import getpass, re
import ipaddress as cidr
import sys, os
sys.stderr = open(os.devnull,'w')

def user_input():
    """ Getting mgmt subnet, user name and password from a user"""
    mgmtnet=''
    usrnm=''
    while mgmtnet =='':
        mgmtnet=input("Mgmt network in x.x.x.x/y (CIDR) notation: ")
        if re.fullmatch(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}/\d{2}',mgmtnet):
            for i,j in enumerate(re.split('\.|/',mgmtnet)):
                if int(j)>255 or (i == 4 and int(j) >32):
                    print('Invalid subnet')
                    mgmtnet=''     
        else:
            print ("Doesn't look like a CIDR...")
            mgmtnet=''
    while usrnm =='':
        usrnm=input ("Username: ") #requesting a username
        if usrnm=='':
            print("Username can't be blank")
    usrpwd = getpass.getpass()
    return mgmtnet, usrnm, usrpwd
        
def device_conn(mgmtnet,usrnm,usrpwd):
    """Connecting to devices and pulling neccessary information"""
    print('Connecting to devices...')
    devstr=() #Tuple of IP/output of show cdp neighbor
    devicelist = [str(ip) for ip in cidr.IPv4Network(mgmtnet)]
    if len(devicelist) != 1: # if list isn't single ip = /32
        devicelist = devicelist[1:len(devicelist)-1] #then slice out subnet and broadcast addresses
    for num, item in enumerate(devicelist): #iterating through devices
        print(f'{num/len(devicelist):.0%}', end='\r') #printing the progress figure
        try:
           device = netm.ConnectHandler(host=item, username=usrnm, password=usrpwd, device_type="cisco_ios", conn_timeout=2) #connecting to device
           devstr += ((item, device.send_command("show cdp neighbors detail"),device.send_command("show version | i IOS")),) # getting output and puts in a tuple   
           device.disconnect() # disconnect from device
        except Exception as e:
            pass
    print('Done!')
    return devstr # return tuple of IP + neighbor string + software string

def neighbor_list(*neighbor_string):
    """Checking the neighbor string from a device and finding out the neighbors"""
    neighbor_list_dict={}
    for host, neighbor, soft in (neighbor_string):
        neigh_name = (re.findall(r'Device ID: (\S*)', neighbor))
        neigh_port = (re.findall(r'Interface: (\S*\b)', neighbor))
        neighbor_list_dict.update ({host:dict(zip(neigh_name,neigh_port))})           
    return neighbor_list_dict #return dict of IP + neighbot list
    
def software_ver(*software_string):
    """Checking the software string from a device and finding out the version"""
    software_ver_dict={}
    for host, neighbor, soft in (software_string):
        soft_ver = (re.findall(r'Version (\S*, RELEASE SOFTWARE \S*)',soft))[0]
        software_ver_dict.update({host:soft_ver})
    return software_ver_dict #return IP + soft ver
 
def printing_output(neighbor_list, software_list):
    """Printing the output as a table"""
    #print(neighbor_list,software_list)
    print('IP\t\t\t\t\t\t\tNeighbors \t\t\t\t\tSoftware')
    delim='--'
    for ip,host in neighbor_list.items():
        for count, keyn in enumerate(host):
            if count==0:
                print(' ')
                print (f'{ip:16}{keyn:>40}@{host[keyn]:31}{software_list[ip]}')
            else:
                print (f'{delim:16}{keyn:>40}@{host[keyn]}')
        if host =={}:
            print (f'{ip:88}{software_list[ip]}')

def runner():
    device_data=device_conn(*user_input())
    neighbor_list_dict = neighbor_list(*device_data)
    software_ver_dict = software_ver(*device_data)
    printing_output(neighbor_list_dict, software_ver_dict)

if __name__== "__main__":
    runner()
    
