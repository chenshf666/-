import socket
import sqlite3
import _thread
from token import *
from consistency import *

filename = 'database2.db'
service_port = 8868
consistency_port = 8869
the_other_side_ip = "127.0.0.1"
the_other_side_consistency_port = 8867

# 注册
def register(client_socket):
    client_socket.send("请输入用户名：\n".encode("utf-8"))
    recv_str = client_socket.recv(1024).decode("utf-8") # 接收用户输入的用户名

    token_socket = get_token() # 获取令牌，如果令牌被其他程序所有，则会阻塞

    conn = sqlite3.connect(filename) # 连接到数据库文件
    c = conn.cursor()
    try:
        c.execute("INSERT INTO PERSON VALUES ('{}')".format(recv_str))
    except sqlite3.IntegrityError as e:
        # 如果方生完整性约束错误，说明主键重复，即用户名已经存在，不能注册
        client_socket.send(('该用户名已经存在!\n').encode("utf-8"))
    else:
        # 没有错误说明可以注册，这时候向另一个server发送vote-request，如果没问题的话，就提交到数据库
        vote_result = vote_request(the_other_side_ip,the_other_side_consistency_port,'command register '+recv_str)
        if vote_result == "global_commit":
            conn.commit()
            client_socket.send(('注册成功！\n').encode("utf-8"))
        else:
            conn.rollback()
            client_socket.send(('发生未知错误，请联系管理员。\n').encode("utf-8"))
    
    conn.close()

    release_token(token_socket) # 释放令牌

    return

# 登录
def signin(client_socket):
    client_socket.send("请输入用户名(输入#return#回到主菜单)：\n".encode("utf-8"))
    recv_str = client_socket.recv(1024).decode("utf-8") # 接收用户输入的用户名
    
    # 输入#return#返回主菜单
    if recv_str == "#return#":
        return
    
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    # 名字不存在后提醒输入
    while True:
        result = c.execute("SELECT * FROM PERSON WHERE NAME == '{}'".format(recv_str))
        # 查询后如果有这个用户名，那至少哟一个结果，说明len > 0
        if len(list(result)) > 0:
            client_socket.send(('登录成功！\n').encode("utf-8"))
            break
        # 没有用户名的话，提醒他重新输入
        else:
            client_socket.send(('该用户名不存在，请重新输入！\n').encode("utf-8"))
            recv_str = client_socket.recv(1024).decode("utf-8")
            
            if recv_str == "#return#":
                conn.close()
                return
    conn.close()

    # 登录成功的话进入机票业务菜单，同时把用户名作为参数传过去
    ticket_services(client_socket,recv_str)


# 登录和注册的主菜单
def major(client_socket):
    while True:
        client_socket.send("欢迎使用chenshf机票定制系统 ver 4.3.9.6 server2！\n".encode("utf-8"))
        client_socket.send("1.注册\n2.登录\n".encode("utf-8"))
        while True:
            recv_str = client_socket.recv(1024).decode("utf-8")
            if recv_str == "1":
                register(client_socket)
                break
            elif recv_str == "2":
                signin(client_socket)
                break
            else:
                client_socket.send("无效输入，请重新输入\n".encode("utf-8"))

# 提供的5种机票业务
def ticket_services(client_socket,name):
    while True:
        client_socket.send("以下是提供给您的几种服务:\n1.查询所有机票\n2.查询固定起点终点机票\n3.订制机票\n4.退订机票\n5.已订\n".encode("utf-8"))
        recv_str = client_socket.recv(1024).decode("utf-8")
        if recv_str == "1":
            search_all_ticket(client_socket) # 查询所有机票
        elif recv_str == "2":
            search_by_start_and_arrive(client_socket) # 查询固定起点终点机票
        elif recv_str == "3":
            buy_ticket(client_socket,name) # 订制机票
        elif recv_str == "4":
            return_ticket(client_socket,name) # 退订机票
        elif recv_str == "5":
            search_buyed(client_socket,name) # 查询已订
        else:
            client_socket.send("无效输入\n".encode("utf-8"))

# 对于查询到的结果进行格式化，方便用户查看
def formated_result(result):
    string = ""
    for row in result:
        new_row = []
        for col in row:
            new_row.append(str(col))
        string += '|'.join(new_row) + '\n'
    return string

# 查询所有机票
def search_all_ticket(client_socket):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    result = c.execute("select * from ticket")
    string = "ID|起点|终点|时间|余票\n" + formated_result(result)
    client_socket.send(string.encode("utf-8"))
    conn.close()

# 让用户输入起点和终点，查询对应机票
def search_by_start_and_arrive(client_socket):
    # %可以在数据库库查询里替代任意字符串，所以可以用%代替未知
    client_socket.send("请输入起点 终点，可用%代替未知：\n".encode("utf-8"))
    recv_str = client_socket.recv(1024).decode("utf-8") # 接收输入的起点和终点

    while True:
        try:
            start,arrive = recv_str.split(' ')
        except Exception as e:
            # 如果发生异常，说明用户随便输入，导致不能正确分割为2元素的元组
            # 提示其重新输入
            client_socket.send("无效输入,请重新输入！\n".encode("utf-8"))
            recv_str = client_socket.recv(1024).decode("utf-8")
        else:
            break

    # 利用起点和终点查询
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    result = c.execute("select * from ticket where start like '%{}%' and arrive like '%{}%'".format(start,arrive))
    string = "ID|起点|终点|时间|余票\n" + formated_result(result)
    client_socket.send(string.encode("utf-8"))
    conn.close()

# 订制机票
def buy_ticket(client_socket, name):
    client_socket.send("请输入机票id：\n".encode("utf-8"))
    recv_str = client_socket.recv(1024).decode("utf-8") # 接收用户输入的机票id

    token_socket = get_token() # 获取令牌，如果令牌被其他程序所有，则会阻塞

    conn = sqlite3.connect(filename) # 连接到数据库文件
    c = conn.cursor()
    
    try:
        c.execute("UPDATE TICKET set NUM = NUM-1 where ID={}".format(recv_str))
    except Exception as e:
        # 如果发生异常，说明NUM < 0 导致约束 check(num>=0)未被，说明机票卖完了
        client_socket.send("机票已经卖完\n".encode("utf-8"))
    else:
        # 如果没发生异常，但是数据库也没发生变化，说明用户输入了
        # 无效的机票id，没有更新任何对象，也不会发生错误
        if conn.total_changes == 0:
            client_socket.send("该机票id不存在\n".encode("utf-8"))
        else:
            # 没问题的话，考虑在 OWN关系 插入新值
            try:
                c.execute("INSERT INTO OWN VALUES ('{}',{})".format(name,recv_str))
            except Exception as e:
                # 发生异常的话，就是主键重复，说明该用户已经订过这种机票
                client_socket.send("请不要重复订机票\n".encode("utf-8"))
                conn.rollback()
            else:
                # 没有错误说明可以购买，这时候向另一个server发送vote-request，如果没问题的话，就提交到数据库
                vote_result = vote_request(the_other_side_ip,the_other_side_consistency_port,'command buy {} {}'.format(name,recv_str))
                if vote_result == "global_commit":
                    conn.commit()
                    client_socket.send("订票成功\n".encode("utf-8"))
                else:
                    conn.rollback()
                    client_socket.send(('发生未知错误，请联系管理员。\n').encode("utf-8"))

    conn.close()

    release_token(token_socket)

# 查询已经订过的机票
def search_buyed(client_socket, name):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    result = c.execute("SELECT NAME,ID,START,ARRIVE,TIME FROM OWN,TICKET WHERE NAME='{}' AND ID=TIKID".format(name))
    string = "NAME|ID|起点|终点|时间\n" + formated_result(result)
    client_socket.send(string.encode("utf-8"))
    conn.close()

# 退票
def return_ticket(client_socket, name):
    search_buyed(client_socket,name)
    client_socket.send("请输入退订的机票的ID\n".encode("utf-8"))
    recv_str = client_socket.recv(1024).decode("utf-8") # 接收用户输入的机票id

    token_socket = get_token() # 获取令牌，如果令牌被其他程序所有，则会阻塞

    conn = sqlite3.connect(filename) # 连接到数据库文件
    c = conn.cursor()
    
    c.execute("SELECT * FROM OWN WHERE NAME='{}' AND TIKID={}".format(name,recv_str))

    # 如果数据库没发生变化，说明用户输入了
    # 无效的机票id，没有查询任何对象，也不会发生错误
    if len(c.fetchall()) == 0:
         client_socket.send("请输入正确的ID\n".encode("utf-8"))
    else:
        # 没问题的话做数据库操作
        c.execute("DELETE FROM OWN WHERE NAME='{}' AND TIKID={}".format(name,recv_str))
        c.execute("UPDATE TICKET set NUM = NUM+1 where ID={}".format(recv_str))

        # 没有错误说明可以退订，这时候向另一个server发送vote-request，如果没问题的话，就提交到数据库
        vote_result = vote_request(the_other_side_ip,the_other_side_consistency_port,'command return {} {}'.format(name,recv_str))
        if vote_result == "global_commit":
            conn.commit()
            client_socket.send("退票成功\n".encode("utf-8"))
        else:
            conn.rollback()
            client_socket.send(('发生未知错误，请联系管理员。\n').encode("utf-8"))

    conn.close()

    release_token(token_socket)

def main():
    # 建立线程监听来自另一个服务器的命令
    _thread.start_new_thread(receive_command,(filename,consistency_port))
    
    # 建立tcp连接，绑定对应端口
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    addr = ("", service_port)
    tcp_server_socket.bind(addr)

    # 监听多个client发出的请求
    tcp_server_socket.listen(10)

    while True:
        # 对于每个connect，建立一个线程处理
        client_socket, client_addr = tcp_server_socket.accept()
        _thread.start_new_thread(major,(client_socket,))
 
    tcp_server_socket.close()


if __name__ == "__main__":
        main()