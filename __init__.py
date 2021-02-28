import sys, os, time, re
from PySide2.QtWidgets import QApplication, QWidget, QDialog, QInputDialog, QMessageBox, QMainWindow, QVBoxLayout, \
    QPushButton, QSlider, QListWidget, QCheckBox, QListWidgetItem
from PySide2.QtCore import QFile, Qt, QSettings, QEvent, QMimeData, QTimer
from PySide2.QtGui import QIcon, QFocusEvent
from PySide2.QtUiTools import QUiLoader
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel

# for UNDO decorator
from functools import wraps

"""
PROTOTYPE TOOL Concept by Gibson Weitzel
"""

ptr = omui.MQtUtil.mainWindow()
parent = wrapInstance(long(ptr), QWidget)


class AppWindow(QDialog):

    def __init__(self):
        '''
        Initializing App UI QDialog instance, parenting it to Maya's window
        '''
        # Passing in Maya's window pointer
        super(AppWindow, self).__init__(parent)

        # Enabling Undo Queue
        cmds.undoInfo(state=True, infinity=True)

        # Create a QIcon object
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))

        # Create Error Messagebox Object
        self.msg = QMessageBox()
        # Assign Error MessageBox Title
        self.msg.setWindowTitle("ERROR")
        # Assign Error MessageBox Icon
        self.msg.setWindowIcon(icon)

        # Assign the icon to the App Window
        self.setWindowIcon(icon)
        # Assign Window Title
        self.setWindowTitle("GSnap")

        # Maximum
        self.setMaximumHeight(282)
        self.setMaximumWidth(195)
        # Minimum
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)

        # App window layout, .ui gets put into
        self.applayout = QVBoxLayout()
        self.applayout.setMargin(0)
        self.setLayout(self.applayout)

        # Import .ui file
        self.ui = QUiLoader().load(QFile(os.path.join(os.path.dirname(__file__), "ui.ui")))

        # Adding .ui elements to applayout
        self.applayout.addWidget(self.ui)

        # Connect .UI widgets to functions
        self.connect_widgets()

        ### Saving temp .ini file for window location / geometry  into 2020/scripts/plugin
        self.settings_path = os.path.join(os.getenv('HOME') + "/maya/2020/scripts/GSnap/", "settingsFile.ini")
        print("SETTINGS PATH  ::: " + str(self.settings_path))
        # Restore window's previous geometry from file
        if os.path.exists(self.settings_path):
            settings_obj = QSettings(self.settings_path, QSettings.IniFormat)
            self.restoreGeometry(settings_obj.value("windowGeometry"))

        ### GUI DATA & INIT FUNCTIONS ###

        try:
            cmds.showHidden(cmds.listRelatives('GSnap', c=True))
        except:
            pass

        # Finally, update the listWidget when the window is visible
        try:
            self.update_widgets()
        except:
            pass

    ### Plugin Funcs ###

    def undo(func):
        """ Puts the wrapped `func` into a single Maya Undo action, then
            undoes it when the function enters the finally: block """

        @wraps(func)
        def _undofunc(*args, **kwargs):
            try:
                # start an undo chunk
                cmds.undoInfo(ock=True)
                return func(*args, **kwargs)
            finally:
                # after calling the func, end the undo chunk and undo
                cmds.undoInfo(cck=True)

        return _undofunc

    def maya_item_changed(self):
        '''
        Updates GUI with Maya changes
        '''
        self.qtimer_update_widgets(maya=True)

    def list_item_changed(self):
        '''
        Updates Maya with GUI changes
        '''
        self.qtimer_update_widgets(gsnap=True)

    def qtimer_update_widgets(self, gsnap=False, maya=False):
        if gsnap:
            self.update_widgets(gsnap=True)
        elif maya:
            self.update_widgets(maya=True)

    def update_widgets(self, gsnap=False, maya=False):
        try:
            if cmds.listRelatives("GSnap", c=True):
                scale = (cmds.getAttr(cmds.listRelatives(cmds.listRelatives("GSnap", c=True)[0], shapes=True)[0] + ".localScaleX"))
                self.locator_scale = int(scale)
                self.horizontalSlider.setValue(self.locator_scale)

                maya_items = cmds.listRelatives('GSnap', c=True)
                listwidget_items = [self.listWidget.item(i) for i in range(self.listWidget.count())]

                ### Items ###

                for i in listwidget_items:
                    if i.text() in maya_items:
                        i.setHidden(False)
                    else:
                        i.setHidden(True)

                for i in maya_items:
                    item = i
                    if i not in [i.text() for i in listwidget_items if i.isHidden() is False]:
                        self.listWidget.addItem(item)

                ### Selection ###
                
                gsnap_list = [i for i in listwidget_items if i.isHidden() is False]
                maya_list = cmds.listRelatives('GSnap', c=True)
                
                gsnap_selected = [i for i in self.listWidget.selectedItems()]
                maya_selected = cmds.ls(sl=True)

                ### GSnap/Maya

                self.qtimer_function(111, self.focus_maya)

                if gsnap:
                    for i in gsnap_list:
                        if i.isSelected():
                            if i.text() not in maya_selected:
                                cmds.select(i.text(), add=True)
                        else:
                            cmds.select(i.text(), deselect=True)

                if maya:
                    for i in maya_list:
                        if i in maya_selected:
                            for item in listwidget_items:
                                if item.text() == i:
                                    item.setSelected(True)
                        else:
                            for item in listwidget_items:
                                if item.text() == i:
                                    item.setSelected(False)

        except Exception as e:
            pass
            #print("ERROR ::: " + str(e.message))

    def vis_locators(self, show=False):
        try:
            if show:
                self.checkbox.setChecked(True)
                cmds.showHidden(cmds.listRelatives("GSnap", c=True))
                return

            if self.checkbox.isChecked():
                cmds.showHidden(cmds.listRelatives("GSnap", c=True))
            else:
                cmds.hide(cmds.listRelatives("GSnap", c=True))
        except:
            pass
        finally:
            self.update_widgets()
    @undo
    def snap_values(self):
        '''
        Snaps selected object 1 to object 2.
        If a constraint exists on object 1, grab it's parent, and reapply it after value change.
        '''

        selected = cmds.ls(sl=True)

        if len(selected) < 2:
            return

        for i in cmds.listRelatives(selected[0], c=True):
            if "parentConstraint" not in str(cmds.listRelatives(selected[0], c=True)):
                constraint = None
                constraint_parent = None
                break
            elif "parentConstraint" in str(i):
                constraint = i
                constraint_parent = cmds.listConnections(constraint, source=True, destination=False, et=True,
                                                         type="transform")
                for i in constraint_parent:
                    if str(i) != str(selected[0]):
                        constraint_parent = i
                        break
                break

        if constraint_parent:
            cmds.delete(constraint)

        try:
            value_locator = cmds.spaceLocator(name="gsnap_value_locator")
            constraint = cmds.parentConstraint(selected[1], selected[0], mo=False)
            cmds.delete(constraint)
            cmds.setAttr(str(selected[0]) + ".translateX", cmds.getAttr(value_locator + ".translateX"))
            cmds.setAttr(str(selected[0]) + ".translateY", cmds.getAttr(value_locator + ".translateY"))
            cmds.setAttr(str(selected[0]) + ".translateZ", cmds.getAttr(value_locator + ".translateZ"))
            cmds.setAttr(str(selected[0]) + ".rotateX", cmds.getAttr(value_locator + ".rotateX"))
            cmds.setAttr(str(selected[0]) + ".rotateY", cmds.getAttr(value_locator + ".rotateY"))
            cmds.setAttr(str(selected[0]) + ".rotateZ", cmds.getAttr(value_locator + ".rotateZ"))
        except Exception as e:
            print("Err Setting Values ::: "+str(e.message))
        finally:
            cmds.delete(value_locator)

        if constraint_parent:
            cmds.parentConstraint(constraint_parent, selected[0], mo=True)  # C   #

        cmds.select(selected[0], replace=True)
        self.update_widgets()
        cmds.setFocus("MayaWindow")
    @undo
    def delete_locators(self):
        try:
            cmds.setFocus("MayaWindow")
            selection = cmds.ls(sl=True)
            if selection:
                for i in selection:
                    maya_object = i
                    for item in [self.listWidget.item(i) for i in range(self.listWidget.count())]:
                        if item.text() == maya_object:
                            item.setHidden(True)
                    if maya_object in cmds.listRelatives('GSnap', c=True):
                            cmds.delete(maya_object)
                return

            msg = QMessageBox()
            msg.setWindowTitle("X")
            text = msg.question(self, 'X', "Delete all Locators?", msg.Yes | msg.No)

            if text == msg.Yes:
                cmds.delete("GSnap")
                self.listWidget.clear()
                cmds.setFocus("MayaWindow")

        except Exception as e:
            print("GSnap Delete Error ::: " + str(e.message))
    @undo
    def add_locator(self):
        selected = cmds.ls(sl=True)

        if cmds.objExists('GSnap') is False:
            cmds.group(name="GSnap", empty=True)
            try:
                cmds.select(selected[0], r=True)
                cmds.select(selected[1], add=True)
            except:

                pass

        text, ok = QInputDialog.getText(self, 'Add Locator', 'Name:')
        text = text.upper().replace(' ', '_')

        try:
            if text.isdecimal() is not False:
                self.msg.setText("Invalid Name:  <B><FONT COLOR='ORANGE'>" + text + "</FONT></B>  !")
                self.msg.show()
                return
            elif text in cmds.listRelatives("GSnap", c=True):
                self.msg.setText("Object already named:  <B><FONT COLOR='ORANGE'>" + text + "</FONT></B>  !")
                self.msg.show()
                return
        except:
            pass

        if not ok:
            return
        else:
            locator = cmds.spaceLocator(name=text)

            cmds.parent(locator, "GSnap")

            try:
                constraint = cmds.parentConstraint(selected[0], locator, maintainOffset=False)
                cmds.delete(constraint)
                cmds.parentConstraint(selected[1], locator, maintainOffset=True)
            except:
                pass  # Less than 2 objects selected

            color = (cmds.getAttr(cmds.listRelatives(cmds.listRelatives("GSnap", c=True)[0], shapes=True)[0] + ".overrideColorRGB"))
            if color[0] != (0.0, 0.0, 0.0):
                cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".overrideEnabled", 1)
                cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".overrideRGBColors", 1)
                cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".overrideColorRGB", color[0][0], color[0][1], color[0][2])
            else:
                cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".overrideEnabled", 1)
                cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".overrideRGBColors", 1)
                cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".overrideColorRGB", 1, 0.19, 0.02)

            cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".localScaleX", self.locator_scale)
            cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".localScaleY", self.locator_scale)
            cmds.setAttr(cmds.listRelatives(locator, s=True)[0] + ".localScaleZ", self.locator_scale)

            self.update_widgets()
            cmds.setFocus("MayaWindow")
    @undo
    def update_size(self, arg=None):
        '''
        Updates the size of every locator when slider is released
        '''
        try:
            value = self.findChild(QWidget, "horizontalSlider").value()
            for i in cmds.listRelatives("GSnap", c=True):
                cmds.setAttr(cmds.listRelatives(i, shapes=True)[0] + '.localScaleX', value)
                cmds.setAttr(cmds.listRelatives(i, shapes=True)[0] + '.localScaleY', value)
                cmds.setAttr(cmds.listRelatives(i, shapes=True)[0] + '.localScaleZ', value)
            self.update_widgets()
        except:
            pass

    def focus_maya(self):
        cmds.setFocus("MayaWindow")

    def qtimer_function(self, time=0, function=None):
        if function:
            QTimer.singleShot(time, function)

    def connect_widgets(self):
        """
        Connect widgets to functions
        """
        # Grabbing all QWidgets

        self.horizontalSlider = self.findChild(QSlider, "horizontalSlider")
        self.checkbox = self.findChild(QCheckBox, "checkBox")
        self.pushbutton_add = self.findChild(QPushButton, "pushButton_add")
        self.pushbutton_snap = self.findChild(QPushButton, "pushButton_snap")
        self.pushbutton_delete = self.findChild(QPushButton, "pushButton_delete")
        self.listWidget = self.findChild(QListWidget, "listWidget")
        self.listWidget.clear()

        self.selectJob = cmds.scriptJob(e=["SelectionChanged", self.maya_item_changed], protected=True)

        self.horizontalSlider.valueChanged.connect(self.update_size)
        self.checkbox.released.connect(self.vis_locators)
        self.pushbutton_add.clicked.connect(self.add_locator)
        self.pushbutton_snap.clicked.connect(self.snap_values)
        self.pushbutton_delete.clicked.connect(self.delete_locators)
        self.listWidget.itemSelectionChanged.connect(self.list_item_changed)
        self.listWidget.itemClicked.connect(self.list_item_changed)

    def closeEvent(self, event):
        """
        Save size geometry/location placement, and destroy on closing
        """
        settings_obj = QSettings(self.settings_path, QSettings.IniFormat)
        settings_obj.setValue("windowGeometry", self.saveGeometry())
        cmds.scriptJob(kill=self.selectJob, force=True)
        self.destroy()


app = AppWindow()

app.show()
