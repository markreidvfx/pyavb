#include <map>
#include <string>
#include <iostream>
#include <string>
#include <vector>
#include <math.h>

using namespace std;

#define TRACK_LABEL_FLAG            1 << 0
#define TRACK_ATTRIBUTES_FLAG       1 << 1
#define TRACK_COMPONENT_FLAG        1 << 2
#define TRACK_FILLER_PROXY_FLAG     1 << 3
#define TRACK_BOB_DATA_FLAG         1 << 4
#define TRACK_CONTROL_CODE_FLAG     1 << 5
#define TRACK_CONTROL_SUB_CODE_FLAG 1 << 6
#define TRACK_START_POS_FLAG        1 << 7
#define TRACK_READ_ONLY_FLAG        1 << 8
#define TRACK_SESSION_ATTR_FLAG     1 << 9

#define TRACK_UNKNOWN_FLAGS         0xFC00

struct Buffer {
  const uint8_t *root;
  const uint8_t *ptr;
  const uint8_t *end;
};

enum StringType {
    MACROMAN,
    UTF8,
};

enum AttrType {
    INT_ATTR = 1,
    STR_ATTR = 2,
    OBJ_ATTR = 3,
    BOB_ATTR = 4,
};

enum ControlPointValueType {
    CP_TYPE_INT = 1,
    CP_TYPE_DOUBLE = 2,
    CP_TYPE_REFERENCE = 4,
};

enum ControlPointType {
    ParamControlPointType,
};

enum PropertyType {
    TRKG,
    TRACK,
};

struct UIntData {
    const char *name;
    uint32_t data;
};

struct IntData {
    const char *name;
    int32_t data;
};

struct DoubleData {
    const char *name;
    double data;
};

struct UIntData64 {
    const char *name;
    uint64_t data;
};

struct IntData64 {
    const char *name;
    int64_t data;
};

struct BoolData {
    const char *name;
    int data;
};

struct BytesData {
    const char *name;
    vector<uint8_t> data;
};

struct PerPoint {
    int16_t code;
    ControlPointValueType type;
    uint32_t value;
    double double_value;
};

struct ControlPoint {
    int32_t offset_num;
    int32_t offset_den;
    int32_t timescale;

    uint32_t value;
    double double_value;
    vector<PerPoint> pp;
};

struct ControlPointData {
    const char *name;
    ControlPointType type;
    ControlPointValueType value_type;
    vector<ControlPoint> data;
};

struct StringData {
    const char *name;
    StringType type;
    vector<uint8_t> data;
};

struct RefListData {
    const char *name;
    vector<uint32_t> data;
};

struct MobIDData {
    const char *name;
    uint8_t data[32];
};

struct AttrData {
    vector<uint8_t> name;
    AttrType type;
    uint32_t value;
    vector<uint8_t> data;
};

struct Properties {
    PropertyType type;
    vector<BoolData> bools;
    vector<UIntData> refs;
    vector<UIntData> dates;
    vector<UIntData> int_unsigned;
    vector<IntData>  int_signed;
    vector<UIntData64> int_unsigned64;
    vector<IntData64>  int_signed64;
    vector<DoubleData> doubles;
    vector<StringData> strings;
    struct ChildData {
        const char *name;
        PropertyType type;
        vector< Properties> data;
    };
    vector<RefListData> reflists;
    vector<ChildData> children;
    vector<MobIDData > mob_ids;
    vector<BytesData> uuids;
    vector<ControlPointData> control_points;
};

static inline uint8_t read_u8(Buffer *f)
{
    if (f->ptr <= f->end)
        return *f->ptr++;
    return 0;
}

#define read_assert_tag(f, value) \
    if (value != read_u8(f)) { \
        cerr << "assert error: " <<  __FILE__ << ":" << __LINE__ << "\n"; \
        return -1; \
    } \

static inline bool read_bool(Buffer *f)
{
    return read_u8(f) == 0x01;
}

static inline uint16_t read_u16le(Buffer *f)
{
    uint16_t value;
    value =  read_u8(f);
    value |= read_u8(f) << 8;
    return value;
}

static inline uint32_t read_u32le(Buffer *f)
{
    uint32_t value;
    value =  read_u16le(f);
    value |= read_u16le(f) << 16;
    return value;
}

static inline uint64_t read_u64le(Buffer *f)
{
    uint64_t value1 = read_u32le(f);
    uint64_t value2 = read_u32le(f);
    return value1 | value2 << 32;
}

static inline double read_double_le(Buffer *f)
{
    uint64_t value = read_u64le(f);
    return *(double*)&value;
}

static inline double read_exp10_encoded_float(Buffer *f)
{
    int32_t mantissa = (int32_t)read_u32le(f);
    int16_t exp10 = (int16_t)read_u16le(f);

    return mantissa * pow(10, exp10);
}

static inline void read_data32(Buffer *f, std::vector<uint8_t> &s)
{
    uint32_t size = read_u32le(f);
    s.resize(size);
    for(int i =0; i < size; i++) {
        s[i] = read_u8(f);
    }
}

static inline void read_data16(Buffer *f, std::vector<uint8_t> &s)
{
    uint16_t size = read_u16le(f);
    if (size < 65535) {
        s.resize(size);
        for(int i =0; i < size; i++) {
            s[i] = read_u8(f);
        }
    }
}

static inline void add_string(Properties *p, Buffer *f, const char* name, StringType t)
{
    size_t string_size = p->strings.size();
    p->strings.resize(string_size + 1);
    StringData &s = p->strings[string_size];

    s.name = name;
    s.type = t;
    read_data16(f, s.data);
}

static inline bool iter_ext(Buffer *f) {
     uint8_t tag = read_u8(f);
     if (tag == 0x01)
        return true;

     f->ptr--;
     return false;
}


static inline void add_object_ref(Properties *p, const char* name, uint32_t value)
{
    UIntData d = {};

    d.name = name;
    d.data = value;
    p->refs.push_back(d);
}

static inline void add_uint(Properties *p, const char* name, uint32_t value)
{
    UIntData d = {};

    d.name = name;
    d.data = value;
    p->int_unsigned.push_back(d);
}

static inline void add_int(Properties *p, const char* name, int32_t value)
{
    IntData d = {};

    d.name = name;
    d.data = value;
    p->int_signed.push_back(d);
}

static inline void add_double(Properties *p, const char* name, double value)
{
    DoubleData d = {};

    d.name = name;
    d.data = value;
    p->doubles.push_back(d);
}


static inline void add_date(Properties *p, const char* name, uint32_t value)
{
    UIntData d = {};

    d.name = name;
    d.data = value;
    p->dates.push_back(d);
}

static inline void add_bool(Properties *p, const char* name, bool value)
{
    BoolData d = {};

    d.name = name;
    d.data = value;
    p->bools.push_back(d);
}

int read_mob_id(Properties *p, Buffer *f, const char* name)
{
    MobIDData mob_id;
    mob_id.name = name;

    uint8_t *m = &mob_id.data[0];

    read_assert_tag(f, 65);
    int smpte_label_len = read_u32le(f);
    if(smpte_label_len != 12)
    return -1;

    for (int i =0; i < 12; i++) {
        *m++ = read_u8(f);
    }

    read_assert_tag(f, 68);
    *m++ = read_u8(f);

    read_assert_tag(f, 68);
    *m++ = read_u8(f);

    read_assert_tag(f, 68);
    *m++ = read_u8(f);

    read_assert_tag(f, 68);
    *m++ = read_u8(f);

    //material
    read_assert_tag(f, 72);
    *m++ = read_u8(f);
    *m++ = read_u8(f);
    *m++ = read_u8(f);
    *m++ = read_u8(f);

    read_assert_tag(f, 70);
    *m++ = read_u8(f);
    *m++ = read_u8(f);

    read_assert_tag(f, 70);
    *m++ = read_u8(f);
    *m++ = read_u8(f);

    read_assert_tag(f, 65);
    int data4len = read_u32le(f);
    if(data4len != 8) {
        cerr << 'wtf\n';
        return -1;
    }

    for (int i = 0; i < 8; i++) {
        *m++ = read_u8(f);
    }

    p->mob_ids.push_back(mob_id);

    return 0;
}

int add_raw_uuid(Properties *p, const char * name, Buffer *f)
{
    p->uuids.push_back(BytesData());
    BytesData *d = &p->uuids[p->uuids.size()-1];
    d->name = name;
    d->data.resize(16);
    for(int i =0; i < 16; i++) {
        d->data[i] = read_u8(f);
    }

    return 0;
}


int read_comp(Buffer *f, Properties *p)
{
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x03);

    add_object_ref(p, "left_bob", read_u32le(f));
    add_object_ref(p, "right_bob", read_u32le(f));

    add_uint(p, "media_kind_id", read_u16le(f));

    add_double(p, "edit_rate", read_exp10_encoded_float(f));

    add_string(p, f, "name", MACROMAN);
    add_string(p, f, "effect_id", MACROMAN);

    add_object_ref(p, "attributes", read_u32le(f));
    add_object_ref(p, "session_attrs", read_u32le(f));
    add_object_ref(p, "precomputed", read_u32le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                read_assert_tag(f, 72);
                add_object_ref(p, "param_list", read_u32le(f));
                break;
            default:
                cerr << "unknown ext tag: " << tag << "\n";
                break;
        }
    }

    return 0;
}

int read_sequence(Buffer *f, Properties *p)
{
    read_comp(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x03);

    uint32_t count = (int32_t)read_u32le(f);
    p->reflists.push_back(RefListData());
    RefListData &reflist = p->reflists[p->reflists.size()-1];
    reflist.name = "components";
    reflist.data.reserve(count);
    for (int i =0; i < count; i++) {
        reflist.data.push_back(read_u32le(f));
    }

    read_assert_tag(f, 0x03);

    return 0;
}
int read_clip(Buffer *f, Properties *p)
{
    read_comp(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);
    add_int(p, "length", (int32_t)read_u32le(f));

    return 0;
}

int read_filler(Buffer *f, Properties *p)
{
    read_clip(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    read_assert_tag(f, 0x03);
    return 0;
}

int read_sourceclip(Buffer *f, Properties *p)
{
    read_clip(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x03);

    //mob_id_hi
    read_u32le(f);
    //mob_id_lo
    read_u32le(f);

    add_int(p, "track_id", (int16_t)read_u16le(f));
    add_int(p, "start_time", (int32_t)read_u32le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                read_mob_id(p, f, "mob_id");
                break;
            default:
                cerr << "unknown ext tag: " << (uint32_t)tag << "\n";
                break;
        }
    }

    read_assert_tag(f, 0x03);

    return 0;
}

int read_paramclip(Buffer *f, Properties *p)
{
    read_clip(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    add_int(p, "interp_kind", (int32_t)read_u32le(f));

    ControlPointValueType value_type = (ControlPointValueType)read_u16le(f);
    add_int(p, "value_type", value_type);

    uint32_t point_count = read_u32le(f);

    p->control_points.resize(1);
    ControlPointData *cp_data = &p->control_points[0];
    cp_data->name = "control_points";
    cp_data->type = ParamControlPointType;
    cp_data->value_type = value_type;
    cp_data->data.resize(point_count);

    for (int i=0; i < point_count; i++) {
        ControlPoint *cp = &cp_data->data[i];
        cp->offset_num = (int32_t)read_u32le(f);
        cp->offset_den = (int32_t)read_u32le(f);
        cp->timescale =  (int32_t)read_u32le(f);

        switch (value_type) {
            case CP_TYPE_INT:
                cp->value = read_u32le(f);
                break;
            case CP_TYPE_DOUBLE:
                cp->double_value = read_double_le(f);
                break;
            case CP_TYPE_REFERENCE:
                cp->value = read_u32le(f);
                break;
            default:
                cerr << "unknown value_type: " << (uint32_t)value_type << "\n";
                return -1;
        }

        int16_t pp_count = read_u16le(f);
        cp->pp.resize(pp_count);
        for(int j = 0; j < pp_count; j++) {
            PerPoint *pp = &cp->pp[0];
            pp->code = read_u16le(f);
            pp->type = (ControlPointValueType)read_u16le(f);
            switch (pp->type) {
                case CP_TYPE_INT:
                    cp->value = read_u32le(f);
                    break;
                case CP_TYPE_DOUBLE:
                    cp->double_value = read_double_le(f);
                    break;
                default:
                    cerr << "unknown value_type: " << (uint32_t)pp->type << "\n";
                    return -1;
            }
        }
    }
    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                read_assert_tag(f, 71);
                add_int(p, "extrap_kind", (int32_t)read_u32le(f));
                break;
            case 0x02:
                read_assert_tag(f, 71);
                add_int(p, "fields", (int32_t)read_u32le(f));
                break;
            default:
                cerr << "unknown ext tag: " << tag << "\n";
                return -1;
        }
    }
    read_assert_tag(f, 0x03);

    return 0;
}

int read_paramitem(Buffer *f, Properties *p)
{
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x02);
    add_raw_uuid(p, "uuid", f);

    int16_t value_type = read_u16le(f);
    add_int(p, "value_type", value_type);
    switch (value_type) {
        case 1:
            add_int(p, "value", (int32_t)read_u32le(f));
            break;
        case 2:
            add_double(p, "value", read_double_le(f));
            break;
        case 4:
            add_object_ref(p, "value", read_u32le(f));
            break;
        default:
            cerr << "unknown value_type: " << (uint32_t)value_type << "\n";
            return -1;
    }

    add_string(p, f, "name", MACROMAN);
    add_bool(p, "enable", read_bool(f));
    add_object_ref(p, "control_track", read_u32le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                read_assert_tag(f, 66);
                add_bool(p, "contribs_to_sig", read_bool(f));
                break;
            default:
                cerr << "unknown ext tag: " << tag << "\n";
                return -1;
        }
    }
    read_assert_tag(f, 0x03);
    return 0;
}

int read_trackref(Buffer *f, Properties *p)
{
    read_clip(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    add_int(p, "relative_scope", (int16_t)read_u16le(f));
    add_int(p, "relative_track", (int16_t)read_u16le(f));
    read_assert_tag(f, 0x03);

    return 0;
}

int read_trackgroup(Buffer *f, Properties *p)
{
    read_comp(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x08);

    add_int(p, "mc_mode", read_u8(f));
    add_int(p, "length", (int32_t)read_u32le(f));
    add_int(p, "num_scalars", (int32_t)read_u32le(f));

    int32_t track_count =  (int32_t)read_u32le(f);

    p->children.push_back(Properties::ChildData());
    Properties::ChildData &child = p->children[ p->children.size()-1];
    child.name = "tracks";
    vector <Properties> &tracks = child.data;
    tracks.resize(track_count);

    for (int i = 0; i < track_count; i++) {
        Properties &track = tracks[i];
        track.type = TRACK;
        uint16_t flags = read_u16le(f);

        if (flags & TRACK_LABEL_FLAG)
            add_int(&track, "index", (int16_t)read_u16le(f));

        if (flags & TRACK_ATTRIBUTES_FLAG)
            add_object_ref(&track, "attributes", read_u32le(f));

        if (flags & TRACK_SESSION_ATTR_FLAG)
            add_object_ref(&track, "session_attr", read_u32le(f));

        if (flags & TRACK_COMPONENT_FLAG)
            add_object_ref(&track, "component", read_u32le(f));

        if (flags & TRACK_FILLER_PROXY_FLAG)
            add_object_ref(&track, "filler_proxy", read_u32le(f));

        if (flags & TRACK_BOB_DATA_FLAG)
            add_object_ref(&track, "bob_data", read_u32le(f));

        if (flags & TRACK_CONTROL_CODE_FLAG)
            add_int(&track, "control_code", (int16_t)read_u16le(f));

        if (flags & TRACK_CONTROL_SUB_CODE_FLAG)
            add_int(&track, "control_sub_code", (int16_t)read_u16le(f));

        if (flags & TRACK_START_POS_FLAG)
            add_int(&track, "start_pos",  (int32_t)read_u32le(f));

        if (flags & TRACK_READ_ONLY_FLAG)
            add_bool(&track, "read_only", read_bool(f));

        if (flags & TRACK_UNKNOWN_FLAGS) {
            cerr << "Unknown Track Flag: " << flags << "\n";
            return -1;
        }
            // raise ValueError("Unknown Track Flag: %d" % flags)
    }

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                for (int i = 0; i < track_count; i++) {
                    read_assert_tag(f, 69);
                    add_int(&tracks[i], "lock_number", (int16_t)read_u16le(f));
                }
                break;
            default:
                cerr << "unknown ext tag: " << tag << "\n";
                break;
        }
    }

    return 0;
}

int read_trackeffect(Buffer *f, Properties *p)
{
    read_trackgroup(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x06);

    add_int(p, "left_length",       (int32_t)read_u32le(f));
    add_int(p, "right_length",      (int32_t)read_u32le(f));

    add_int(p, "info_version",      (int16_t)read_u16le(f));
    add_int(p, "info_current",      (int32_t)read_u32le(f));
    add_int(p, "info_smooth",       (int32_t)read_u32le(f));
    add_int(p, "info_color_item",   (int16_t)read_u16le(f));
    add_int(p, "info_quality",      (int16_t)read_u16le(f));
    add_int(p, "info_is_reversed",  (int8_t)read_u8(f));
    add_bool(p, "info_aspect_on",   read_bool(f));

    add_object_ref(p, "keyframes",       read_u32le(f));
    add_bool(p, "info_force_software",   read_bool(f));
    add_bool(p, "info_never_hardware",   read_bool(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x02:
                read_assert_tag(f, 72);
                add_object_ref(p, "trackman", read_u32le(f));
                break;
            default:
                cerr << "unknown ext tag: " << (uint32_t)tag << "\n";
                return -1;
        }
    }

    return 0;
}

int read_selector(Buffer *f, Properties *p)
{
    read_trackgroup(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    add_bool(p, "is_ganged", read_bool(f));
    add_uint(p, "selected",  read_u16le(f));

    read_assert_tag(f, 0x03);

    return 0;
}

int read_composition(Buffer *f, Properties *p)
{
    read_trackgroup(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x02);

    //mob_hi
    read_u32le(f);
    //mob_lo
    read_u32le(f);

    add_date(p, "last_modified", read_u32le(f));
    add_uint(p, "mob_type_id", read_u8(f));
    add_int(p, "usage_code", read_u32le(f));
    add_object_ref(p, "descriptor", read_u32le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                read_assert_tag(f, 71);
                add_date(p, "creation_time", read_u32le(f));
                break;
            case 0x02:
                read_mob_id(p, f, "mob_id");
                break;
            default:
                cerr << "unknown ext tag: " << (uint32_t)tag << "\n";
                return -1;
        }
    }

    read_assert_tag(f, 0x03);

    return 0;
}

int read_attributes(Buffer *f, std::vector<AttrData> &d)
{

    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    uint32_t attr_count = read_u32le(f);
    d.resize(attr_count);

    AttrData *ptr = &d[0];

    for(int i =0; i < attr_count; i++) {
        ptr->type = (AttrType)read_u32le(f);
        read_data16(f, ptr->name);
        switch (ptr->type) {
            case INT_ATTR:
                ptr->value = read_u32le(f);
                break;
            case STR_ATTR:
                read_data16(f, ptr->data);
                break;
            case OBJ_ATTR:
                ptr->value = read_u32le(f);
                break;
            case BOB_ATTR:
                read_data32(f, ptr->data);
                break;
            default:
                cerr << "unknown attr type: " << (uint32_t)ptr->type << "\n";
                return -1;
        }
         ptr++;
    }
    read_assert_tag(f, 0x03);

    return 0;
}
