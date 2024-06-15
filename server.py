import json
import socket
import sys
import threading
from collections import defaultdict
# 通讯协议命令
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QApplication, QHBoxLayout, QLayout, QLineEdit

COMMAND_HEARTBEAT = "HB"
COMMAND_DATA = "DT"
COMMAND_ONLINE = "ON"
COMMAND_OFFLINE = "OF"

next_HostNumber=0

from datetime import datetime




def next_number():
    global next_HostNumber
    next_HostNumber+=1
    return f"{next_HostNumber:02d}"


data_storage = {}
t=None
class Server_sock():
    def __init__(self,serverUI):
        self.serverUI=serverUI
        global t
        t=threading.Thread(target=self.main)
        t.start()

    def handle_client(self,client_socket, client_address, data_storage):
        while True:
            try:
                rev_data = client_socket.recv(1024).decode()
            except (socket.timeout,ConnectionResetError):
                rev_data = 'EF'  # 超时后返回EF数据  作为超时信号
            datas=rev_data[4:].split('$',1)
            sign_data = rev_data[:2]
            hostNumber= rev_data[2:4]

            if sign_data==COMMAND_ONLINE:
                if hostNumber == '00':
                    hostNumber=next_number()
                if hostNumber in data_storage:
                    data_storage[hostNumber][0] = 'ON'
                else:
                    data_storage[hostNumber] = ['ON', ]
                src = COMMAND_ONLINE + hostNumber + '$'
                client_socket.send(src.encode())
                self.serverUI.send_data_edit2.setText(f"连接主机号 {hostNumber}")
                print(f"Connection from {hostNumber}")
            elif sign_data==COMMAND_HEARTBEAT:
                src = COMMAND_HEARTBEAT +hostNumber +'$'
                client_socket.send(src.encode())
            elif sign_data==COMMAND_DATA:
                t = eval(str(datas[0]))
                d1 = t['temperature']
                d2 = t['humidity']
                p = [d1, d2]
                if hostNumber not in data_storage:
                    data_storage[hostNumber]=['ON',p,]
                    self.serverUI.send_data_edit2.setText(f"连接主机号 {hostNumber}")
                else:

                    data_storage[hostNumber] = data_storage[hostNumber]+[p]
                if hostNumber in data_storage:
                     data_storage[hostNumber][0] = 'ON'
                     self.serverUI.send_data_edit2.setText(f"连接主机号{hostNumber}")
            elif sign_data==COMMAND_OFFLINE:
                print('有通知断开连接')
                client_socket.close()
                if hostNumber in data_storage:
                    data_storage[hostNumber][0]='OFF'
                self.serverUI.send_data_edit2.setText(f"有通知断开连接 {hostNumber}")
                break
            elif sign_data=='EF':
                client_socket.close()
                if hostNumber in data_storage:
                    data_storage[hostNumber][0] = 'OFF'
                self.serverUI.send_data_edit2.setText(f"无通知断开连接 {hostNumber}")
                break
                print('无通知断开连接')
            else:
                print(f'非法数据 {hostNumber}')



    def main(self):
        server_address = ('localhost', 10001)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(server_address)
        server_socket.listen(99)
        global data_storage


        while True:
            client_socket, client_address = server_socket.accept()
            client_socket.settimeout(2.1)  # 设置超时时间为2.1秒
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address, data_storage))
            client_thread.start()

isShow={}

class ServerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(400, 400, 450, 250)
        self.nowline=0
        self.setWindowTitle('服务器')
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        # 设置行高和列宽为最小值
        self.layout.setRowStretch(0, 0)
        self.layout.setColumnStretch(0, 0)

        self.init_ui()
        self.isOpen=False
        self.server=Server_sock(self)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.timer.start(1)

    def init_ui(self):
        sub_layout1 = QGridLayout()

        self.send_data_edit = QLabel('服务器已开启...')
        self.now_time = QLabel('')
        self.send_data_edit2 = QLabel('......')
        sub_layout1.addWidget(self.send_data_edit,0,0)
        sub_layout1.addWidget(self.now_time,0,1)
        sub_layout1.addWidget(self.send_data_edit2,1,0,1,2)
        self.layout.addLayout(sub_layout1,0,0,1,5)

        self.nowline +=1
        sub_layout = QGridLayout()
        sub_layout.setSizeConstraint(QLayout.SetFixedSize)

        online_label = QLabel('机号')


        online_label2 = QLabel('状态')


        online_label3 = QLabel('最新数据')

        b=QPushButton('save')
        b.clicked.connect(self.save)
        sub_layout.addWidget(online_label, self.nowline, 1)
        sub_layout.addWidget(online_label2, self.nowline, 2)
        sub_layout.addWidget(online_label3, self.nowline, 3, 1, 4)

        self.layout.addLayout(sub_layout, self.nowline, 0, 1, 4)




    def save(self):
        with open('w.json',mode='w',encoding='utf-8') as f:
            json.dumps(f)


    def check(self):
        # 获取当前时间
        now = datetime.now()

        # 格式化时间，精确到秒
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.now_time.setText(formatted_time)
        for i in data_storage.keys():
            key = i
            sign = data_storage[key][0]
            if len(data_storage[key])>1:
                data = data_storage[key][-1]
            else:
                data=['无','无']
            lis = [key, sign, data]
            if i not in isShow.keys():
                isShow[key]=self.online(key,sign,data)
            else:
                self.updata(isShow[key],lis)



    def online(self,key,sign,data):
        self.nowline+=1
        sub_layout = QGridLayout()
        sub_layout.setSizeConstraint(QLayout.SetFixedSize)

        online_label = QLabel(key)

        online_label2 = QLabel(sign)
        #online_label3 = QLabel(sign)

        online_label3 = QLabel(f'温度：{data[0]}，湿度：{data[1]}')

        sub_layout.addWidget(online_label, self.nowline, 1)
        sub_layout.addWidget(online_label2, self.nowline, 2)
        sub_layout.addWidget(online_label3, self.nowline, 3, 1, 4)
        self.layout.addLayout(sub_layout, self.nowline, 0, 1, 4)
        return [online_label,online_label2,online_label3]
    def updata(self,lis,data_lis):
        sign=data_lis[-2]
        if sign=='ON':
            lis[-2].setText('<font color="green">ON</font>')
        else:
            lis[-2].setText('<font color="red">OFF</font>')
        data=data_lis[-1]
        lis[-1].setText(f'温度：{data[0]}，湿度：{data[1]}')

    def closeEvent(self, event):
        self.offline()
        global t
        t.join(1)
        event.accept()





if __name__ == "__main__":
    app = QApplication(sys.argv)
    serverui=ServerUI()
    serverui.show()
    #serverui.server.main()
    sys.exit(app.exec_())