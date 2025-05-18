InterHolon is a messenger app for language learners. It includes both basic chatting application functions as well as linguistical features: POS highlighting and typos checker

Instruction on launch:
  1) Start a server (chat_server.py)
  2) Start a client in a local network (qt_UI.py)
  3) Enter the server IP in the client window (if both are on the same device, you can enter nothing)

Libraries required:
  Client:
    PyQt6
    Cryptography
  Server:
    Cryptography
    stanza
    pyspellchecker
    phunspell
    numpy

Not finished:
In-time new messages highlighting
typo catching
