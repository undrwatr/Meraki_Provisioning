#!/usr/bin/python

#imports
import sys
import requests
import json
import os
import pymssql as mdb
import subprocess
import cred

#custom variables for the program imported from the cred.py file located in the same directory
organization = cred.organization
key = cred.key
hub = cred.hub
sql_host = cred.sql_host
sql_username = cred.sql_username
sql_password = cred.sql_password
sql_database = cred.sql_database

#Main URL for the Meraki Platform
dashboard = "https://dashboard.meraki.com"
#api token and other data that needs to be uploaded in the header
headers = {'X-Cisco-Meraki-API-Key': (key), 'Content-Type': 'application/json'}

#variables for testing ***** Need to switch to an argument or something else
store = input("What store do you need to configure? The store must already exist in Meraki Console: ")

#Pull back the SQL Data to populate for the config later on
sql_connection = mdb.connect(sql_host,sql_username,sql_password,sql_database)

cursor = sql_connection.cursor()

cursor.execute("select [GW IP] from tblDSlip where [Store #] = (%s)", (store))
VLAN2GW = str(cursor.fetchone()[0]) 
cursor.execute("select [LAN] from tblDSlip where [Store #] = (%s)", (store))
VLAN2LAN = str(cursor.fetchone()[0]) 
cursor.execute("select [TEST LAN] from tblDSlip where [Store #] = (%s)", (store))
VLAN5LAN = str(cursor.fetchone()[0]) 
cursor.execute("select [Test GW IP] from tblDSlip where [Store #] = (%s)", (store))
VLAN5GW = str(cursor.fetchone()[0]) 

#pull back all of the networks for the organization
get_network_url = dashboard + '/api/v0/organizations/%s/networks' % organization

#request the network data
get_network_response = requests.get(get_network_url, headers=headers)

#puts the data into json format
get_network_json = get_network_response.json()

#pull back the network_id of the store that you are configuring
for i in get_network_json:
    if i["name"] == str(store):
        network_id=(i["id"])

#Update Vlans based on information taken from SQL Server, I only have a VLAN2 and VLAN5 so this is specific for my needs.

#Update Vlan2

#Buil the JSON for the put request VLAN2
VLAN2JSON = {}
VLAN2JSON["applianceIp"] = VLAN2GW
VLAN2JSON["subnet"] = VLAN2LAN + "/28"

#Create the URL
get_network_vlan2jsonurl = dashboard + '/api/v0/networks/%s/vlans/2' % network_id

#perform the update
get_network_vlan2json = requests.put(get_network_vlan2jsonurl, data=json.dumps(VLAN2JSON), headers=headers)

#Update Vlan5

#Buil the JSON for the put request VLAN5
VLAN5JSON = {}
VLAN5JSON["applianceIp"] = VLAN5GW
VLAN5JSON["subnet"] = VLAN5LAN + "/28"

#Create the URL
get_network_vlan5jsonurl = dashboard + '/api/v0/networks/%s/vlans/5' % network_id

#perform the update
get_network_vlan5json = requests.put(get_network_vlan5jsonurl, data=json.dumps(VLAN5JSON), headers=headers)

#enable VPN by writing out a curl function to a file and then calling it. This is put in due to an issue with the Meraki site. The better code is below, but this works for right now.
curl_com = open("curl", "w", 0)
bash_com = "curl -L -H 'X-Cisco-Meraki-API-Key: %s' -X PUT -H 'Content-Type: application/json' --data-binary '{\"mode\":\"spoke\",\"hubs\":[{\"hubId\":\"%s\",\"useDefaultRoute\":true }]}' 'https://dashboard.meraki.com/api/v0/networks/%s/siteToSiteVpn'" % (key, hub, network_id)
curl_com.write(bash_com)
curl_com.close()

subprocess.call(["bash ./curl"], shell=True)

#turn on VPN for the store once VLAN Configuration is done**** THIS CODE ISN'T READY YET, DUE TO SOME ISSUE WITH THE BACKEND
#VPNSET = {}
#VPNSET["hubs"] = "{'hubId': '%s', 'useDefaultRoute': 'true'}" % hub
#VPNSET["mode"] = "spoke"
#VPNSET = {"mode":"spoke","hubs":[{"hubId":"%s","useDefaultRoute":"true"}]} % hub


#create the url
#get_network_vpnset = dashboard + '/api/v0/networks/%s/siteToSiteVpn' % network_id

#perform the udpate
#get_network_vpnsetjson = requests.put(get_network_vpnset, data=json.dumps(VPNSET), headers=headers)

#Cleanup after everything is done
#close the sql connection
sql_connection.close()