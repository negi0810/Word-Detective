from ctypes.wintypes import WORD
from gettext import find
from turtle import fd


st = "アイス、かき氷、シャーベット、氷砂糖"
fd = st.find("氷")
print(fd)


co = st.count("氷")
print(co)


print("氷" in st)