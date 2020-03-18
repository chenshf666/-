import socket
import _thread

# 访问地址服务器获取服务器地址
def ip_and_port():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest_ip = '127.0.0.1' # 默认本地ip
    dest_port = 10001 # 默认端口
    dest_addr = (dest_ip, dest_port)
    tcp_socket.connect(dest_addr)
    recv_str = tcp_socket.recv(10240).decode('utf-8')
    tcp_socket.close()

    return recv_str.split('|')

# 独立线程发送
def send(tcp_socket):
    print("<<<<<输入#exit#退出>>>>>")
    while True:
        send_data = input()
        if send_data == '#exit#':
            tcp_socket.close()
            exit()
        tcp_socket.send(send_data.encode("utf-8"))

# 独立线程接受消息
def receive(tcp_socket):
    while True:
        recv_data = tcp_socket.recv(10240)
        print('-------------------------------')
        print(recv_data.decode("utf-8"),end='') 
        print('-------------------------------')
def main():
    # 1.创建套接字socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 2.连接服务器
    dest_ip,dest_port = ip_and_port()
    dest_addr = (dest_ip, int(dest_port))
    tcp_socket.connect(dest_addr)

    # 创建独立线程用于接受服务器的消息
    _thread.start_new_thread(receive,(tcp_socket,))
    send(tcp_socket)
    # 4. 关闭套接字socket
    tcp_socket.close()

if __name__ == "__main__":
        main()