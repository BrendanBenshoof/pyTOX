#simple polite_logging library
import readline, sys
from threading import Lock

print_logs = False

logfilename = "log.log"

file(logfilename,"w+").close()

log_lock = Lock()

def log(*astr):
    res = concat(astr)
    if print_logs:
        polite_print(res)
    if log_lock.acquire():
        f= file(logfilename,"w+").close()
        f.write(res+"\n")
        f.close()
        log_lock.release()

def logPrint(*astr):
    res = concat(astr)
    polite_print(res)
    if log_lock.acquire():
        f = file(logfilename,"w+")
        f.write(res+"\n")
        f.close()
        log_lock.release()

def polite_print(astr):
    sys.stdout.write('\r'+' '*(len(readline.get_line_buffer())+2)+'\r')
    print astr
    sys.stdout.write('> ' + readline.get_line_buffer())
    sys.stdout.flush()

def concat(astr):
    output = ""
    first = True
    for i in astr:
        if not first:
            output += " "
        else:
            first = False
        output+=str(i)
    return output
