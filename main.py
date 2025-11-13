from pydantic import BaseModel
import psycopg2
import os
import sqlite3
import telebot
from openai import OpenAI
import random

conn = psycopg2.connect(
    dbname="python",
    user="postgres",
    password="1324",
    host="localhost",
    port="5432"
)
with open('token.txt', 'r', encoding='utf-8') as token:
    token = token.read()
    bot = telebot.TeleBot(token)


user_data = {}
class Book(BaseModel):
    id: int
    title: str
    author: str
    year: int
books = [
    Book(id = 1, title='Три товарища', author='Эрих Мария Ремарк', year=1945),
    Book(id = 2, title='Белые ночи', author='Достоевский', year=1967)
]


book1 = Book(id = 3, title='Герой нашего времени', author='Лермонтов', year=1845)
from fastapi import FastAPI

cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INT,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100),
    year INTEGER
);""")

app = FastAPI()
@app.get('/')
def read_root():
    return {'message': 'Virtual Library' }

@app.get('/books')
def get_books():
    return books

@app.get('/books/do2000')
def get_books_by_year():
    return [book for book in books if book.year < 2000]

@app.get('/books/posle2000')
def get_books_year():
    list3 = []
    for book in books:
        if int(book.year) > 2000:
            list3.append(book)
    return list3
    return {'error': 'Book not found'}
@app.get('/books/author')
def get_books_by_author(author: str):
    list2 = []
    for book in books:
        if book.author == author:
            list2.append(book)
    return list2
    return {'error': 'Book not found'}

@app.get('/books/{book_id}')
def get_book(book_id: int):
        for book in books:
            if book.id == book_id:
                return book
        return {'error': 'Book not found'}
@app.post('/books')
def add_book(id: int, title: str, author: str, year: int):
    book = Book(id=id, title=title, author=author, year=year)
    books.append(book)
    cur.execute('INSERT INTO books (id, title, author, year) VALUES (%s, %s, %s, %s);',(book.id, book.title, book.author, book.year))
    conn.commit()
    return {'message': 'Book added', 'book': book1}
@app.get('/credits')
def get_credits():
    return {'author': 'Mansur'}
@app.delete('/books/{book_id}')
def delete_book(book_id: int):
    for book in books:
        if book.id == book_id:
            books.remove(book)
            cur.execute('DELETE FROM books WHERE id = %s;',(book_id,))
            conn.commit()
            return {'message': 'Book deleted', '    book': book}
    return {'error': 'Book not found'}
@app.post('/books/{book_id}')
def update_book(book_id: int, title: str, author: str, year: str):
    for book in books:
        if book.id == book_id:
            if title != '-':
                book.title = title
                cur.execute('UPDATE books SET title = %s WHERE id = %s;', (title, book_id))
                conn.commit()
            if author != '-':
                book.author = author
                cur.execute('UPDATE books SET author = %s WHERE id = %s;', (author, book_id))
                conn.commit()
            if year != '-':
                book.year = year
                cur.execute('UPDATE books SET year = %s WHERE id = %s;', (int(year), book_id))
                conn.commit()
            return {'message': 'Book updated', 'book': book}
    return {'error': 'Book not found'}


with open("token.txt", "r", encoding="utf-8") as f:
    token = f.read().strip()
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "Вот что я могу:\n"
        "/books\n"
        "/author\n"
        "/years\n"
        "/prokat\n"
        "/available\n"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['books'])
def show_books(message):
    cur.execute("SELECT id, title, author, year, is_rented FROM books;")
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Библиотека пуста")
        return
    text = "\n".join([f"{r[0]} {r[1]} {r[2]} {r[3]}" for r in rows])
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['author'])
def by_author(message):
        author = " ".join(message.text.split()[1:])
        cur.execute("SELECT id, title, year FROM books WHERE author ILIKE %s;", (author,))
        rows = cur.fetchall()
        if not rows:
            bot.send_message(message.chat.id, f"Книг автора '{author}' не найдено.")
            return
        text = "\n".join([f"{r[0]} {r[1]} {r[2]}" for r in rows])
        bot.send_message(message.chat.id, text)



@bot.message_handler(commands=['years'])
def by_years(message):
        year, start, end = message.text.split()
        start, end = int(start), int(end)
        cur.execute("SELECT id, title, author, year FROM books WHERE year BETWEEN %s AND %s;", (start, end))
        rows = cur.fetchall()
        if not rows:
            bot.send_message(message.chat.id, "не найдено")
            return
        text = "\n".join([f"{r[0]} {r[1]} {r[2]} {r[3]}" for r in rows])
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['prokat'])
def rent_book(message):
        book_id = int(message.text.split()[1])
        cur.execute("SELECT is_rented FROM books WHERE id = %s;", (book_id,))
        res = cur.fetchone()
        if res[0]:
            bot.send_message(message.chat.id, "Книга недоступна к прокату")
            return
        cur.execute("UPDATE books SET is_rented = TRUE WHERE id = %s;", (book_id,))
        conn.commit()
        bot.send_message(message.chat.id, f"Книга взята на прокат")


@bot.message_handler(commands=['available'])
def available_books(message):
    cur.execute("SELECT id, title, author, year FROM books WHERE is_rented = FALSE;")
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Нет доступных книг к прокату")
        return
    text = "\n".join([f"{r[0]} {r[1]} {r[2]} {r[3]}" for r in rows])
    bot.send_message(message.chat.id, text)





with open('openrouter.txt', 'r') as f:
    token1 = f.read()
client = OpenAI(api_key=token1, base_url="https://openrouter.ai/api/v1/")
cur.execute("SELECT id, title, author, year FROM books")
books3 = cur.fetchall()
system_promt = {"role": "system", "content": [f"{books3}, это список книг, ты можешь советовать или рассказывать что либо о них", ]}

@bot.message_handler(commands=['ai'])
def ai_chatid(message):
    bot.send_message(message.chat.id, 'Начало ии чата:')
    user_data[message.chat.id] = []
    bot.register_next_step_handler(message, ai_chat)
def ai_chat(message):
    chat_id = message.chat.id
    if message.text.strip().lower() == "exit":
        bot.send_message(message.chat.id, "Конец ИИ чата")
        user_data.pop(chat_id, None)
        return
    user_data[chat_id].append(message.text)
    user_input = message.text
    response = client.chat.completions.create(
        model="openrouter/auto",
        messages=[system_promt, {"role": "user", "content": user_input}]
    )
    bot.send_message(message.chat.id, response.choices[0].message.content)
    bot.register_next_step_handler(message, ai_chat)


@bot.message_handler(commands=['echo'])
def echo_message(message):
    bot.send_message(message.chat.id, f'Повторю твой текст как: "{message.text}"')
    user_data[message.chat.id] = []
    bot.register_next_step_handler(message, echoing)

def echoing(message):
    chat_id = message.chat.id
    if message.text.strip().lower() == '/done':
        bot.send_message(chat_id, 'Эхо остановлено')
        print(user_data)
        user_data.pop(chat_id, None)
        return

    user_data[chat_id].append(message.text)
    bot.send_message(chat_id, f'Эхо: "{message.text}"')
    bot.register_next_step_handler(message, echoing)
@bot.message_handler(commands=['aibehavior'])
def aibehavior(message):
    user_input = message.text
    system_promt["content"] += f"\n{user_input}"
    bot.send_message(message.chat.id, 'успешно изменили настройки поведения')


from PyQt5 import QtCore, QtGui, QtWidgets
import random


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(626, 692)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.random = QtWidgets.QPushButton(self.centralwidget)
        self.random.setGeometry(QtCore.QRect(20, 10, 141, 34))
        self.random.setObjectName("random")
        self.randomline = QtWidgets.QLabel(self.centralwidget)
        self.randomline.setGeometry(QtCore.QRect(30, 60, 208, 18))
        self.randomline.setObjectName("randomline")
        self.author = QtWidgets.QPushButton(self.centralwidget)
        self.author.setGeometry(QtCore.QRect(20, 100, 141, 34))
        self.author.setObjectName("author")
        self.authorline = QtWidgets.QLineEdit(self.centralwidget)
        self.authorline.setGeometry(QtCore.QRect(180, 100, 113, 32))
        self.authorline.setObjectName("authorline")
        self.year = QtWidgets.QPushButton(self.centralwidget)
        self.year.setGeometry(QtCore.QRect(330, 100, 121, 34))
        self.year.setObjectName("year")
        self.yearline = QtWidgets.QLineEdit(self.centralwidget)
        self.yearline.setGeometry(QtCore.QRect(470, 100, 131, 32))
        self.yearline.setObjectName("yearline")
        self.authobrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.authobrowser.setGeometry(QtCore.QRect(20, 150, 256, 201))
        self.authobrowser.setObjectName("authobrowser")
        self.yearbrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.yearbrowser.setGeometry(QtCore.QRect(330, 150, 256, 201))
        self.yearbrowser.setObjectName("yearbrowser")
        self.random_prokat = QtWidgets.QPushButton(self.centralwidget)
        self.random_prokat.setGeometry(QtCore.QRect(330, 10, 221, 34))
        self.random_prokat.setObjectName("random_prokat")
        self.random_prokatline = QtWidgets.QLabel(self.centralwidget)
        self.random_prokatline.setGeometry(QtCore.QRect(340, 60, 68, 18))
        self.random_prokatline.setObjectName("random_prokatline")
        self.availabletext = QtWidgets.QLabel(self.centralwidget)
        self.availabletext.setGeometry(QtCore.QRect(30, 370, 181, 18))
        self.availabletext.setObjectName("availabletext")
        self.btn_prokat = QtWidgets.QPushButton(self.centralwidget)
        self.btn_prokat.setGeometry(QtCore.QRect(330, 490, 121, 34))
        self.btn_prokat.setObjectName("btn_prokat")
        self.btn_prokatline = QtWidgets.QLineEdit(self.centralwidget)
        self.btn_prokatline.setGeometry(QtCore.QRect(470, 490, 113, 32))
        self.btn_prokatline.setObjectName("btn_prokatline")
        self.availablebrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.availablebrowser.setGeometry(QtCore.QRect(20, 410, 256, 200))
        self.availablebrowser.setObjectName("availablebrowser")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 626, 28))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        cur.execute("SELECT title FROM books")
        self.books = cur.fetchall()
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.random.clicked.connect(self.random_book_clicked)
        self.random_prokat.clicked.connect(self.random_book_prokat_clicked)
        self.author.clicked.connect(self.book_by_author)
        self.year.clicked.connect(self.book_by_year)
        self.btn_prokat.clicked.connect(self.take_book)
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.random.setText(_translate("MainWindow", "Случайная книга"))
        self.randomline.setText(_translate("MainWindow", "....."))
        self.author.setText(_translate("MainWindow", "Книги по автору"))
        self.year.setText(_translate("MainWindow", "Книги по году"))
        self.authobrowser.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:\'Rubik\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.yearbrowser.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:\'Rubik\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.random_prokat.setText(_translate("MainWindow", "Случайная книга на прокате"))
        self.random_prokatline.setText(_translate("MainWindow", "....."))
        self.availabletext.setText(_translate("MainWindow", "Список доступных книг"))
        self.btn_prokat.setText(_translate("MainWindow", "Забрать книгу"))
        self.availablebrowser.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:\'Rubik\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        cur.execute(f"SELECT id, title, author FROM books WHERE is_rented = false;;")
        self.books = cur.fetchall()
        for book in self.books:
            book1 = str(book).replace("'", ' ')
            book1 = book1.replace('(', '')
            self.availablebrowser.append(f"ID: {str(book).replace(")", "")}")
    def random_book_clicked(self):
        cur.execute(f"SELECT id, title, author FROM books WHERE is_rented = false;;")
        self.books1 = cur.fetchall()
        self.book = random.choice(self.books1)
        self.randomline.setText(str(self.book))

    def random_book_prokat_clicked(self):
        cur.execute("SELECT * FROM books WHERE is_rented = false")
        self.book = cur.fetchall()
        self.book1 = random.choice(self.book)
        self.random_prokatline.setText(str(self.book1))
    def book_by_author(self):
        cur.execute(f"SELECT title, author FROM books WHERE author = '{self.authorline.text()}';")
        self.books = cur.fetchall()
        self.list2 = []
        self.list2.append(self.books)
        self.authobrowser.setText(str(self.list2))

    def book_by_year(self):
        cur.execute(f"SELECT title, author, is_rented FROM books WHERE year = '{self.yearline.text()}';")
        self.books = cur.fetchall()
        self.list2 = []
        self.list2.append(self.books)
        self.yearbrowser.setText(str(self.list2))
    def take_book(self):
        cur.execute("UPDATE books SET is_rented = true WHERE id = %s;", (self.btn_prokatline.text(),))
        cur.execute(f"SELECT id, title, author FROM books WHERE is_rented = false;")
        self.books = cur.fetchall()
        self.availablebrowser.setText(str(self.books))






if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())




bot.polling()