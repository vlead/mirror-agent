import subprocess
import time
import sys
import re

class MirrorAgent:
	""" 
		This class acts as a wrapper layer over rsync for mirroring a source filesystem to a destination filesystem. 
		It can be used for both backup and restore of a filesystem.

		It uses python subprocess module to create child proccess for the file-transfer.
	    
	    It assumes that the user has appropriate privileges over both source and destination Urls. The Urls are directly 
	    passed as arguments to the rsync command.
	    
	    Note: It deletes any extraneous and newer files on the destination and hence needs to be carefully used.
	    

	    The following methods are exposed:

	    init(destUrl, srcUrl='../', logPath='')	: 
	    	Default constructor of the class. Mandatory arguments are destination Url. Optional arguments are 
	    	srcUrl(default value is parent directory '..') and logPath(default is stdout)
	    	Return Values - None
	    dryrun()  : 
	    	This method does a rsync dry-run of the mirroring operation and can be used to see commands to be run, 
	    	estimate transfer statistics like numfiles, totaltransfersize. 
	    	Return Values - Tuple containing (statusOfDryRun, estimatedFiles, estimatedSize)
	    run()     : 
	    	This method starts a the rsync real-run process with proper arguments.
	    	Return Values - Tuple containing (statusOfRun, rsyncPid)
	    monitor() : 
	    	This method can be used to monitor the rsync process, its progress and return code
	    	Return Values - Boolean based on the ExitStatus of the rsync process
	    getprogress() : 
	    	This method estimates the progress of the file-transfer based on the current 
	    	status (Not yet implemented fully).
	    	Return Values - IntegerValue(%) indicating how much of the mirroring is done
	    log() : 
	    	This method logs messages to the MirrorAgent log.
	    	Return Values - None
	    terminate() : 
	    	This method can be used to abort a running file-transfer in certain circumstances.
	    	Return Values - Returns True on Success

	    A typical use-case is described below :-

	    1) Create an instance of the MirrorAgent Class:
				mymirrorAgent = MirrorAgent(destUrl, srcUrl, 'mirroring.log')

		2) Execute a dryrun of the mirroring process:
				mymirrorAgent.dryrun()

		3) Execute a real run of the mirroring process:
				mymirrorAgent.run()

		4) Monitor the rsync process:
				mymirrorAgent.monitor()

	 """


	RSYNC_BASE_CMD = '/usr/bin/rsync '
	RSYNC_COMPRESS_ARGS = '--compress '
	RSYNC_VERBOSE_ARGS = '--verbose '
	RSYNC_ARCHIVE_ARGS = '--archive --delete '   # rlptgoD ( --recursive --links --perms --times --group --owner --devices --specials )
	RSYNC_DRY_RUN_ARGS = '--stats --dry-run '
	RSYNC_PROGRESS_ARGS = '--progress '
	RSYNC_EXCLUDES = ''
	RSYNC_INCLUDES = ''	
	RSYNC_CMD = RSYNC_BASE_CMD + RSYNC_COMPRESS_ARGS + RSYNC_VERBOSE_ARGS + RSYNC_ARCHIVE_ARGS
	RETRIES = 3
	POLL_TIMER = 30
	RSYNC_LOG = '_rsync-transfer.log'
	MIRROR_LOG = 'mirroragent.log'


	class Status:
		""" Enumeration Status Codes """
	 	(INIT, RUNNING, FAILURE, SUCCESS) = range(0, 4)

	def __init__(self, destUrl, srcUrl='../ ', logPath=''):
		""" Initialize the destination Url and logFile path """		
		self.srcUrl = srcUrl + ' '
		self.destUrl = destUrl + ' '
		try:
			if logPath == '':
				self.logDesc = sys.stdout
			else:
 				self.logDesc = open(logPath, 'wb+')		
 			self.status = self.Status.INIT	
 			self.log('Initialization done with log=' + logPath + ' srcUrl=' + self.srcUrl + ' destUrl=' + self.destUrl)	
		except IOError, e:
			print 'Initialization Failed: Unable to open logfile:' + logPath, e
			self.status = self.Status.FAILURE
			print 'Dying..'
		
	def dryrun(self):
		""" Spawns a rsync dry run process and returns totalFiles and totalSize """
		dryrun_cmd = MirrorAgent.RSYNC_CMD + MirrorAgent.RSYNC_DRY_RUN_ARGS + self.srcUrl + self.destUrl
		self.log('Attempting a dry-run...')		
		self.log('Dryrun Command= ' + dryrun_cmd)
		try:				
			self.dryproc = subprocess.Popen(dryrun_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			result = self.dryproc.communicate()[0]
			#self.log('Dryrun Output:' + result)
			self.totalFiles = re.findall(r'Number of files: (\d+)', result)
			self.totalSize = re.findall(r'Total file size: (\d+)', result)
			self.log('Total Files= ' + self.totalFiles[0] + ' Total Size=' + self.totalSize[0])
			return (True, self.totalFiles, self.totalSize)

		except OSError, e:
			self.log('Dryrun failed - OS Error:' + e)
			return (False, -1, -1)

		except ValueError, e:
			self.log('Dryrun failed - Invalid Arguments' + e)
			return (False, -1, -1)

		except Exception, e:
			self.log('Dryrun failed - Some error occured' + e)
			return (False, -1, -1)

	def run(self):
		""" Spaws the rsync process to start the mirroring and returns the pid of the process """		
		self.dryrun()
		self.status = self.Status.RUNNING
		run_cmd = MirrorAgent.RSYNC_CMD + MirrorAgent.RSYNC_PROGRESS_ARGS + self.srcUrl + self.destUrl	
		self.log('Run Command= ' + run_cmd)		
		self.log('Rsync Log=' + MirrorAgent.RSYNC_LOG)	
		try:

			self.rsyncDesc = open(MirrorAgent.RSYNC_LOG, 'wb')		
			self.proc = subprocess.Popen(run_cmd, shell=True, stdout=self.rsyncDesc, stderr=self.rsyncDesc)
			self.log('Started rsync process... with pid ' + str(self.proc.pid))	
			return (True, self.proc.pid)
			
		except IOError, e:
			self.log('Unable to open rsync-transfer logfile')
			self.status = self.Status.FAILURE
			return (False, -1)	
		except OSError, e:
			self.log('Start failed - OS Error:' + e)			
			self.status = self.Status.FAILURE
			return (False, -1)	
		except ValueError, e:
			self.log('Start failed - Invalid Arguments' + e)
			self.status = self.Status.FAILURE	
			return (False, -1)	
		except Exception, e:
			self.log('Start failed - Some error occured' + e)
			self.status = self.Status.FAILURE	
			return (False, -1)	

	def monitor(self):
		""" Report stats of the running rsync process """
		print "MirrorAgent Monitor :"
		if self.status == self.Status.RUNNING :
			while self.proc.returncode == None :						
				self.log('Progress=' + str(self.getprogress())
				self.proc.poll()					
			if self.proc.returncode > 0 :
				self.status = self.Status.SUCCESS
				self.log('Rsync process(PID=' + self.proc.pid + ') completed')
			else:
				self.status = self.Status.FAILURE				
				self.log('Rsync process(PID=' + self.proc.pid + ') failed with statuscode=' + self.proc.returnCode)
			time.sleep(MirrorAgent.POLL_TIMER)			
		return self.status

	def getprogress(self):
		""" Still not implemented - but is possible through the rsync process handle """
		#stdoutline = self.rsyncDesc.readline()			
		#rem = re.findall(r'to-check=(\d+)/(\d+)', stdoutline)
		#print rem
		#progress = (100 * (int(rem[0][1]) - int(rem[0][0]))) / total_files
		return 0
				
	def log(self, line):
		""" Output logs to a logfile """
		current_time = time.strftime("%Y-%m-%d %H:%M:%S")
		self.logDesc.write(current_time + " :[" + self.__class__.__name__ + "]: " + line + "\n")
		self.logDesc.flush()
		
	def terminate(self):
		""" Terminate any running processes and close all file handles """
		self.dryproc.terminate()
		self.proc.terminate()
		self.logDesc.close()
		return True


if __name__ == '__main__' :
	
	myAgent = MirrorAgent('vuser@10.4.14.106:/data/', '../../', 'mirror.log' )
	print 'Executing a Dryrun:'
	print mAgent.dryrun()	
	print 'Executing a Real Run:'
	print 'PID=' + mAgent.run()
	print 'Starting the Monitor:'
	print 'ExitStatus = ' + mAgent.monitor()
	