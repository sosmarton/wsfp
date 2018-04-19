import socket
import ssl
import glob
import sys
import urlparse
import string
import sqlite3 as lite
import webbrowser, os
import argparse



def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default


class bcolors:
	    HEADER = '\033[95m'
	    OKBLUE = '\033[94m'
	    OKGREEN = '\033[92m'
	    WARNING = '\033[93m'
	    FAIL = '\033[91m'
	    ENDC = '\033[0m'
	    BOLD = '\033[1m'
	    UNDERLINE = '\033[4m'

def SendRequest(ip,port,req_body,SSL):

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	ss=s

	if (SSL != False):
		ss = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1)

	addr = (ip, port)
	ss.connect(addr)
	ss.send(req_body)
	resp = ss.recv(1000)
	ss.close()
	print "###################"
	print repr(req_body)
	print "###################"
	return resp

def ParseIp(url):

	address = urlparse.urlsplit(url)[1]
		
	split=urlparse.urlsplit(url)	

	if split[0] == "http":
		port=80
	elif split[0] == "https":
		port=443

	return {'IP':address,'Port':port}


def GetFileContent(fname):
	with open(fname, "r") as ins:
		return ins.read()

def msg(msg):
	print "[+] %s" % (msg)

def err(msg):
	print "%s[-] %s%s" % (bcolors.FAIL,msg,bcolors.ENDC)


def main():

	parser = argparse.ArgumentParser(description='Request sender')
	parser.add_argument('-u','--url', help='url', required=True)
	parser.add_argument('-l','--learning', help='learning mode', default=0, const=1, required=False, nargs='?') #dest --> unique variable
	args = vars(parser.parse_args())

	dirr="requests"
	url=args['url']


	msg("Reading the contents of the "+bcolors.BOLD+dirr+bcolors.ENDC+" directory.")

	files=glob.glob(dirr+"/*")
	files_num=str(len(files))

	msg(""+bcolors.OKGREEN+files_num+bcolors.ENDC+" file(s) found.")


	target=ParseIp(url)

	msg("Target set to "+bcolors.OKGREEN+target['IP']+":"+str(target['Port'])+bcolors.ENDC+".")
	

	isSSL=False

	if (target['Port'] == 443):
		isSSL=True
	else:
		isSSL=False


	if (raw_input("Do you want to continue? (y/n)") != "y"): 
		sys.exit()

	#CREATING DB STRUCTURE
	#if os.path.isfile("test.db"):
	#	os.remove("test.db")


	db = lite.connect('test.db')
	c = db.cursor()

	c.execute('CREATE TABLE IF NOT EXISTS Servers (SId INT NOT NULL, SIP VARCHAR(255), SType VARCHAR(255), SVersion VARCHAR(255), XPByType VARCHAR(255), XPByVersion VARCHAR(255), PRIMARY KEY (SId))')
	c.execute('CREATE TABLE IF NOT EXISTS Responses (RPId INT NOT NULL, RQId INT(11), SId VARCHAR(255), RPVersion TEXT, RPStatusCode TEXT, PRIMARY KEY (RPId))')
	c.execute('CREATE TABLE IF NOT EXISTS Requests (RQId INT NOT NULL, RQName VARCHAR(255), SId INT, RQText TEXT, PRIMARY KEY (RQId))')

	db.commit()



	#CLEANUP




	db.commit()


	c.execute('SELECT SId FROM Servers ORDER BY SId DESC LIMIT 1;')

	fetch1=c.fetchone()

	if fetch1 is None:
		S_lastid = 1
	else:
		S_lastid = (int(fetch1[0]))+1

	c.execute('SELECT RPId FROM Responses ORDER BY RPId DESC LIMIT 1;')

	fetch1=c.fetchone()

	if fetch1 is None:
		RP_lastid = 1
	else:
		RP_lastid = (int(fetch1[0]))+1

	c.execute('SELECT RQId FROM Requests ORDER BY RQId DESC LIMIT 1;')

	fetch1=c.fetchone()


	if fetch1 is None:
		RQ_lastid = 1
	else:
		RQ_lastid = (int(fetch1[0]))+1

	db.commit()






	c.execute("INSERT INTO Servers VALUES('"+str(S_lastid)+"','"+url+"','N/A','N/A','N/A','N/A')")
	db.commit()




	msg("Reading file contents.")

	id=0
	reqresp={}

	for ff in files:
		id=id+1

		msg("File under "+bcolors.OKGREEN+ff+bcolors.ENDC+" was opened.")

		body = GetFileContent(ff)

		msg("Sending request #"+str(id)+" to the target...")

		resp = SendRequest(target['IP'],target['Port'],body,isSSL)



		c.execute("INSERT INTO Requests VALUES('"+str(RQ_lastid)+"','"+ff+"','"+str(S_lastid)+"','"+body+"')")
		db.commit()




		reqresp[id] = {}
		reqresp[id]['request']=body.split('\n', 1)[0]
		reqresp[id]['response']=resp.split('\n', 1)[0]
		reqresp[id]['reqfile']=ff

		c.execute("INSERT INTO Responses VALUES('"+str(RP_lastid)+"','"+str(RQ_lastid)+"','"+str(S_lastid)+"','"+reqresp[id]['response'][:8]+"','"+reqresp[id]['response'][9:]+"'"+")")		
		db.commit()

		msg("Response for the #"+str(id)+" request received...")
		
		msg("Response:")
		print resp
		msg("----------")

		found = False
		print ff
		if (ff == "requests/00 - normal"):
			for line in resp.splitlines():
				if "Server: " in line and found == False:
					found=True
					full = line[8:]
					
					if "/" in full:
						fullarray=full.split('/')
						print fullarray[0]+" || "+ fullarray[1]
						styp=fullarray[0]
						sver=fullarray[1]

					else:
						styp=full
						sver='N/A'

					c.execute("UPDATE Servers SET SType='"+styp+"', SVersion='"+sver+"' WHERE SId="+str(S_lastid)+"")
					db.commit()

				if "X-Powered-By: " in line and found == False:
					found=True
					full = line[8:]
					
					if "/" in full:
						fullarray=full.split('/')
						print fullarray[0]+" || "+ fullarray[1]
						styp=fullarray[0]
						sver=fullarray[1]

					else:
						styp=full
						sver='N/A'

					c.execute("UPDATE Servers SET XPByType='"+styp+"', XPByVersion='"+sver+"' WHERE SId="+str(S_lastid)+"")
					db.commit()

		RP_lastid=RP_lastid+1
		RQ_lastid=RQ_lastid+1


	file = open("output.html","w") 
	file.write("<h3>Uploaded Data ("+url+") </h3><table border=1><tr><th>ID</th><th>Request</th><th>Version</th><th>Status Code</th></tr>")

	db.commit()


	for x in range(1, id+1):

	    #msg("Response: %s" % (reqresp[x]['response'])
	    if reqresp[x]['response'] != "":
	    	file.write("<tr><td>"+str(x)+"</td>"+"<td>"+str(reqresp[x]['reqfile'])+"</td>"+"<td>"+reqresp[x]['response'][:8]+"</td><td>"+reqresp[x]['response'][9:]+"</td></tr>") 
	    else:
	    	file.write("<tr><td>"+str(x)+"</td>"+"<td>"+str(reqresp[x]['reqfile'])+"</td>"+"<td>N/A</td><td>N/A</td></tr>") 
	file.write("</table>") 


	file.write("<h3>Mostly matched</h3>")

	c.execute('SELECT SId FROM Servers ORDER BY SId DESC LIMIT 1;')
	fetch1=c.fetchone()

	db.commit()

	c.execute('SELECT SId FROM Servers WHERE SId != '+str(fetch1[0])+';')
	fetch2=c.fetchall()

	c.execute('SELECT count(*) FROM Servers WHERE SId != '+str(fetch1[0])+';')
	fetch2count=c.fetchone()


	c.execute('SELECT count(DISTINCT RQName) FROM Requests;')
	allreqss=c.fetchone()

	c.execute('SELECT RQName,RPStatusCode,RPVersion,Stype,SVersion,Responses.SId,XPByVersion,XPByType FROM Responses, Requests,Servers WHERE Responses.SId = '+str(fetch1[0])+' AND Requests.RQId = Responses.RQId AND Requests.SId = Servers.SId AND Responses.SId = Servers.SId;')
	refdata=c.fetchall()

	db.commit()

	pmatch={}


	for x in fetch2:


		pmatch[int(x[0])] ={}
		pmatch[int(x[0])]['counter']=0
		pmatch[int(x[0])]['servertype'] = ""
		pmatch[int(x[0])]['serverversion'] = ""
		pmatch[int(x[0])]['xpbyversion'] = ""
		pmatch[int(x[0])]['xpbytype'] = ""

		c.execute('SELECT RQName,RPStatusCode,RPVersion,Stype,SVersion,Responses.SId,XPByVersion,XPByType FROM Responses, Requests,Servers WHERE Requests.SId = '+str(x[0])+' AND Requests.RQId = Responses.RQId AND Requests.SId = Servers.SId AND Responses.SId = Servers.SId;')
		fetch5=c.fetchall()
		db.commit()

		for asd in fetch5:
			for refdata2 in refdata:
				if asd[1] == refdata2[1] and asd[2] == refdata2[2] and asd[0] == refdata2[0]:
					pmatch[int(x[0])]['counter']+=1
					pmatch[int(x[0])]['servertype'] = asd[3]
					pmatch[int(x[0])]['serverversion'] = asd[4]
					pmatch[int(x[0])]['xpbyversion'] = asd[6]
					pmatch[int(x[0])]['xpbytype'] = asd[7]

	file.write("<table border=1><tr><th>Server Type</th><th>Server Version</th><th>X-P-By Type</th><th>X-P-By Version</th><th>% match</th></tr>")


	c.execute('SELECT SId FROM Servers ORDER BY SId ASC LIMIT 1;')

	fetchasd=c.fetchone()

	for x in range(fetchasd[0], S_lastid):
			file.write("<tr><td>"+str(pmatch[x]['servertype'])+"</td>"+"<td>"+str(pmatch[x]['serverversion'])+"</td>"+"<td>"+str(pmatch[x]['xpbyversion'])+"</td><td>"+str(pmatch[x]['xpbytype'])+"</td><td>"+str(float(pmatch[x]['counter'])/float(allreqss[0])*100)+" %</td>")


	file.write("</table>") 


	file.close() 


	db.commit()

	if args['learning'] == 0:
		c.execute('DELETE FROM Servers WHERE Servers.SId='+str(S_lastid)+'')
		c.execute('DELETE FROM Requests WHERE Requests.SId='+str(S_lastid)+'')
		c.execute('DELETE FROM Responses WHERE Responses.SId='+str(S_lastid)+'')
		msg("Temporarly stored data were "+bcolors.OKGREEN+"removed"+bcolors.ENDC+" from the database.")
		db.commit()


	msg("Opening results in browser.")

	webbrowser.open('file://' + os.path.realpath("output.html"))

	db.commit()
	db.close()

if __name__ == "__main__":
	main()