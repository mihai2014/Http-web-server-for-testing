#list of name fuctions define below and allowed for access by the user
#preventig random access for other functions
functionsList = [
    'do_something',
    'echo'
]

def do_something(request):
    msg = "Data posted was:<br>"
    fd = request.FormData
    parts = fd.parts
    for part in parts:
	if "filename" in part:
	    contentType = part['Content-Type']
	    fileName = part['filename']
	    file = part['data'] 
	    #print fileName,contentType,len(file) 
	    msg += ("fileName = %s, type = %s, size = %s bytes<br>") % (fileName,contentType,len(file))
	else:
	    name = part['name']
	    value = part['data']
	    #print name, value 
	    msg += ("%s = %s <br>") % (name,value)

    response = "<html><body>" + msg + "<html><body>"
 
    return response


def echo(request):
    firstLine = request.firstLine    
    return firstLine   
