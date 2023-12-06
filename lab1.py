from tkinter import *
from serial import *
import threading

global port
global curnumber
global baudrate
global recv_thread
global finish
global started

# Создаем главное окно
root = Tk()
root.geometry("585x460")
root.resizable(False, False)
root.title("Lab1")
root.configure(bg="light blue")

def close_frame(frame):
  frame.destroy()

# Открытие порта по умолчанию
def on_start():
  global port
  global curnumber
  global recv_thread
  global started
  global baudrate
  started = 0
  curnumber = 0
  baudrate = -1
  for j in range(1, 11):
    if(check_port_av(j)):
      curnumber = j
      com_var.set(curnumber)
      port = open_port(curnumber)
      started = 1
      return
  top_frame = Frame(root, bg="blue", padx=10, pady=5)
  top_frame.grid(row=0, column=1, padx=10, pady=5)
  Label(top_frame, text="Error", bg="cyan").pack(pady=(10, 0))
  Label(top_frame, text="No Available Ports", bg="cyan").pack(pady=(10, 0))
  close_button = Button(top_frame, text="OK", bg="cyan", command=lambda: close_frame(top_frame))
  close_button.pack(pady=(10, 0))

# Завершение программы
def on_closing():
  global port
  global recv_thread
  global finish
  finish = 0
  try:
    close_port(port)
    recv_thread.join
  except Exception:
    pass
  root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Открытие COM-порта
def open_port(port_number):
  global started
  global recv_thread
  global port
  if(check_port_av(port_number)):
    port = Serial(f"COM{port_number}", 9600, int(bits_var.get()))
    port.timeout = 0.1
  if started == 0:
    started = 1
    recv_thread = threading.Thread(target=rec_data)
    recv_thread.start()
  return port

# Закрытие COM-порта
def close_port(ser):
  if ser.is_open:
    ser.close()

# Изменение COM-порта
def chport(*args):
  global port
  global curnumber
  if(check_port_av(com_var.get())):
    try:
      close_port(port)
    except Exception:
      pass
    port = open_port(com_var.get())
    curnumber = com_var.get()
  else:
    failnum = com_var.get()
    if(curnumber != 0): com_var.set(curnumber)
    else: com_var.set("1")
    top_frame = Frame(root, bg="blue", padx=10, pady=5)
    top_frame.grid(row=0, column=1, padx=10, pady=10)
    Label(top_frame, text="Error", bg="cyan").pack(pady=(10, 0))
    Label(top_frame, text="Port {} is unavailable!".format(failnum), bg="cyan").pack(pady=(10, 0))
    close_button = Button(top_frame, text="OK", bg="cyan", command=lambda: close_frame(top_frame))
    close_button.pack(pady=(10, 0))

# Изменение количества битов в байте
def chbyte(*args):
  global port
  global started
  if(started):
    if int(bits_var.get()) == 5:
      port.bytesize = FIVEBITS
    elif int(bits_var.get()) == 6:
      port.bytesize = SIXBITS
    elif int(bits_var.get()) == 7:
      port.bytesize = SEVENBITS
    elif int(bits_var.get()) == 8:
      port.bytesize = EIGHTBITS

# Отправка символов через COM-порт
def send_data(event):
  global port
  global started
  cursor_position = input_text.index("insert")
  if input_text.index("end-1c") != cursor_position:
    input_text.insert("insert", "\n")
  text = input_text.get("1.0", "end")
  if input_text.index("end-1c") != cursor_position:
    input_text.delete("insert-1c")
  if(started == 1): 
    port.write(text.encode('cp1251'))
    update_state(len(text))
    
# Получение символов через COM-порт
def rec_data():
  global finish
  finish = 1
  rec_end = 0
  text = ""
  printed = False
  while True:
    try:
      symbol = port.read().decode('cp1251')
      if(finish == 0): return
      if(symbol):
        if(rec_end == 1):
          text = ""
          printed = False
          output_text.config(state=NORMAL)
          output_text.delete("1.0", "end")
          output_text.config(state=DISABLED)
        rec_end = 0
        text = text + symbol
      else:
        rec_end = 1
        if(printed == False):
          output_text.config(state=NORMAL)
          output_text.insert("1.0", text)
          output_text.config(state=DISABLED)
          printed = True
    except Exception:
          pass

# Проверка, доступен ли COM-порт
def check_port_av(number):
      try:
          cport = "COM" + str(number)
          ser = Serial(cport)
          ser.close()
          return True
      except Exception:
          return False
        
# Обновление окна состояния
def update_state(number):
  global baudrate
  state_text.config(state=NORMAL)
  state_text.delete('1.0', END)
  if(baudrate < 0):
    state_text.delete('1.0', END)
    try:
      baudrate = port.baudrate
      state_text.insert(END, "Speed: {}\n".format(baudrate))
    except Exception:
      state_text.insert(END, "Speed: N/A\n")
      baudrate = -1
  else:
    state_text.insert(END, "Speed: {}\n".format(baudrate))
  state_text.insert(END, "Bytes sent: {}".format(number))
  state_text.config(state=DISABLED)

#########################################################

# Создание графического интерфейса
input_frame = Frame(root, bg="white", padx=10, pady=10)
input_frame.grid(row=0, column=0, padx=10, pady=10)
Label(input_frame, text="Input").pack()
input_text = Text(input_frame, width=30, height=10)
input_text.pack(side=LEFT)
input_scrollbar = Scrollbar(input_frame)
input_scrollbar.pack(side=RIGHT, fill=Y)
input_text.config(yscrollcommand=input_scrollbar.set)
input_scrollbar.config(command=input_text.yview)
input_text.bind("<Return>", send_data)
control_frame = Frame(root, bg="white", padx=60, pady=25)
control_frame.grid(row=0, column=1, padx=10, pady=10)
Label(control_frame, text="Control").pack()

com_var = StringVar(control_frame)
com_var.set("1")
bits_var = StringVar(control_frame)
bits_var.set("8")

com_label = Label(control_frame, text="COM port number")
com_label.pack(pady=(25, 0))
com_menu = OptionMenu(control_frame, com_var, "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", command=chport)
com_menu.pack()

bits_label = Label(control_frame, text="Bits in a byte")
bits_label.pack()
bits_menu = OptionMenu(control_frame, bits_var, "5", "6", "7", "8", command=chbyte)
bits_menu.pack()

output_frame = Frame(root, bg="white", padx=10, pady=10)
output_frame.grid(row=1, column=0, padx=10, pady=10)
Label(output_frame, text="Output").pack()
output_text = Text(output_frame, width=30, height=10, state=DISABLED)
output_text.pack(side=LEFT)
output_scrollbar = Scrollbar(output_frame)
output_scrollbar.pack(side=RIGHT, fill=Y)
output_text.config(yscrollcommand=output_scrollbar.set)
output_scrollbar.config(command=output_text.yview)

state_frame = Frame(root, bg="white", padx=10, pady=10)
state_frame.grid(row=1, column=1, padx=10, pady=10)
Label(state_frame, text="State").pack()
state_text = Text(state_frame, width=30, height=10, state=DISABLED)
state_text.pack()

on_start()
update_state(0)
  
# Запускаем цикл обработки событий
root.mainloop()
