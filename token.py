import socket
import sqlite3
import _thread

# 用于获取令牌和释放令牌

# 获取令牌
def get_token():
	# 连接到令牌服务器
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest_ip = '127.0.0.1'
    dest_port = 10086
    dest_addr = (dest_ip, dest_port)
    tcp_socket.connect(dest_addr)
    # 收到令牌服务器的回复说明拿到了令牌
    recv_str = tcp_socket.recv(1024).decode('utf-8')
    return tcp_socket

# 释放令牌
def release_token(tcp_socket):
	# 发消息OK给令牌服务器，说明令牌已经不需要
	tcp_socket.send('OK'.encode('utf-8'))
	tcp_socket.close()