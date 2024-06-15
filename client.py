import random
import sys
import threading

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QGridLayout, \
    QMessageBox, QDialog
import socket
import random
import time

# 通讯协议命令
COMMAND_HEARTBEAT = "HB"
COMMAND_DATA = "DT"
COMMAND_ONLINE = "ON"
COMMAND_OFFLINE = "OF"


HostNumber= "00"



class Client_sock():
    def __init__(self,edit_text,online_label,ui):
        self.server_address = ('localhost', 10001)
        #self.sock.connect(server_address)
        self.edit_text=edit_text
        self.online_label=online_label
        self.ui=ui
        self.isOn = False
        self.isNeed = False
    def Online(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2.1)  # 设置超时时间为2.1秒
        client_socket = self.sock
        try:
            client_socket.connect(self.server_address)
        except (ConnectionResetError, ConnectionRefusedError) as f:
            print(f)
            self.ui.show_dialog('服务器不在线')
        heart_thread = threading.Thread(target=self.heart, args=(client_socket, ))
        heart_thread.start()

    def generate_data(self):
        data=str({"temperature": round(random.uniform(20, 30), 2), "humidity":  round(random.uniform(40, 60),2)})
        self.edit_text.setText(data)

    def send_data2(self, sign,data):
        srs= sign + HostNumber + data + '$'
        self.sock.send(srs.encode())

    def send_data(self, sign):
        srs= sign + str(HostNumber) + '$'
        self.sock.send(srs.encode())


    def Offline(self):
        self.isOn = False
        self.isNeed = True




    def heart(self,client_socket):
        i = 0
        while i < 4:
            try:
                if self.isNeed == True:
                    self.isNeed=False
                    self.send_data(COMMAND_OFFLINE)
                    self.sock.close()
                    print('线程断开')

                    break
                if not self.isOn:
                    self.send_data(COMMAND_ONLINE)
                    i += 1

                rev_data = client_socket.recv(1024).decode()
            except (socket.timeout,ConnectionResetError) as f:
                rev_data = 'EF'  # 超时后返回EF数据  作为超时信号
            print(rev_data)
            sign_data = rev_data[:2]
            # 确认登入
            if sign_data == COMMAND_ONLINE:
                self.isOn = True
                if len(rev_data)>3 and '$' in rev_data:
                    global HostNumber
                    # 设立主机号
                    HostNumber= rev_data.split('$')[0][2:4]
                self.online_label.setText('在线状态：<font color="green">在线</font>')
                self.send_data(COMMAND_HEARTBEAT)
            # 心跳响应
            elif sign_data == COMMAND_HEARTBEAT:
                self.ui.online_label2.setText(f'主机号:{HostNumber}')
                self.send_data(COMMAND_HEARTBEAT)
            # 确认离线
            elif sign_data == COMMAND_OFFLINE:
                print('有通知断开连接')
                self.isOn = False
                self.online_label.setText('在线状态：<font color="red">离线</font>')
                break
            # 无响应
            elif rev_data == 'EF':
                self.isOn= False
                self.online_label.setText('在线状态：<font color="red">离线</font>')
                print('无通知断开连接或主机不在线')
                break
            else:
                print('非法数据')
            time.sleep(1)

class ClientUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(400, 400, 540, 250)
        self.init_ui()
        self.client_sock=Client_sock(self.send_data_edit, self.online_label,self)
        self.isAuto=False

        self.timer = QTimer()
        self.timer.timeout.connect(self.isAutoSend)
        self.timer.start(2000)  # 每隔1秒检查一次状态

    def init_ui(self):
        self.setWindowTitle('客户端')

        layout = QGridLayout()

        self.online_label = QLabel('在线状态：<font color="red">离线</font>')
        layout.addWidget(self.online_label,0,0)

        self.online_label2 = QLabel('主机号:')
        layout.addWidget(self.online_label2, 0, 1)

        self.online_button = QPushButton('上线')
        self.online_button.clicked.connect(self.online)
        layout.addWidget(self.online_button,1,0)

        self.offline_button = QPushButton('下线')
        self.offline_button.clicked.connect(self.offline)
        layout.addWidget(self.offline_button,1,1)



        self.send_button = QPushButton('发送数据')
        self.send_button.clicked.connect(self.ui_send_data)
        layout.addWidget(self.send_button,2,0)

        self.generate_data_button = QPushButton('生成数据')
        self.generate_data_button.clicked.connect(self.generate_data)
        layout.addWidget(self.generate_data_button,2,1)

        self.auto_button = QPushButton('自动生成数据并发送')
        self.auto_button.clicked.connect(self.auto_send)
        layout.addWidget(self.auto_button, 3, 0,1,2)

        self.send_data_edit = QLineEdit()
        layout.addWidget(self.send_data_edit, 4, 0,1,2)

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit,5,0,1,2)

        self.setLayout(layout)


    def isAutoSend(self):
        if self.isAuto:
            self.generate_data()
            self.ui_send_data()

    def auto_send(self):
        self.isAuto=not self.isAuto

    def online(self):
        self.client_sock.Online()

    def offline(self):
        self.online_label.setText('在线状态：<font color="red">离线</font>')
        self.client_sock.Offline()

    def ui_send_data(self):
        # 在这里处理发送数据的逻辑
        data=self.send_data_edit.text()
        if self.client_sock.isOn:
            self.text_edit.append('已发送:'+str(data))
            self.client_sock.send_data2('DT',data)
        else:
           self.show_dialog('please online')

    def generate_data(self):
        # 在这里处理生成数据的逻辑
        self.client_sock.generate_data()

    def closeEvent(self, event):
        self.offline()
        event.accept()

    def show_dialog(self,text):
        # 创建一个非模态对话框
        dialog = QDialog(self)
        dialog.setWindowTitle('Notice')

        layout = QVBoxLayout(dialog)
        message_label = QLabel(text)
        layout.addWidget(message_label)

        ok_button = QPushButton('YES', dialog)
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)

        # 创建定时器
        timer = QTimer(dialog)
        timer.setSingleShot(True)  # 设置为单次触发
        timer.timeout.connect(dialog.accept)  # 连接定时器的超时信号到对话框的 accept 方法
        timer.start(1000)  # 设置定时器超时时间为1000毫秒（1秒）并启动定时器

        # 显示对话框
        dialog.show()

def mainAction():
    app = QApplication(sys.argv)
    client_ui = ClientUI()
    client_ui.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    mainAction()
