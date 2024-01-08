import math
import time
from tkinter import *
from serial import *
import threading
import random

global port
global curnumber
global baudrate
global recv_thread
global finish
global started
global lastnumber
global coll_stat

# Создаем главное окно
root = Tk()
root.geometry("585x460")
root.resizable(False, False)
root.title("Lab4")
root.configure(bg="light blue")


# Обработка ввода
def validate_data(event):
    key = event.char
    if key in ["0", "1", "\r"]:
        cursor_pos = input_text.index(INSERT)
        input_text.insert(cursor_pos, key)
    elif key == "\b":
        input_text.delete(END - 1)
    return "break"


def close_frame(frame):
    frame.destroy()


# Открытие порта по умолчанию
def on_start():
    global port
    global curnumber
    global recv_thread
    global started
    global baudrate
    global coll_stat
    started = 0
    curnumber = 0
    baudrate = -1
    coll_stat = ""
    for j in range(1, 11):
        if check_port_av(j):
            curnumber = j
            com_var.set(curnumber)
            port = open_port(curnumber)
            started = 1
            return
    top_frame = Frame(root, bg="blue", padx=10, pady=5)
    top_frame.grid(row=0, column=1, padx=10, pady=5)
    Label(top_frame, text="Error", bg="cyan").pack(pady=(10, 0))
    Label(top_frame, text="No Available Ports", bg="cyan").pack(pady=(10, 0))
    close_button = Button(
        top_frame, text="OK", bg="cyan", command=lambda: close_frame(top_frame)
    )
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
    if check_port_av(port_number):
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
    if check_port_av(com_var.get()):
        try:
            close_port(port)
        except Exception:
            pass
        port = open_port(com_var.get())
        curnumber = com_var.get()
    else:
        failnum = com_var.get()
        if curnumber != 0:
            com_var.set(curnumber)
        else:
            com_var.set("1")
        top_frame = Frame(root, bg="blue", padx=10, pady=5)
        top_frame.grid(row=0, column=1, padx=10, pady=10)
        Label(top_frame, text="Error", bg="cyan").pack(pady=(10, 0))
        Label(
            top_frame, text="Port {} is unavailable!".format(failnum), bg="cyan"
        ).pack(pady=(10, 0))
        close_button = Button(
            top_frame, text="OK", bg="cyan", command=lambda: close_frame(top_frame)
        )
        close_button.pack(pady=(10, 0))


# Изменение количества битов в байте
def chbyte(*args):
    global port
    global started
    if started:
        if int(bits_var.get()) == 5:
            port.bytesize = FIVEBITS
        elif int(bits_var.get()) == 6:
            port.bytesize = SIXBITS
        elif int(bits_var.get()) == 7:
            port.bytesize = SEVENBITS
        elif int(bits_var.get()) == 8:
            port.bytesize = EIGHTBITS


# Разделение стрки на подстроки
def split_string(string):
    result = []
    for i in range(0, len(string), 3):
        if i + 3 <= len(string):
            result.append(string[i : i + 3])
        else:
            result.append(string[i:] + "x" * (3 - len(string[i:])))
    return result


# Преобразование числа в двоичное представление
def binary_string(num):
    bin_num = bin(num)[2:]
    num_zeros = 4 - len(bin_num)
    bin_string = "0" * num_zeros + bin_num
    return bin_string


# Бит-стаффинг
def bitStuffing(data):
    stuffed: str = ""
    i: int = 0
    while i < len(data):
        if data[i : i + 7] == "0000001":
            stuffed += "00000010"
            i += 6
        else:
            stuffed += data[i]
        i += 1
    return stuffed


# Выделение изменённых символов
def highlight(string, newfcs):
    for i in range(8, len(string)):
        if string[i : i + 7] == "0000001":
            string = string[: i + 7] + "{" + string[i + 7] + "}" + string[i + 8 :]
    j: int = 0
    c: int = 0
    while j < len(string):
        print(string[j])
        if string[j] == "{":
            c -= 1
        elif string[j] != "}":
            c += 1
        if c == 19:
            newlist = list(string)
            newlist.insert(j + 1, " ")
            break
        j += 1
    return list_to_str(newlist)


# Де-бит стаффинг
def deBitStuffing(string):
    destuffed: str = string[0:8]
    i: int = 8
    while i < len(string):
        if string[i : i + 7] == "0000001":
            destuffed += string[i : i + 7] + string[i + 8 :]
            break
        else:
            destuffed += string[i]
        i += 1
    return destuffed


# Разбитие строки на подстроки по флагу
def split_rec_string(string):
    substrings = []
    current_substring = ""
    for i in range(len(string)):
        if string[i : i + 8] == "00000011":
            if current_substring:
                substrings.append(current_substring)
            current_substring = ""
        current_substring += string[i]
    if current_substring:
        substrings.append(current_substring)
    return substrings


# Перевод списка символов в строку
def list_to_str(lst: list[str]) -> str:
    data: str = ""
    for i in lst:
        data += i
    return data


# Искажение случайного бита с вероятностью 70%
def distortion(data):
    if random.random() <= 0.7:
        index: int = random.randint(0, 2)
        data_list: list[str] = list(data)
        if data_list[index] != "x":
            if data_list[index] == "0":
                data_list[index] = "1"
            else:
                data_list[index] = "0"
            return list_to_str(data_list)
    return data


# Код Хэмминга
def fcscalc(data):
    control_positions: list[int] = [1, 2, 4]
    fcs: str = ""
    data = "x" + data
    data_list: list[str] = list(data)
    for position in control_positions:
        data_list.insert(position, "1")
    values: list[str] = []
    bit1: str = data_list[1] + data_list[3] + data_list[5]
    bit2: str = data_list[2] + data_list[3] + data_list[6]
    bit3: str = data_list[4] + data_list[5] + data_list[6]
    values.append(bit1)
    values.append(bit2)
    values.append(bit3)
    for value in values:
        if value.count("1") % 2 == 0:
            fcs += "0"
        else:
            fcs += "1"
    return fcs


# Исправление ошибки
def fix(data, fcs, newfcs):
    control_positions: list[int] = [1, 2, 4]
    incorrect_bits_positions: list[int] = []
    for i in range(0, 3):
        if fcs[i] != newfcs[i]:
            incorrect_bits_positions.append(control_positions[i])
    incorrect_bit: int = 0
    for bit_position in incorrect_bits_positions:
        incorrect_bit += bit_position
    data = "x" + data
    data_list: list[str] = list(data)
    for position in control_positions:
        data_list.insert(position, "1")
    if data_list[incorrect_bit] == "0":
        data_list[incorrect_bit] = "1"
    else:
        data_list[incorrect_bit] = "0"
    control_positions.reverse()
    for i in control_positions:
        data_list[i] = ""
    return list_to_str(data_list)[1::1]

def send_data_in_thread(event):
    s_t = threading.Thread(target=send_data, args=(event,))
    s_t.start()

# Отправка символов через COM-порт
def send_data(event):
    global port
    global started
    global coll_stat
    text = input_text.get("1.0", "end")
    newtext = text.replace("\n", "")
    input_text.delete("1.0", "end")
    input_text.insert("1.0", newtext)
    strlist = split_string(newtext)
    if started == 1:
        flag: str = "00000011"
        destaddr: str = "0000"
        srcaddr: str = binary_string(int(com_var.get()))
        fin_len: int = 0
        coll_stat = ""
        str_to_send: str = ""
        for el in strlist:
            final_data = bitStuffing(destaddr + srcaddr + distortion(el) + fcscalc(el))
            str_to_send += collision_emul(flag + final_data)
            fin_len += len(str_to_send)
        port.write(str_to_send.encode("cp1251"))
        update_state(fin_len, "")
    return "break"


# Получение символов через COM-порт
def rec_data():
    global finish
    finish = 1
    rec_end = 0
    text = ""
    printed = False
    while True:
        try:
            symbol = port.read().decode("cp1251")
            if finish == 0:
                return
            if symbol:
                if rec_end == 1:
                    text = ""
                    printed = False
                    output_text.config(state=NORMAL)
                    output_text.delete("1.0", "end")
                    output_text.config(state=DISABLED)
                rec_end = 0
                text = text + symbol
            else:
                rec_end = 1
                if printed == False:
                    substrings = split_rec_string(text)
                    destuffed = []
                    restext: str = ""
                    for element in substrings:
                        if(len(element) == 22 or len(element) == 23):
                            destuffed_one = deBitStuffing(element)
                            olddata = destuffed_one[16:19]
                            oldfcs = destuffed_one[19:22]
                            newdata = olddata
                            newfcs = fcscalc(olddata)
                            highlighted = highlight(element, newfcs)
                            destuffed.append(highlighted[:-3] + newfcs)
                            if oldfcs != newfcs:
                                newdata = fix(olddata, oldfcs, newfcs)
                            restext += newdata
                        else:
                            pass
                    restext_f = restext.replace("x", "")
                    output_text.config(state=NORMAL)
                    output_text.insert("1.0", restext_f)
                    output_text.config(state=DISABLED)
                    update_state(-1, text)
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
def update_state(number, frames):
    global baudrate
    global lastnumber
    global coll_stat
    state_text.config(state=NORMAL)
    state_text.delete("1.0", END)
    if baudrate < 0:
        state_text.delete("1.0", END)
        try:
            baudrate = port.baudrate
            state_text.insert(END, "Speed: {}\n".format(baudrate))
        except Exception:
            state_text.insert(END, "Speed: N/A\n")
            baudrate = -1
    else:
        state_text.insert(END, "Speed: {}\n".format(baudrate))
    if number >= 0:
        lastnumber = number
        state_text.insert(END, "Bytes sent: {} {}\n".format(number, coll_stat))
    else:
        state_text.insert(END, "Bytes sent: {} {}\n".format(lastnumber, coll_stat))
    state_text.insert(END, "Frames: \n")
    for frame in frames:
        state_text.insert(END, "{}".format(frame))
    state_text.config(state=DISABLED)


# Случайная задержка
def backoff(n):
    k: int = 0
    if n > 10:
        k = 10
    else:
        k = n
    backoff: float = random.random() * math.pow(2, k) / 1000
    time.sleep(backoff)


# Занятость порта
def free_port():
    if random.random() < 0.7:
        return True
    else:
        return False


# Коллизия
def collision():
    if random.random() < 0.3:
        return True
    else:
        return False
    # return False


# Окно коллизий
def wait_collision_window():
    time.sleep(0.02)


# Эмуляция отправки
def collision_emul(data):
    global coll_stat
    data_to_send: str = ""
    for ch in data:
        while True:
            counter: int = 0
            while not free_port():
                pass
            data_to_send += ch
            wait_collision_window()
            if collision():
                # data_to_send = data_to_send[:-1]
                coll_stat += "+"
                counter += 1
                if counter < 20:
                    backoff(counter)
                else:
                    break
            else:
                coll_stat += "-"
                break
        coll_stat += " "
    return data_to_send


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
input_text.bind("<KeyPress>", validate_data)
input_text.bind("<Return>", send_data_in_thread)
control_frame = Frame(root, bg="white", padx=60, pady=25)
control_frame.grid(row=0, column=1, padx=10, pady=10)
Label(control_frame, text="Control").pack()

com_var = StringVar(control_frame)
com_var.set("1")
bits_var = StringVar(control_frame)
bits_var.set("8")

com_label = Label(control_frame, text="COM port number")
com_label.pack(pady=(25, 0))
com_menu = OptionMenu(
    control_frame,
    com_var,
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    command=chport,
)
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
update_state(0, "")

# Запускаем цикл обработки событий
root.mainloop()
