import socket
import sqlite3
import _thread
import time

token_server_name = '<<<令牌服务器>>>'
address_server_name = '   地址服务器   '

def _time():
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

# 令牌服务器
def allocate_token():
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    addr = ("", 10086)
    tcp_server_socket.bind(addr)
    tcp_server_socket.listen(32)

    while True:
        client_socket, client_addr = tcp_server_socket.accept()

        client_socket.send('OK'.encode('utf-8'))
        print(token_server_name,_time(),'将令牌交给',client_addr)
        client_socket.recv(1024)
        print(token_server_name,_time(),'回收令牌',client_addr)
        
        client_socket.close()
    tcp_server_socket.close()

def main():
    # 新建线程维护令牌服务器
    _thread.start_new_thread(allocate_token,())

    # 下面是地址服务器，用于告诉客户端应该访问的服务器地址
    available_ip = ["127.0.0.1","127.0.0.1"]
    available_port = [8866, 8868]
    index = 0 # 决定发送哪个地址给客户端
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    addr = ("", 10001)
    tcp_server_socket.bind(addr)
    tcp_server_socket.listen(16)

    while True:
        client_socket, client_addr = tcp_server_socket.accept()
        client_socket.send(("{}|{}".format(available_ip[index],available_port[index])).encode('utf-8'))
        print(address_server_name,_time(),"Lead",client_addr,'To',available_ip[index],available_port[index])
        index = (index+1)%len(available_port) # 按照顺序给客户端分发地址
        client_socket.close()
    tcp_server_socket.close()

if __name__ == '__main__':
    main()