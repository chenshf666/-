import sqlite3
import random

def init_file():
	filename = 'database.db'
	f = open('database.db','w')
	f.close()
	return filename

# sqlite3.IntegrityError
def create_table(filename):
	conn = sqlite3.connect(filename)
	print("Opened database successfully")
	c = conn.cursor()
	c.execute('''CREATE TABLE TICKET
	       (ID INT PRIMARY KEY     NOT NULL,
	       START        CHAR(50),
	       ARRIVE       CHAR(50),
	       TIME 		CHAR(50),
	       NUM 			INT CHECK (NUM >= 0));''')
	
	c.execute('''CREATE TABLE PERSON
	       (NAME CHAR(50) PRIMARY KEY NOT NULL);''')

	c.execute('''CREATE TABLE OWN
	       (NAME CHAR(50) not null,
	       TIKID INT not null,
	       FOREIGN KEY(NAME) REFERENCES PERSON(NAME),
	       FOREIGN KEY(TIKID) REFERENCES TICKET(ID),
	       PRIMARY KEY(NAME,TIKID));''')
	print("Table created successfully")
	conn.commit()
	conn.close()

def choose_two_provinces(provinces):
	start = random.choice(provinces)
	arrive = random.choice(provinces)
	while arrive == start:
		arrive = random.choice(provinces)
	return start,arrive

def insert_values(filename,provinces,num=50):
	conn = sqlite3.connect(filename)
	c = conn.cursor()
	for i in range(1,num+1,3):
		s,a = choose_two_provinces(provinces)
		_id = i
		for time in range(3):
			num = random.randint(3,10)
			c.execute("INSERT INTO TICKET (ID,START,ARRIVE,TIME,NUM) \
      			VALUES ({}, '{}', '{}',{},{})".format(_id+time,s,a,time,num));
	conn.commit()
	conn.close()

def show_values(filename):
	conn = sqlite3.connect(filename)
	c = conn.cursor()
	result = c.execute('select * from ticket')
	for r in result:
		print(r)
	conn.commit()
	conn.close()

def main():
	province_str = '北京市，天津市，上海市，重庆市，河北省，山西省，辽宁省，吉林省，黑龙江省，江苏省，浙江省，安徽省，福建省，江西省，山东省，河南省，湖北省，湖南省，广东省，海南省，四川省，贵州省，云南省，陕西省，甘肃省，青海省，台湾省，内蒙古自治区，广西壮族自治区，西藏自治区，宁夏回族自治区，新疆维吾尔自治区，香港'
	provinces = province_str.split('，')
	filename = init_file()
	create_table(filename)
	insert_values(filename,provinces,20)
	show_values(filename)

if __name__ == '__main__':
	main()