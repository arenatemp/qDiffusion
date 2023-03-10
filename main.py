import sys
import signal
import traceback
import datetime
import subprocess
import os
import glob
import shutil
import importlib

from PyQt5.QtCore import QUrl, QCoreApplication, Qt
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtWidgets import QApplication

import gui
import sql
import canvas

class Application(QApplication):
        def event(self, e):
            return QApplication.event(self, e)

def buildQMLRc():
    qml_rc = os.path.join("qml", "qml.qrc")
    if os.path.exists(qml_rc):
        os.remove(qml_rc)

    items = []

    tabs = glob.glob(os.path.join("tabs", "*"))
    for tab in tabs:
        for src in glob.glob(os.path.join(tab, "*.*")):
            if src.split(".")[-1] in {"qml","svg"}:
                dst = os.path.join("qml", src)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)
                items += [dst]

    items += glob.glob(os.path.join("qml", "*.qml"))
    items += glob.glob(os.path.join("qml", "components", "*.qml"))
    items += glob.glob(os.path.join("qml", "style", "*.qml"))
    items += glob.glob(os.path.join("qml", "fonts", "*.ttf"))
    items += glob.glob(os.path.join("qml", "icons", "*.svg"))

    items = ''.join([f"\t\t<file>{os.path.relpath(f, 'qml')}</file>\n" for f in items])

    contents = f"""<RCC>\n\t<qresource prefix="/">\n{items}\t</qresource>\n</RCC>"""

    with open(qml_rc, "w") as f:
        f.write(contents)

def buildQMLPy():
    qml_py = os.path.join("qml", "qml_rc.py")
    qml_rc = os.path.join("qml", "qml.qrc")

    if os.path.exists(qml_py):
        os.remove(qml_py)

    status = subprocess.run(["pyrcc5", "-o", qml_py, qml_rc], capture_output=True)
    if status.returncode != 0:
        raise Exception(status.stderr.decode("utf-8"))

    shutil.rmtree(os.path.join("qml", "tabs"))
    os.remove(qml_rc)

def loadTabs(app, backend):
    tabs = []
    for tab in glob.glob(os.path.join("tabs", "*")):
        tab_name = tab.split(os.path.sep)[-1]
        tab_module = importlib.import_module(f"tabs.{tab_name}.{tab_name}")
        tab_class = getattr(tab_module, tab_name)
        tab_instance = tab_class(parent=app)
        tab_instance.source = f"qrc:/tabs/{tab_name}/{tab_name}.qml"
        tabs += [tab_instance]
    for tab in tabs:
        if not hasattr(tab, "priority"):
            tab.priority = len(tabs)
    
    tabs.sort(key=lambda tab: tab.priority)
    backend.registerTabs(tabs)

def start():
    import qml.qml_rc

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = Application(sys.argv)
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    app.startTimer(100)

    sql.registerTypes()
    gui.registerTypes()
    canvas.registerTypes()
    canvas.registerMiscTypes()


    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)

    qmlRegisterSingletonType(QUrl("qrc:/Common.qml"), "gui", 1, 0, "COMMON")

    backend = gui.GUI(parent=app)

    os.makedirs("outputs/txt2img", exist_ok=True)
    os.makedirs("outputs/img2img", exist_ok=True)

    engine.addImageProvider("sync", backend.thumbnails.sync_provider)
    engine.addImageProvider("async", backend.thumbnails.async_provider)

    qmlRegisterSingletonType(gui.GUI, "gui", 1, 0, "GUI", lambda qml, js: backend)
    
    loadTabs(backend, backend)

    engine.load(QUrl('qrc:/Main.qml'))
    
    os._exit(app.exec())

def exceptHook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a") as f:
        f.write(f"{datetime.datetime.now()}\n{tb}\n")
    print(tb)
    print("TRACEBACK SAVED: crash.log")
    QApplication.quit()

if __name__ == "__main__":
    sys.excepthook = exceptHook
    buildQMLRc()
    buildQMLPy()
    start()
