import libtmux
import os
import subprocess
os.system("tmux kill-session -t NFVi")
os.system("tmux new-session -d -s NFVi")
server = libtmux.Server()
session = server.find_where({ "session_name": "NFVi" })
window_base_index = int(session.attached_window.get('window_index'))
window = session.select_window(window_base_index)
#Create vertical pannel
window.split_window(attach=False,vertical=False)
os.system("tmux attach -t NFVi")
