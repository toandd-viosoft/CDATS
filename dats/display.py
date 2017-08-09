#
# Dataplane Automated Testing System
#
# Copyright (c) 2015-2016, Viosoft Corporation.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Viosoft Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import libtmux
import os

session_name="Crucio"
server=""
session=""
window="CrucioBaremetal"
sutPanel= None
testerPanel= None
controllerPanel = None
def attachDashboard():
    global  sutPanel
    global  testerPanel 
    global  controllerPanel
    server = libtmux.Server()
    session = server.find_where({ "session_name": "Crucio" })
    #attach to window
    window_base_index = int(session.attached_window.get('window_index'))
    window = session.select_window(window_base_index)
    testerPanel = window.select_pane(0)
    sutPanel = window.select_pane(1)
    controllerPanel = window.select_pane(2)
def runCmdOnSutPannel(cmd):
    global  sutPanel
    return sutPanel.send_keys(cmd)

def runCmdOnTesterPannel(cmd):
    global  testerPanel 
    return testerPanel.send_keys(cmd)
def runCmdOnControllerPannel(cmd):
    global  controllerPanel 
    return controllerPanel.send_keys(cmd)
