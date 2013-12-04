#!/usr/bin/env python

"""
  This is a job scheduled on crontab that initiates the mirroring process with 
  appropriate arguments
"""
import time
from MirrorAgent import MirrorAgent

# IIT Delhi Variables
iitDelHost = '10.4.14.106' 
iitDelUser = 'vuser'
iitDelLoc = '/data/'
iitDelRsyncUrl = iitDelUser + '@' + iitDelHost + ":" + iitDelLoc
iitDelmirrorLog = 'iitd-mirror-' + time.strftime("%Y-%m-%d") + '.log'

# Source Url
iiithUrl = '/labs/'
iitDelAgent = MirrorAgent(iitDelRsyncUrl, iiithUrl, iitDelmirrorLog)

print 'Executing a Dryrun:'
(status, files, bytes) = iitDelAgent.dryrun()	
if status == False :
	print 'Dryrun failed. Check logfile(' + iitDelmirrorLog + ') for details'
	sys.exit(-1)

print 'Executing a Real Run:'
(status, pid) = iitDelAgent.run()
if status == False :
	print 'Realrun failed. Check logfile(' + iitDelmirrorLog + ') for details'
	sys.exit(-1)

print 'Starting the Monitor:'
print 'ExitStatus = ' + iitDelAgent.monitor()