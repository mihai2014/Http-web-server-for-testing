#list of name fuctions define below and allowed for access by the user
#preventig random access for other functions
functionsList = [
    'do_something',
    'echo'
]

def do_something(request):
    msg = "Data posted was:<br>"
    fd = request.FormData
    postData = fd.read

    for item in postData:
	name 		= item["name"]
	contentType 	= item["contentType"]
	fileName 	= item["fileName"]
	value 		= item["value"]

	if(fileName == ""):
	    msg += "name = %s value = %s<br>" % (name,value)
	else:
	    fileSize = len(value)
	    msg += "fileName = %s type = %s fileSize = %s<br>" % (fileName,contentType,fileSize)

    response = "<html><body>" + msg + "<html><body>"
 
    return response


def echo(request):
    firstLine = request.firstLine    
    return firstLine   
