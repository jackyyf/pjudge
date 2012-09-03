#!/usr/bin/python
import judge

status = {-1: 'Compile Error', 0: 'Accepted', 1: 'Wrong Answer', 2: 'Runtime Error', 3: 'CPU Limit Exceeded', 4: 'Memory Limit Exceeded', 5: 'Idleness Limit Exceeded', -2147483648: 'Contact Staff', -2: 'Hacking Attempt Detected', 6: 'Partial Points'}

_judge = judge.Judge(3.0, 16777216)
print 'Verdict:', status[_judge.judge("C++", "aplusb.cpp", "aplusb.in", "aplusb.out")]
print 'CPU Usage:', _judge.cpuusage.value, 's'
print 'Memory Usage: %.2f KB' % (float(_judge.memoryusage.value * 100 / 1024) / 100)
print 'Score Ratio:', _judge.score.value
