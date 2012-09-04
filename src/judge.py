#!/usr/bin/python2.7

import multiprocessing, subprocess, time, os, resource, signal, sys

_scale = {'kB': 1024, 'mB': 1048576,
		  'KB': 1024, 'MB': 1048576}

def _compare(usr, std):
	std = std.split("\n")
	usr = usr.split("\n")
	lstd = len(std)
	lusr = len(usr)
	for _ in range(0, max(lstd, lusr)):
		try:
			stdl = std[_].strip()
		except IndexError:
			stdl = ''
		try:
			usrl = usr[_].strip()
		except IndexError:
			usrl = ''
		if(stdl != usrl):
			return 0.0
	return 1.0

class Judge:
	def __init__(self, cpulimit = 1.0, memorylimit = 256 * 1024 * 1024):
		self.cpulimit = multiprocessing.Value('f', cpulimit)
		self.memorylimit = multiprocessing.Value('i', memorylimit)
		self.cpuusage = multiprocessing.Value('f', 0.0)
		self.memoryusage = multiprocessing.Value('i', 0)
		self.status = multiprocessing.Value('i', 0)
		self.errstr = ''
		self.score = multiprocessing.Value('f', 0.0)
		
	def limit(self):
		resource.setrlimit(resource.RLIMIT_AS, (self.memorylimit.value, self.memorylimit.value + 16777216))
		resource.setrlimit(resource.RLIMIT_CPU, (self.cpulimit.value, self.cpulimit.value + 1.0))
		os.chroot("/tmp/pjudge/")
		os.setgid(305)
		os.setuid(305)
		return 0
	
	def monitor(self, pid):
		global _scale
		path1 = '/proc/%d/status' % pid
		while self.status.value == 255:
			try:
				f = open(path1, 'r')
				dat = f.read()
				f.close()
			except IOError:
				time.sleep(0.01)
				continue
			i = dat.index("VmPeak")
			dat = dat[i:].split(None, 3)
			if len(dat) < 3:
				time.sleep(0.01)
				continue
			self.memoryusage.value = int(int(dat[1]) * _scale[dat[2]])
	def run(self, command, _input, output, compare):
		try:
			f = open(_input, 'r')
			_in = f.read() + chr(26)
			f.close()
			f = open(output, 'r')
			_out = f.read()
			f.close()
		except IOError:
			self.status.value = -2147483648
			return -2147483648
		try:
			programThread = subprocess.Popen(command, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, preexec_fn = self.limit, bufsize = -1)
		except OSError:
			self.status.value = -2
			return -2
		programThreadId = programThread.pid
		monitorThread = multiprocessing.Process(target = self.monitor, args = (programThreadId, ))
		monitorThread.daemon = True
		monitorThread.start()
		programOutput = programThread.communicate(_in)
		self.status.value = 0
		monitorThread.terminate()
		path2 = '/proc/%d/stat' % os.getpid()
		f = open(path2, 'r')
		self.cpuusage.value = float(f.read().split(" ")[15]) / float(os.sysconf(os.sysconf_names['SC_CLK_TCK']))
		f.close()
		if programThread.returncode != 0 :
			if -programThread.returncode == signal.SIGXCPU :
				self.status.value = 3
				return 3
			self.status.value = 2
			return 2
		self.score.value = compare(programOutput[0], _out)
		if self.score.value == 1.0:
			self.status.value = 0
			return 0
		if self.score.value != 0.0:
			self.status.value = 6
			return 6
		self.status.value = 1
		return 1 
	
	def judge(self, _type, source, _input, output, compare = _compare):
		if os.getuid() != 0:
			print >> sys.stderr, 'Judge must be run by root!'
			return -2147483648
		sys.stderr = open('/dev/null', 'w')
		try:
			os.mkdir('/tmp/pjudge/')
			os.chmod('/tmp/pjudge/', 0755)
		except OSError:
			pass
		exeName = '/bin' + str(os.getpid())
		exePath = '/tmp/pjudge/bin' + str(os.getpid())
		if _type == 'C++':
			compileThread = subprocess.Popen(['g++', '--static', '-Wall', '-o', exePath, source], stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = -1)
		elif _type == 'C':
			compileThread = subprocess.Popen(['gcc', '--static', '-Wall', '--std=c99', '-lm', '-o', exePath, source], stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = -1)
		elif _type == 'FPC':
			compileThread = subprocess.Popen(['fpc', '-o' + exePath, source], stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = -1)
		else :
			self.status.value = -2147483648
		compileResult = compileThread.communicate()
		if compileThread.returncode != 0:
			self.errstr = compileResult[1]
			self.status.value = -1
			return -1
		sizeThread = subprocess.Popen(['size', exePath], stdout = subprocess.PIPE, stderr = subprocess.PIPE, bufsize = -1)
		self.memoryusage.value = int(sizeThread.communicate()[0].split("\n")[1].split("\t")[3])
		if(self.memoryusage.value >= self.memorylimit.value):
			self.status.value = 4
			return 4
		self.status.value = 255
		judgeThread = multiprocessing.Process(target = self.run, args = (exeName, _input, output, compare))
		judgeThread.start()
		judgeThread.join(self.cpulimit.value + 2.0)
		if self.status.value == 255:
			path2 = '/proc/%d/stat' % judgeThread.pid
			f = open(path2, 'r')
			self.cpuusage.value = float(f.read().split(" ")[15]) / float(os.sysconf(os.sysconf_names['SC_CLK_TCK']))
			f.close()
			judgeThread.terminate()
			os.remove(exePath)
			self.status.value = 5
			return 5
		os.remove(exePath)
		return self.status.value

