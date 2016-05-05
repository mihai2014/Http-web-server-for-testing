import subprocess

#'netstat -anp | grep 8000')

#subrocess.call(['netstat', '-anp'])
#output = subprocess.check_output(['netstat', '-anp'])


def clean():
    proc = subprocess.Popen(['netstat', '-anp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    #print 'stdout:', out
    #print 'stderr:', err

    out = out.split('\n')
    for line in out:
        if(line.find('8000') > 0):
    	    items = line.split(' ')
            for item in items:
	        if(item != ''):
	            pidStr = item.find('python')
	            if(pidStr > 0):
		        pid = item.split('/')[0]
		        subprocess.check_output(['kill', '-9', pid])

