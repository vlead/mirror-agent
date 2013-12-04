import subprocess
import time
import sys
import re

class MirrorAgent:
	""" Main Class responsible to start the mirroring operation """
	RSYNC_BASE_CMD = '/usr/bin/rsync '
	RSYNC_COMPRESS_ARGS = '--compress '
	RSYNC_VERBOSE_ARGS = '--verbose '
	RSYNC_ARCHIVE_ARGS = '--archive '   # rlptgoD ( --recursive --links --perms --times --group --owner --devices --specials )
	RSYNC_DRY_RUN_ARGS = '--stats --dry-run '
	RSYNC_PROGRESS_ARGS = '--progress '
	RSYNC_EXCLUDES = ''
	RSYNC_INCLUDES = ''	
	RSYNC_CMD = RSYNC_BASE_CMD + RSYNC_COMPRESS_ARGS + RSYNC_VERBOSE_ARGS + RSYNC_ARCHIVE_ARGS
	RETRIES = 3
	RSYNC_LOG = 'rsync-transfer.log'
	MIRROR_LOG = 'mirroragent.log'


	class Status:
		""" Enumeration for Status """
	 	(INIT, RUNNING, FAILURE, SUCCESS) = range(0, 4)

	def __init__(self, destUrl, logPath='', srcUrl='./ '):
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
		""" Does a dry run and gets some stats """
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
			return (self.totalFiles, self.totalSize)

		except OSError, e:
			log('Start failed - OS Error:' + e)
			self.status = self.Status.FAILURE

		except ValueError, e:
			log('Start failed - Invalid Arguments' + e)
			self.status = self.Status.FAILURE

	def run(self):
		""" Starts the mirroring process """		
		self.dryrun()
		self.status = self.Status.RUNNING
		run_cmd = MirrorAgent.RSYNC_CMD + MirrorAgent.RSYNC_PROGRESS_ARGS + self.srcUrl + self.destUrl	
		self.log('Run Command= ' + run_cmd)		
		self.log('Rsync Log=' + MirrorAgent.RSYNC_LOG)	
		try:

			self.rsyncDesc = open(MirrorAgent.RSYNC_LOG, 'wb')		
			self.proc = subprocess.Popen(run_cmd, shell=True, stdout=self.rsyncDesc, stderr=self.rsyncDesc)
			self.log('Started rsync process... with pid ' + str(self.proc.pid))					
			
		except IOError, e:
			log('Unable to open rsync-transfer logfile')
			self.status = self.Status.FAILURE
		except OSError, e:
			log('Start failed - OS Error:' + e)			
			self.status = self.Status.FAILURE
		except ValueError, e:
			log('Start failed - Invalid Arguments' + e)
			self.status = self.Status.FAILURE		

	def monitor(self):
		""" Report stats of the running process """
		print "MirrorAgent Status :"
		if self.status == self.Status.RUNNING :
			while self.proc.poll() == None:		
				self.getprogress()				
			if self.proc.returnCode > 0 :
				self.status = self.Status.SUCCESS
			else:
				self.status = self.Status.FAILURE
		return (self.status)

	def getprogress(self):
		stdoutline = self.proc.stdout.readline()			
		rem = re.findall(r'to-check=(\d+)/(\d+)', stdoutline)
		#progress = (100 * (int(rem[0][1]) - int(rem[0][0]))) / total_files
		return 100
				
	def log(self, line):
		""" Output logs to logfile """
		current_time = time.strftime("%Y-%m-%d %H:%M:%S")
		self.logDesc.write(current_time + " :[" + self.__class__.__name__ + "]: " + line + "\n")
		self.logDesc.flush()
		
	def terminate(self):
		""" Close the logfile """
		self.dryproc.terminate()
		self.proc.terminate()
		self.logDesc.close()


if __name__ == '__main__' :
	print "This is main"
	mAgent = MirrorAgent('vuser@10.4.14.106:/data/', 'mirror.log')
	print "Dryrun:"
	print mAgent.dryrun()	
	print "Run:"
	mAgent.run()
	print "Monitor:"
	mAgent.monitor()
	#mAgent.die()