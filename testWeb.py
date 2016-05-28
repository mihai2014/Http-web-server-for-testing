from internal import *
from clean import clean
from http_codes import http_codes
import sys, os
from socket import *

#clean port 8000 just in case
clean()

HOST = ''   # all available interfaces
PORT = 8000

s = socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)

def isThere(name):
    for item in functionsList:
        if (item == name):
            return True
    return None

def getFunction(name):
    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(name)
    if not method:
        raise NotImplementedError("Method %s not implemented" % name)
    return method

def readFile(file):
    try:
        f = open(file, "rb")
        str = f.read();
        f.close()
        return str
    except:
        return None

def state(nr):
    try:
        return http_codes[str(nr)][0]
    except:
        return None

def send_all(sock,msg):
    totalsent = 0
    while totalsent < len(msg):
        sent = sock.send(msg[totalsent:])
	if sent == 0:
	    raise RuntimeError("socket connection broken")
	totalsent = totalsent + sent	

def recv_all(sock, length):
    data = ''
    while len(data) < length:
	chunk = sock.recv(length - len(data))
        if not chunk:
	    raise RuntimeError('socket closed: read only %d bytes from a %d-byte message' % (len(data), length))
	data += chunk
    return data

class FormData:
    def __init__(self,data,boundary):
	self.debug = False
	self.data = data
	self.boundary = boundary
	self.type = [] 
	self.level = 0
	self.read = []
	self.load()

    def load(self):
	endLine = "\r\n"
	endDescription = "\r\n\r\n"
	endData= "\r\n--"
	endForm = "--\r\n"

	strData = ""
	str1 = ""   # 2 chars accumulator
	str2 = ""   # 4 chars accumulator
	str3 = ""   # len(boundary) chars accumulator

        for c in self.data:

            strData += c
            str1 += c
	    str2 += c
	    str3 += c

            if (len(str1) > 2):
                str1 = str1[1:len(str1)]
            if (len(str2) > 4):
                str2 = str2[1:len(str2)]
            if (len(str3) > len(self.boundary)):
                str3 = str3[1:len(str3)]


	    if(str3 == self.boundary):			
		self.level = 1  # boundary
		strData = ""
	    elif(str1 == endLine and self.level == 1):	
		self.level = 2  # begin description
		strData = ""
	    elif(self.level == 2 and str2 == endDescription):
		self.level = 3  # end description, begin data
		self.processData("description",strData[0:len(strData)-4]) #without last ending chars: endDescription
		strData = ""
	    elif(self.level == 3 and str2 == endData):
		self.level = 0  # end data, reset
		self.processData("data",strData[0:len(strData)-4]) #without last ending chars: endData
		strData = ""


    def processData(self,type,data=None):
        if(self.debug):
            print type,
            if(data != None):
                print data.replace("\r\n","CRLF")
            else:
                print ""


	if(type == "description"):
	    description = data.split("\r\n")
	    for item in description:
		self.type.append(self.readDescription(item))

	if(type == "data"):
	    #init
            filename = ""
            contentType = ""
            value = ""

            for item in self.type:
                if(item[0] == "Content-Disposition"):
                    name = item[2]["name"]
                    if("filename" in item[2]):
                        filename = item[2]["filename"]
                if(item[0] == "Content-Type"):
                    contentType = item[1]

            #print "name=%s filename=%s contentType=%s" % (name, filename, contentType)
            #print "value=%s" % (data)
            self.read.append({'name':name,'fileName':filename,'contentType':contentType,'value':data})

	    #reset
	    self.type = []
            filename = ""
            contentType = ""
            value = ""

    def readDescription(self,line):
	variables = {}

	string = line.split(":")
	param = string[0]
	attribs = string[1].split(";")
	length = len(attribs)

	for n in range(length):
	    if(n == 0):
		dataType = attribs[n].replace(' ','')
	    else:
		attr = attribs[n].replace('"','')
		attr = attr.replace(' ','')
		attr = attr.split("=")
		variables[attr[0]] = attr[1]

	return[param, dataType, variables]
	
	

class Header:
    def __init__(self):
        self.list = {}

    def add(self,name,value):
	self.list[name] = value
	if(name == "Content-Type"):
	    if(value.find("multipart/form-data") >= 0):
	        self.contentType = "multipart/form-data"
		items = value.split(" ")
		for item in items:
		    if(item.find("boundary") >= 0):
			self.boundary = item.split("=")[1]
	    else:
	        self.contentType = value
	        self.boundary = None

    def value(self,name):
	for key in self.list.keys():
	    if(key == name):
		return self.list[key]
	return None

    def read(self):
        headerStr = ""
        for key in self.list.keys():
            val = self.list[key]
            headerStr += key + ": " + val + "\r\n"
        return headerStr

class Message:
    def __init__(self):
        self.content = ""
        self.header = Header()
        self.body = ""
	self.isRequest = False
	self.isResponse = False
	self.FormData = []

    def response(self,code):
	self.isResponse = True
	code = str(code)
	self.firstLine = "HTTP/1.1 " + code  + " " + state(code)
	self.httpCode = "HTTP/1.1"
	self.code = code
	self.state = state(code)

    def request(self,method,resource,httpCode):
	self.isRequest = True
	self.firstLine = method + " " + resource + " " + httpCode
	self.method = method
	self.resource = resource.split("/")[1]
	self.httpCode = httpCode

    def read(self):
	self.content = ""
	if(self.isRequest and self.isResponse):
	    print "Error setting message"
	    return "Error"
        self.content += self.firstLine + "\r\n"
        self.content += self.header.read()
        self.content += "\r\n"
        self.content += self.body
        return self.content


defcon = 0
def endHeader(ch):
    """ identify CR LF CR LF succession"""

    global defcon

    if(ch != chr(13) and ch != chr(10)):
        defcon = 0
        return True

    if (defcon == 0 and ch == chr(13)): defcon = 1
    if (defcon == 1 and ch == chr(10)): defcon = 2
    if (defcon == 2 and ch == chr(13)): defcon = 3
    if (defcon == 3 and ch == chr(10)): defcon = 4

    if(defcon == 4):
        defcon = 0
        return False
    else:
        return True


def process(client):
    #1st line(method) + header

    data = ""
    notEnd = True
    while(notEnd):
        ch = client.recv(1)
        data += ch
        notEnd = endHeader(ch)

    #print "rawData", data

    message = Message()

    requestArray = []
    reqStr = data.split('\r\n')
    for item in reqStr:
        requestArray.append(item)

    startLine = requestArray[0].split(' ')
    method = startLine[0]
    resource = startLine[1]
    httpCode = startLine[2]
    message.request(method,resource,httpCode)

    for n in range(1,len(requestArray)):
	item = requestArray[n].split(":",1)
	if(item != ['']):
	    name = item[0]
	    value = item[1]
            #remove 1st blank space from name
            value2 = value.split(" ")
            if(len(value2) == 2):
                value = value2[1]
	    message.header.add(name,value)

    return message    

def do_GET(request,client):   
    ip = client.getpeername()[0]

    url = request.resource

    found = False

    if (("." in url) or (url == "")):
        if(url == ""):
            resource = "index.html"
            result = readFile(resource)
	    if(result != None): found = True
        else:
            resource = url
            result = readFile(resource)
	    if(result != None) : found = True
    else:
        if(isThere(url)):
            resource = getFunction(url)
            if(resource != None):
		found = True
                result = resource(request)
	else:
	    found = False
	    def noneFunction(): pass
	    resource =  noneFunction	
    	
    message = Message()
    message.header.add('Server','testWeb')
    message.header.add('Connection','closed')

    if(type(resource).__name__ == 'function'):
	contentType = 'text/html'
    else:
        fileName = resource.split(".")
	extension = fileName[1]
	if(extension in ["html","css","js"]):
	    contentType = 'text/html'
	elif(extension in ["png","jpg","gif"]):
	    contentType = "image/"+extension
	else:
	    contentType = 'text/html'

    message.header.add('Content-Type',contentType)

    if(found != False):
        code = 200
	message.response(code)
	if(result != None):
            message.body = result
	    contentLength = len(result)
	else:
	    msg = "<html><body><h1>GET! Done. No response defined.</h1></body></html>\n"
	    contentLength = len(msg)
	    message.body = msg
    else:
        code = 404
        message.response(code)
	msg = "<html><body><h1>" + str(code) + " " + state(code) +"</h1></body></html>\n"
	message.body = msg
	contentLength = len(msg)

    message.header.add('Content-Length',str(contentLength))

    #print request.firstLine + " " + str(code) + " " + state(code) + " " + str(contentLength)

    #print "HEADER start ==================================="
    #print request.header.read()
    #print "HEADER end ====================================="

    send_all(client,message.read())


def do_POST(request,client):
    ip = client.getpeername()[0]

    url = request.resource
    bytes = request.header.value('Content-Length')
    contentType = request.header.contentType
    boundary = request.header.boundary

    body = recv_all(client, int(bytes))

    f = open('post_log.txt', 'w+')
    f.write(request.read() + body)
    f.close()

    fd = FormData(body,boundary)
    request.FormData = fd

    msg = "<html><body><h1>POST! done. No response defined.</h1></body></html>\n"

    if(isThere(url)):
        resource = getFunction(url)
        if(resource != None):
	    code = 200
            result = resource(request)
	    if(result != None): 
		msg = result
    else:
	code = 404
        msg = "<html><body><h1>" + str(code) + " " + state(code) +"</h1></body></html>\n"
        message.body = msg
        contentLength = len(msg)	

    message = Message()
    message.response(code)
    message.header.add('Server','testWeb')
    message.header.add('Connection','closed') 
    message.header.add('Content-Type','text/html')
    contentLength = len(msg)
    message.header.add('Content-Length',str(contentLength))
    message.body = msg 

    #print request.firstLine + " " + str(code) + " " + state(code) + " " + str(contentLength)

    #print "HEADER start ==================================="
    #print request.header.read()
    #print "HEADER end ====================================="

    #client.send(message.read())
    send_all(client,message.read())

def do_Error(request,client,code,e):
    print request.firstLine + " " + str(code) + " " + state(code)
    if(e != None):
        print e

    message = Message()
    message.response(code)
    message.header.add('Server','testWeb')
    message.header.add('Content-Type','text/html')
    message.header.add('Connection','closed')
    message.body = "<html><body><h1>" + str(code) + " " + state(code) +"</h1></body></html>\n"

    client.send(message.read())


def reap():
    """Try to collect zombie processes, if any."""
    while 1:
        try:
            result = os.waitpid(-1, os.WNOHANG)
            #if no zombies anymore, stop
            if result[0] == 0: break
            procList.remove(result[0])
            print procList
        except:
            #no child processes
            break
        #print "Reaped child process %d" % result[0]

methods = ['GET','POST'] 

procList = []

while(1):
    client, addr = s.accept()

    #collecting "zombie" processes
    reap()

    pid = os.fork()

    if (pid == 0):
        request = process(client)
        method = request.method

        try:
            if(method == "GET"):
                do_GET(request,client)
            if(method == "POST"):
                do_POST(request,client)

        except Exception as e:
            #internal server error
            do_Error(request,client,500,e)

        if not(method in methods):
            #not implemented
            do_Error(request,client,501)

        os._exit(0)

    procList.append(pid)

    client.close()
