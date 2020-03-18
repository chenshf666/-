import socket
import sqlite3
import _thread
import time

def _time():
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

# 用于维护一致性和两阶段提交协议的文件


# 建立一个线程，维护这个函数，始终监听来自另一个服务器的
# 命令，同时响应两阶段提交协议的vote-request，
# 发出命令的就是协作者，当协作者发回来global_commit的
# 消息，提交到数据库，否则回滚
def receive_command(filename, port):
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    addr = ("", port)
    tcp_server_socket.bind(addr)
    tcp_server_socket.listen(32)

    while True:
        client_socket, client_addr = tcp_server_socket.accept()

        command = client_socket.recv(1024).decode('utf-8') # 接收命令
        print(_time(),'收到command 来自:',client_addr,command)
        try:
            conn = do_command(filename,command)
        except Exception as e:
            # 如果发生了异常，就发给协作者,abort的消息，并回滚数据库
            client_socket.send('abort'.encode('utf-8'))
            print(_time(),'回应vote-request: abort 发起者:',client_addr,command)
            conn.rollback()
            conn.close()
        else:
            # 如果正常执行，发给协作者commit消息，等待协作者决策
            client_socket.send('commit'.encode('utf-8'))
            print(_time(),'回应vote-request: commit 发起者:',client_addr,command)
            # 对应不同的决策，做不同的动作
            vote_result = client_socket.recv(1024).decode('utf-8')
            if vote_result == 'global_commit':
                # 提交
                print(_time(),'收到vote-result: global_commit，提交事务 发起者:',client_addr,command)
                conn.commit()
                conn.close()
            else:
                # 回滚
                print(_time(),'收到vote-result: global_abort，回滚事务 发起者:',client_addr,command)
                conn.rollback()
                conn.close()
        
        client_socket.close()

    tcp_server_socket.close()

# 发起一个vote-request
def vote_request(ip,port,command):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest_addr = (ip, port)
    tcp_socket.connect(dest_addr)
    # 发送一个vote_request
    tcp_socket.send(command.encode('utf-8'))
    # 如果收到的是 commit,则返回global_commit,否则返回gloabl abort
    recv_str = tcp_socket.recv(1024).decode('utf-8')
    if recv_str == 'commit':
        send_str = 'global_commit'
    elif recv_str == 'abort':
        send_str = 'global_abort'
    else:
        raise Exception
    tcp_socket.send(send_str.encode('utf-8'))
    tcp_socket.close()
    return send_str


# 执行数据库操作，但是暂时不提交到数据库，通过两阶段提交协议来决定
# 是否提交到数据库
# 对应三种类型的命令
# command register username
# command buy username ticket_id
# command return username ticket_id
def do_command(filename, command):
    commands = command.split(' ')
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    if commands[0] == 'command' and commands[1] == 'register':
        c.execute("INSERT INTO PERSON VALUES ('{}')".format(commands[2]))
    elif commands[0] == 'command' and commands[1] == 'buy':
        c.execute("UPDATE TICKET set NUM = NUM-1 where ID={}".format(commands[3]))
        c.execute("INSERT INTO OWN VALUES ('{}',{})".format(commands[2],commands[3]))
    elif commands[0] == 'command' and commands[1] == 'return':
        c.execute("DELETE FROM OWN WHERE NAME='{}' AND TIKID={}".format(commands[2],commands[3]))
        c.execute("UPDATE TICKET set NUM = NUM+1 where ID={}".format(commands[3]))

    return conn