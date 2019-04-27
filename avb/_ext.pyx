# cython: language_level=3, distutils: language = c++, boundscheck=False

from libcpp.vector cimport vector
from libcpp.map cimport map
from libc.stdint cimport (uint8_t, int16_t, uint32_t, int32_t)
from cython.operator cimport dereference as deref, preincrement as inc
cimport cython

from datetime import datetime
import uuid

from .utils import AVBObjectRef
from . import utils
from .mobid import MobID
from . import core

cdef extern from "" namespace "Properties":
    struct ChildData:
        const char *name
        vector[Properties] data

cdef extern from "_ext_core.cpp" nogil:
    cdef enum StringType:
        MACROMAN,
        UTF8

    cdef enum PropertyType:
        TRKG,
        TRACK,

    cdef enum AttrType:
        INT_ATTR,
        STR_ATTR,
        OBJ_ATTR,
        BOB_ATTR,

    cdef enum ControlPointType:
        ParamControlPointType,

    cdef enum ControlPointValueType:
        CP_TYPE_INT,
        CP_TYPE_DOUBLE,
        CP_TYPE_REFERENCE,

    cdef struct UIntData:
        const char *name
        uint32_t data

    cdef struct IntData:
        const char *name
        int32_t data

    cdef struct DoubleData:
        const char *name
        double data

    cdef struct BoolData:
        const char *name
        bint data

    cdef struct StringData:
        const char *name;
        StringType type
        vector[uint8_t] data

    cdef struct BytesData:
        const char *name;
        vector[uint8_t] data

    cdef struct RefListData:
        const char *name
        vector[uint32_t] data

    cdef struct MobIDData:
        const char *name;
        uint8_t data[32]

    cdef struct PerPoint:
        int16_t code;
        ControlPointValueType type
        uint32_t value;
        double double_value;

    cdef struct ControlPoint:
        int32_t offset_num;
        int32_t offset_den;
        int32_t timescale;
        uint32_t value;
        double double_value;
        vector[PerPoint] pp;

    cdef struct ControlPointData:
        const char *name
        ControlPointType type
        ControlPointValueType value_type
        vector[ControlPoint] data

    cdef struct AttrData:
        vector[uint8_t] name
        AttrType type
        uint32_t value
        vector[uint8_t] data

    cdef struct Buffer:
        const uint8_t *root
        const uint8_t *ptr
        const uint8_t *end

    cdef struct Properties:
        Buffer *f
        vector[UIntData]   refs
        vector[UIntData]   int_unsigned
        vector[IntData]    int_signed
        vector[BoolData]   bools
        vector[UIntData]   dates
        vector[DoubleData] doubles
        vector[BytesData]  uuids
        vector[StringData] strings
        vector[MobIDData]  mob_ids
        vector[RefListData] reflists
        vector[ChildData]  children;
        vector[ControlPointData] control_points

    cdef int read_attributes(Buffer *f, vector[AttrData] &d)

    cdef int read_comp(Buffer *f, Properties *p) except+
    cdef int read_sequence(Buffer *f, Properties *p) except+
    cdef int read_sourceclip(Buffer *f, Properties *p) except+
    cdef int read_paramclip(Buffer *f, Properties *p) except+
    cdef int read_paramitem(Buffer *f, Properties *p) except+
    cdef int read_trackref(Buffer *f, Properties *p) except+
    cdef int read_filler(Buffer *f, Properties *p) except+
    cdef int read_trackeffect(Buffer *f, Properties *p) except+
    cdef int read_selector(Buffer *f, Properties *p) except+
    cdef int read_composition(Buffer *f, Properties *p) except+


cdef class AVBPropertyData(dict):

    def deref(self, value):
        if isinstance(value, utils.AVBObjectRef):
            return value.value
        return value

    def __getitem__(self, key):
        return self.deref(super(AVBPropertyData, self).__getitem__(key))

    def items(self):
        for key, value in super(AVBPropertyData, self).items():
            yield key, self.deref(value)

    def get(self, *args, **kwargs):
        return self.deref(super(AVBPropertyData, self).get(*args, **kwargs))

cdef void refs2dict(object root, dict d, Properties* p):
    cdef bytes name
    cdef UIntData item

    for item in p.refs:
        name = <bytes> item.name
        # d[name.decode('utf-8')] = item.data
        d[name.decode('utf-8')] = AVBObjectRef(root, item.data)

cdef void reflist2dict(object root, dict d, Properties* p):
    cdef bytes name
    cdef RefListData item
    cdef uint32_t i

    for item in p.reflists:
        name = <bytes> item.name
        reflist = core.AVBRefList.__new__(core.AVBRefList, root=root)
        reflist.extend(item.data)
        d[name.decode('utf-8')] = reflist

cdef void controlpoints2dict(object root, dict d, Properties* p):

    cdef ControlPointData item
    cdef ControlPoint cp
    cdef PerPoint pp
    cdef bytes name
    cdef list control_point_list
    cdef list pp_list

    cdef object obj_class
    cdef object pp_obj_class

    cdef AVBPropertyData cpdata
    cdef AVBPropertyData ppdata

    for item in p.control_points:
        if item.type == ParamControlPointType:
            obj_class = utils.AVBClassName_dict['ParamControlPoint']
            pp_obj_class = utils.AVBClassName_dict['ParamPerPoint']
        else:
            obj_class = utils.AVBClassName_dict['ControlPoint']
            pp_obj_class = utils.AVBClassName_dict['PerPoint']

        name = <bytes>item.name
        control_point_list = []
        for cp in item.data:

            cpdata = AVBPropertyData()
            cpdata['offset'] = (cp.offset_num, cp.offset_den)
            cpdata['timescale'] = cp.timescale

            if item.value_type == CP_TYPE_INT:
                cpdata['value'] = cp.value
            elif item.value_type == CP_TYPE_DOUBLE:
                cpdata['value'] =cp.double_value
            elif item.value_type == CP_TYPE_REFERENCE:
                cpdata['value'] = utils.AVBObjectRef(root, cp.value)

            pp_list = []
            for pp in cp.pp:
                ppdata = AVBPropertyData()
                ppdata['code'] = pp.code
                ppdata['type'] = pp.type
                if pp.type == CP_TYPE_DOUBLE:
                    ppdata['value'] = pp.double_value
                elif pp.type == CP_TYPE_INT:
                    ppdata['value'] = pp.value

                py_pp = pp_obj_class.__new__(pp_obj_class, root=root)
                py_pp.property_data = ppdata
                pp_list.append(py_pp)

            cpdata['pp'] = pp_list
            py_cp = obj_class.__new__(obj_class, root=root)
            py_cp.property_data = cpdata
            control_point_list.append(py_cp)
        d[name.decode("utf-8")] = control_point_list


cdef void int_usigned2dict(dict d, Properties* p):
    cdef bytes name
    cdef UIntData item

    for item in p.int_unsigned:
        name = <bytes> item.name
        d[name.decode('utf-8')] = item.data

cdef void dates2dict(dict d, Properties* p):
    cdef bytes name
    cdef UIntData item

    for item in p.dates:
        name = <bytes> item.name
        d[name.decode('utf-8')] = datetime.fromtimestamp(item.data)

cdef void int_signed2dict(dict d, Properties* p):
    cdef bytes name
    cdef IntData item

    for item in p.int_signed:
        name = <bytes> item.name
        d[name.decode('utf-8')] = item.data

cdef void doubles2dict(dict d, Properties *p):
    cdef bytes name
    cdef DoubleData item
    for item in p.doubles:
        name = <bytes> item.name
        d[name.decode('utf-8')] = item.data

cdef void bools2dict(dict d,  Properties *p):
    cdef bytes name
    cdef BoolData item
    for item in p.bools:
        name = <bytes> item.name
        d[name.decode('utf-8')] = item.data

cdef void uuid2dict(dict d, Properties *p):

    cdef bytes name
    cdef bytes data

    cdef BytesData item
    cdef uint8_t *ptr

    for item in p.uuids:
        name = <bytes> item.name
        ptr = &item.data[0]
        data = <bytes> ptr[:16]

        d[name.decode('utf-8')] = uuid.UUID(bytes_le=data)

cdef void mob_id2dict(dict d, Properties *p):

    cdef bytes name
    cdef bytes data
    cdef MobIDData item

    for item in p.mob_ids:
        name = <bytes> item.name
        data = <bytes> item.data[:32]

        d[name.decode('utf-8')] = MobID(bytes_le=data)

cdef void strings2dict(dict d, Properties *p):
    cdef const char * ptr

    cdef bytes data
    cdef bytes name
    cdef StringData item
    cdef size_t data_size;

    for item in p.strings:
        name = <bytes> item.name
        data_size = item.data.size()

        if data_size > 0:
            ptr = <const char *>&item.data[0]
            data = <bytes>ptr[:data_size]
            d[name.decode('utf-8')] = data.decode("macroman")
        else:
            d[name.decode('utf-8')] = u""

cdef void children2dict(object root, dict d, Properties *p):
    cdef ChildData item
    cdef Properties child_properties

    cdef bytes name
    cdef list plist
    cdef dict pdata

    for item in p.children:
        name = <bytes> item.name
        plist = []

        for child_properties in item.data:
            pdata = process_poperties(root, &child_properties)
            obj_class = utils.AVBClassName_dict['Track']
            object_instance = obj_class.__new__(obj_class, root=root)
            object_instance.property_data = pdata
            plist.append(object_instance)

        d[name.decode('utf-8')] = plist

cdef dict process_poperties(object root, Properties *p):
    cdef dict result = AVBPropertyData()

    refs2dict(root, result, p)
    reflist2dict(root, result, p)
    int_usigned2dict(result, p)
    int_signed2dict(result, p)
    doubles2dict(result, p)
    strings2dict(result, p)
    bools2dict(result, p)
    uuid2dict(result, p)
    mob_id2dict(result, p)
    dates2dict(result, p)
    if p.control_points.size():
        controlpoints2dict(root, result, p)
    children2dict(root, result, p)

    return result


def read_attr_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    cdef AttrData item
    cdef vector[AttrData] d
    cdef bytes item_name
    cdef bytes item_data
    cdef object value

    cdef const char * ptr
    cdef size_t data_size;

    with nogil:
        read_attributes(&buf, d)

    for item in d:
        data_size = item.name.size()
        ptr =  <const char *>&item.name[0]
        item_name = <bytes> ptr[:data_size]
        value = None

        if item.type == INT_ATTR:
            value = <int32_t>item.value

        elif item.type == STR_ATTR:
            data_size = item.data.size()
            ptr =  <const char *>&item.data[0]
            item_data = <bytes> ptr[:data_size]
            value = item_data.decode('macroman')

        elif item.type == OBJ_ATTR:
            value = utils.AVBObjectRef(root, item.value)

        elif item.type == BOB_ATTR:
            data_size = item.data.size()
            ptr =  <const char *>&item.data[0]
            item_data = <bytes> ptr[:data_size]
            value = bytearray(item_data)


        object_instance[item_name.decode('macroman')] = value

# @cython.boundscheck(False)
def read_fourcc_le(object f):
    cdef const unsigned char[:] data = f.read(4)
    if len(data) != 4:
        return None

    cdef uint32_t value = data[3]
    value |= data[2] << 8
    value |= data[1] << 16
    value |= data[0] << 24
    cdef uint8_t *ptr = <uint8_t *> &value
    cdef bytes result = <bytes> ptr[:4]
    return result


def read_sequence_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_sequence(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_sourceclip_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_sourceclip(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_paramclip_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_paramclip(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_paramitem_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_paramitem(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_trackref_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_trackref(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_filler_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_filler(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def reads_selector_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_selector(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_composition_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_composition(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_trackeffect_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]

    cdef Properties p
    with nogil:
        read_trackeffect(&buf, &p)

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

READERS = {
b'CMPO': read_composition_data,
b'TKFX': read_trackeffect_data,
b'SLCT': reads_selector_data,
b"SEQU": read_sequence_data,
b'FILL': read_filler_data,
b'SCLP': read_sourceclip_data,
b'PRCL': read_paramclip_data,
b'PRIT': read_paramitem_data,
b'TRKR': read_trackref_data,
b'ATTR': read_attr_data,
}
