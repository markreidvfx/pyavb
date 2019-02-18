from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import sys
from PySide2 import QtCore

import avb

if str is not bytes:
    unicode = str

def pretty_value(value):
    if isinstance(value, bytearray):
        return "bytearray(%d)" % len(value)
        # return ''.join(format(x, '02x') for x in value)
    return value

def get_properties(obj):

    propertie_keys = []
    property_data = None

    if isinstance(obj, avb.core.AVBObject):
        property_data = obj.property_data
        for pdef in obj.propertydefs:
            key = pdef.name
            if key not in obj.property_data:
                continue
            propertie_keys.append(key)

    elif isinstance(obj, dict):
        propertie_keys = obj.keys()
        propertie_keys.sort()
        property_data = obj

    result = []
    for key in propertie_keys:
        value = property_data[key]
        if value is not None:
            result.append([key, pretty_value(value)])
    return result


class TreeItem(object):

    def __init__(self, name, value, parent=None, index = 0):
        self.parentItem = parent
        self._name = name
        self.item = value
        self.children = {}
        self.children_count = 0
        self.properties = {'Name':name}
        self.loaded = False
        self.index = index
        self.references = []
        #self.getData()
    def columnCount(self):
        return 1

    def childCount(self):
        self.setup()
        return self.children_count

    def child(self,row):
        self.setup()
        if row in self.children:
            return self.children[row]
        # print(row, self.item)
        # self.children[row] = t
        # return t

    def childNumber(self):
        self.setup()
        return self.index

    def parent(self):
        self.setup()
        return self.parentItem

    def extend(self, items):
        for name, value in items:
            index = self.children_count
            t = TreeItem(name, value, self, index)

            self.children[index] = t
            self.children_count += 1

    def name(self):
        return self._name


    def setup(self):
        if self.loaded:
            return

        item = self.item

        if isinstance(item, (avb.core.AVBObject, dict)):
            self.extend(get_properties(item))
            self.properties['Value'] = 'AVBObject'
        if isinstance(item, list):
            children = []
            for i in item:
                if hasattr(i, 'name') and i.name is not None:
                    children.append([i.name, i])
                else:
                    children.append([i.__class__.__name__, i])
            self.properties['Value'] = 'list'
            self.extend(children)

        else:
            self.properties['Value'] = unicode(item)

        self.properties['Name'] = self._name
        self.loaded = True

class AVBModel(QtCore.QAbstractItemModel):

    def __init__(self, root ,parent=None):
        super(AVBModel,self).__init__(parent)

        self.rootItem = TreeItem("Root", root)

        self.headers = ['Name', 'Value',]

    def headerData(self, column, orientation,role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[column]
        return None

    def columnCount(self,index):
        #item = self.getItem(index)

        return len(self.headers)

    def rowCount(self,parent=QtCore.QModelIndex()):
        parentItem = self.getItem(parent)
        return parentItem.childCount()

    def data(self, index, role):

        if not index.isValid():
            return 0

        if role != QtCore.Qt.DisplayRole:
            return None

        item = self.getItem(index)

        header_key = self.headers[index.column()]

        return str(item.properties.get(header_key,''))

    def parent(self, index):

        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def index(self, row, column, parent = QtCore.QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QtCore.QModelIndex()

        item = self.getItem(parent)
        childItem = item.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()


    def getItem(self,index):

        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

if __name__ == "__main__":

    from PySide2 import QtWidgets
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-m','--mobs',action="store_true", default=False)
    parser.add_option('-t','--toplevel',action="store_true", default=False)

    (options, args) = parser.parse_args()

    if not args:
        parser.error("not enough arguments")

    file_path = args[0]

    f = avb.open(file_path)

    root = f.content
    if options.toplevel:
        root = list(f.content.toplevel())
    if options.mobs:
        root = list(f.content.mobs)

    app = QtWidgets.QApplication(sys.argv)

    model = AVBModel(root)

    use_column = False

    if use_column:
        tree = QtWidgets.QColumnView()
        tree.setModel(model)
    else:
        tree = QtWidgets.QTreeView()
        tree.setModel(model)

        tree.setUniformRowHeights(True)
        tree.expandToDepth(1)
        tree.resizeColumnToContents(0)
        tree.resizeColumnToContents(1)

    tree.resize(700,600)
    tree.setAlternatingRowColors(True)

    tree.show()

    sys.exit(app.exec_())
