import random
import hashlib
import threading
import subprocess
import SocketServer
import os
import signal
from subprocess import Popen, PIPE, STDOUT

import subprocess, shlex
from threading import Timer

def kill(p, md5sum):
    print "killing", p.pid
    p.kill()
    os.kill(p.pid, signal.SIGKILL)
    os.unlink(md5sum)

def run(cmd, timeout_sec, md5sum):
    proc = subprocess.Popen(shlex.split(cmd))
    kill_proc = kill
    timer = Timer(timeout_sec, kill_proc, [proc, md5sum])
    timer.start()

class HandleRequest(SocketServer.BaseRequestHandler):
    def handle(self):
        r = self.request
        read_len = random.randint(0, 512)
        buf_size = random.randint(0, 512)
        port = random.randint(1025, 65535)

        binary = '''
        #include <sys/types.h>
        #include <sys/socket.h>
        #include <netdb.h>
        #include <stdio.h>
        #include<string.h>

        int main()
        {{
            char str[{buf_size}];
            int listen_fd, comm_fd;
            struct sockaddr_in servaddr;
            listen_fd = socket(AF_INET, SOCK_STREAM, 0);
            memset(&servaddr, 0, sizeof(servaddr));
            servaddr.sin_family = AF_INET;
            servaddr.sin_addr.s_addr = htons(INADDR_ANY);
            servaddr.sin_port = htons({port});
            bind(listen_fd, (struct sockaddr *) &servaddr, sizeof(servaddr));
            listen(listen_fd, 10);
            comm_fd = accept(listen_fd, (struct sockaddr*) NULL, NULL);

            read(comm_fd,str,{read_len});
            write(comm_fd, str, strlen(str)+1);
        }}'''.format(buf_size=buf_size, read_len=read_len, port=port)


        compiler = Popen(['gcc', '-o', '/dev/stdout', '-fno-stack-protector' ,'-xc', '-'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        binary = compiler.communicate(input=binary)[0]

        md5sum = hashlib.md5(binary).hexdigest()

        with open(md5sum, 'w+b') as f:
            f.write(binary)

        r.sendall(binary)

        print 'bufsize:', buf_size
        print 'read:', read_len
        print 'port', port
        print 'md5', md5sum

        os.chmod(md5sum, 0o777)
        run('./{}'.format(md5sum), 5, md5sum)

class ThreadedServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":
    HOST, PORT = "", int(8888)
    server = ThreadedServer((HOST, PORT), HandleRequest)
    server.allow_reuse_address = True
    server.serve_forever()
