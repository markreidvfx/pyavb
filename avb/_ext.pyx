# cython: language_level=3, distutils: language = c++, boundscheck=False, profile=False

from libcpp.vector cimport vector
cimport cython

IF UNAME_SYSNAME == "Windows":
    cdef extern from *:
        ctypedef unsigned char  uint8_t
        ctypedef   signed char  int8_t

        ctypedef unsigned short uint16_t
        ctypedef   signed short int16_t

        ctypedef unsigned int   uint32_t
        ctypedef   signed int   int32_t

        ctypedef unsigned long long int uint64_t
        ctypedef   signed long long int int64_t
ELSE:
    from libc.stdint cimport (uint8_t, int16_t, uint32_t, int32_t, uint64_t, int64_t)

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
        PARAM,

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
        CP_TYPE_REFERENCE

    cdef union IntDataValue:
        uint64_t u64
        int64_t  s64

    cdef struct IntData:
        const char *name
        bint is_signed;
        IntDataValue data

    cdef struct IntArrayData:
        const char *name
        vector[int64_t] data

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
        const char *error_message

    cdef struct Properties:
        PropertyType type
        vector[IntData]   refs
        vector[IntData]   ints
        vector[BoolData]   bools
        vector[IntData]   dates
        vector[DoubleData] doubles
        vector[BytesData]  uuids
        vector[StringData] strings
        vector[BytesData]  mob_ids
        vector[RefListData] reflists
        vector[ChildData]  children;
        vector[ControlPointData] control_points
        vector[IntArrayData] arrays
        vector[BytesData] bytearrays

    cdef int read_attributes(Buffer *f, vector[AttrData] &d) except+
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
    cdef int read_media_descriptor(Buffer *f, Properties *p) except+
    cdef int read_did_descriptor(Buffer *f, Properties *p) except+
    cdef int read_cdci_descriptor(Buffer *f, Properties *p) except+
    cdef int read_effectparamlist(Buffer *f, Properties *p) except+

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
    cdef IntData item
    for item in p.refs:
        d[item.name.decode('utf-8')] = AVBObjectRef(root, item.data.u64)

cdef void reflist2dict(object root, dict d, Properties* p):
    cdef RefListData item
    cdef uint32_t i

    for item in p.reflists:
        reflist = core.AVBRefList.__new__(core.AVBRefList, root=root)
        reflist.extend(item.data)
        d[item.name.decode('utf-8')] = reflist

cdef void controlpoints2dict(object root, dict d, Properties* p):

    cdef ControlPointData item
    cdef ControlPoint cp
    cdef PerPoint pp
    cdef bytes name
    cdef list control_point_list
    cdef list pp_list

    cdef object obj_class
    cdef object pp_obj_class

    cdef dict cpdata
    cdef dict ppdata

    for item in p.control_points:
        if item.type == ParamControlPointType:
            obj_class = utils.AVBClassName_dict['ParamControlPoint']
            pp_obj_class = utils.AVBClassName_dict['ParamPerPoint']
        else:
            obj_class = utils.AVBClassName_dict['ControlPoint']
            pp_obj_class = utils.AVBClassName_dict['PerPoint']

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

        d[item.name.decode("utf-8")] = control_point_list


cdef void ints2dict(dict d, Properties* p):
    cdef IntData item
    cdef int64_t signed_value
    for item in p.ints:
        if item.is_signed:
            d[item.name.decode('utf-8')] = item.data.s64
        else:
            d[item.name.decode('utf-8')] = item.data.u64

cdef void dates2dict(dict d, Properties* p):
    cdef IntData item
    for item in p.dates:
        d[item.name.decode('utf-8')] = datetime.fromtimestamp(item.data.u64)

cdef void doubles2dict(dict d, Properties *p):
    cdef DoubleData item
    for item in p.doubles:
        name = <bytes> item.name
        d[item.name.decode('utf-8')] = item.data

cdef void bools2dict(dict d,  Properties *p):
    cdef BoolData item
    for item in p.bools:
        d[item.name.decode('utf-8')] = item.data

cdef void uuid2dict(dict d, Properties *p):
    cdef bytes data

    cdef BytesData item
    cdef uint8_t *ptr

    for item in p.uuids:
        ptr = &item.data[0]
        data = <bytes> ptr[:16]

        d[item.name.decode('utf-8')] = uuid.UUID(bytes_le=data)

cdef void mob_id2dict(dict d, Properties *p):
    cdef bytes data
    cdef BytesData item
    cdef uint8_t *ptr

    for item in p.mob_ids:
        ptr = &item.data[0]
        data = <bytes> ptr[:32]

        d[item.name.decode('utf-8')] = MobID(bytes_le=data)

cdef void strings2dict(dict d, Properties *p):
    cdef const char * ptr

    cdef StringData item
    cdef size_t data_size;

    for item in p.strings:
        data_size = item.data.size()

        if data_size > 0:
            ptr = <const char *>&item.data[0]
            d[item.name.decode('utf-8')] = ptr[:data_size].decode("macroman")
        else:
            d[item.name.decode('utf-8')] = u""

cdef void children2dict(object root, dict d, Properties *p):
    cdef ChildData item
    cdef Properties child_properties

    cdef list plist
    cdef dict pdata

    for item in p.children:
        plist = []

        for child_properties in item.data:
            pdata = process_poperties(root, &child_properties)

            if child_properties.type == TRACK:
                obj_class = utils.AVBClassName_dict['Track']
            elif child_properties.type == PARAM:
                obj_class = utils.AVBClassName_dict['EffectParam']

            object_instance = obj_class.__new__(obj_class, root=root)
            object_instance.property_data = pdata
            plist.append(object_instance)

        d[item.name.decode('utf-8')] = plist

cdef void int_array2dict(dict d, Properties *p):
    cdef IntArrayData item
    for item in p.arrays:
        name = item.name.decode('utf-8')
        if name in ('valid_box', 'essence_box', 'source_box', 'framing_box'):
            d[name] = [ [item.data[0], item.data[1]],
                        [item.data[2], item.data[3]],
                        [item.data[4], item.data[5]],
                        [item.data[6], item.data[7]],]
        else:
            d[name] = item.data

cdef void bytearray2dict(dict d, Properties *p):
    cdef BytesData item
    cdef uint8_t *ptr
    cdef size_t size
    for item in p.bytearrays:
        size = item.data.size()
        if size:
            ptr = &item.data[0]
            d[item.name.decode('utf-8')] = <bytearray> ptr[:size]
        else:
            d[item.name.decode('utf-8')] = bytearray()

cdef dict process_poperties(object root, Properties *p):
    cdef dict result = AVBPropertyData()

    if p.refs.size():
        refs2dict(root, result, p)
    if p.reflists.size():
        reflist2dict(root, result, p)
    if p.ints.size():
        ints2dict(result, p)
    if p.doubles.size():
        doubles2dict(result, p)
    if p.strings.size():
        strings2dict(result, p)
    if p.bools.size():
        bools2dict(result, p)
    if p.uuids.size():
        uuid2dict(result, p)
    if p.mob_ids.size():
        mob_id2dict(result, p)
    if p.dates.size():
        dates2dict(result, p)
    if p.arrays.size():
        int_array2dict(result, p)
    if p.bytearrays.size():
        bytearray2dict(result, p)
    if p.control_points.size():
        controlpoints2dict(root, result, p)
    if p.children.size():
        children2dict(root, result, p)

    return result


def read_attr_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef AttrData item
    cdef vector[AttrData] d

    cdef object value

    cdef const char * ptr
    cdef size_t data_size;
    cdef int ret = 0

    with nogil:
        ret = read_attributes(&buf, d)

    if ret < 0:
        raise ValueError("Error reading Attributes: %s" % buf.error_message.decode("utf-8"))

    for item in d:

        value = None

        if item.type == INT_ATTR:
            value = <int32_t>item.value

        elif item.type == STR_ATTR:
            data_size = item.data.size()
            ptr =  <const char *>&item.data[0]
            value = ptr[:data_size].decode('macroman')

        elif item.type == OBJ_ATTR:
            value = utils.AVBObjectRef(root, item.value)

        elif item.type == BOB_ATTR:
            data_size = item.data.size()
            ptr =  <const char *>&item.data[0]
            value = <bytearray> ptr[:data_size]

        data_size = item.name.size()
        ptr =  <const char *>&item.name[0]
        object_instance[ptr[:data_size].decode('macroman')] = value

# cdef print_property_sizes(Properties *p):
#     print("refs",           p.refs.size())
#     print("ints",           p.ints.size())
#     print("bools",          p.bools.size())
#     print("dates",          p.dates.size())
#     print("doubles",        p.doubles.size())
#     print("uuids",          p.uuids.size())
#     print("strings",        p.strings.size())
#     print("mob_ids",        p.mob_ids.size())
#     print("reflists",       p.reflists.size())
#     print("children",       p.children.size())
#     print("control_points", p.control_points.size())

def read_sequence_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_sequence(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading SEQU: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_sourceclip_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_sourceclip(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading SCLP: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_paramclip_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        p.refs.reserve(6)
        p.ints.reserve(6)
        ret = read_paramclip(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading PRCL: %s" % buf.error_message.decode("utf-8"))

    # print_property_sizes(&p)
    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_paramitem_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_paramitem(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading PRIT: %s" % buf.error_message.decode("utf-8"))

    # print_property_sizes(&p)
    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_trackref_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_trackref(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading TRKR: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_filler_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_filler(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading FILL: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def reads_selector_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_selector(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading SLCT: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_composition_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        p.ints.reserve(6)
        p.refs.reserve(7)
        p.strings.reserve(2)
        ret = read_composition(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading CMPO: %s" % buf.error_message.decode("utf-8"))

    # print_property_sizes(&p)
    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_media_descriptor_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_media_descriptor(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading MDES: %s" % buf.error_message.decode("utf-8"))

    # print_property_sizes(&p)
    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_did_descriptor_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_did_descriptor(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading DIDD: %s" % buf.error_message.decode("utf-8"))

    # print_property_sizes(&p)
    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result


def read_cdci_descriptor_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_cdci_descriptor(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading CDCI: %s" % buf.error_message.decode("utf-8"))

    # print_property_sizes(&p)
    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result

def read_trackeffect_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        p.refs.reserve(8)
        p.ints.reserve(12)
        ret = read_trackeffect(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading TKFX: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    # print_property_sizes(&p)
    object_instance.property_data = result

def read_effectparamlist_data(root, object_instance, const unsigned char[:] data):
    cdef Buffer buf
    buf.root = &data[0]
    buf.ptr =  &data[0]
    buf.end = &data[-1]
    buf.error_message = ""

    cdef Properties p
    cdef int ret
    with nogil:
        ret = read_effectparamlist(&buf, &p)

    if ret < 0:
        raise ValueError("Error reading FXPS: %s" % buf.error_message.decode("utf-8"))

    cdef dict result = process_poperties(root, &p)

    object_instance.property_data = result


READERS = {
b'CMPO': read_composition_data,
b'TKFX': read_trackeffect_data,
b'MDES': read_media_descriptor_data,
b'DIDD': read_did_descriptor_data,
b'CDCI': read_cdci_descriptor_data,
b'SLCT': reads_selector_data,
b"SEQU": read_sequence_data,
b'FILL': read_filler_data,
b'SCLP': read_sourceclip_data,
b'PRCL': read_paramclip_data,
b'PRIT': read_paramitem_data,
b'TRKR': read_trackref_data,
b'FXPS': read_effectparamlist_data,
b'ATTR': read_attr_data,
}
