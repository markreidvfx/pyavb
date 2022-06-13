#include <vector>
#include <math.h>

#ifdef _MSC_VER

#if _MSC_VER == 1500

    typedef unsigned char  uint8_t;
    typedef   signed char  int8_t;

    typedef unsigned short uint16_t;
    typedef   signed short int16_t;

    typedef   signed int   int32_t;
    typedef unsigned int   uint32_t;

    typedef   signed long long int  int64_t;
    typedef unsigned long long int uint64_t;

#endif
#endif

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
    const char *error_message;
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
    PARAM,
};

union IntDataValue {
    uint64_t u64;
    int64_t s64;
};

struct IntData {
    const char *name;
    bool is_signed;
    IntDataValue data;
};

struct DoubleData {
    const char *name;
    double data;
};

struct IntArrayData {
    const char *name;
    vector<int64_t> data;
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

struct AttrData {
    vector<uint8_t> name;
    AttrType type;
    uint32_t value;
    vector<uint8_t> data;
};

struct Properties {
    PropertyType type;
    vector<BoolData> bools;
    vector<IntData> refs;
    vector<IntData> dates;
    vector<IntData> ints;
    vector<DoubleData> doubles;
    vector<StringData> strings;
    struct ChildData {
        const char *name;
        PropertyType type;
        vector< Properties> data;
    };
    vector<RefListData> reflists;
    vector<ChildData> children;
    vector<BytesData> mob_ids;
    vector<BytesData> uuids;
    vector<ControlPointData> control_points;
    vector<IntArrayData> arrays;
    vector<BytesData> bytearrays;
};

static inline uint8_t read_u8(Buffer *f)
{
    if (f->ptr <= f->end)
        return *f->ptr++;
    return 0;
}

#define S1(x) #x
#define S2(x) S1(x)
#define ASSERT_MESSAGE "Assert error: " __FILE__ " : " S2(__LINE__)

#define read_assert_tag(f, value) \
    if (value != read_u8(f)) { \
        f->error_message = ASSERT_MESSAGE; \
        return -1; \
    } \

#define check(value) \
    if (value < 0) {  \
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

    return mantissa * pow(10.0, (int)exp10);
}

static inline void read_data32(Buffer *f, std::vector<uint8_t> &s)
{
    size_t size = read_u32le(f);
    s.resize(size);
    for(size_t i =0; i < size; i++) {
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


static inline void add_object_ref(Properties *p, const char* name, uint64_t value)
{
    IntData d = {};

    d.name = name;
    d.data.u64 = value;
    p->refs.push_back(d);
}

static inline void add_uint(Properties *p, const char* name, uint64_t value)
{
    IntData d = {};

    d.name = name;
    d.data.u64 = value;
    p->ints.push_back(d);
}

static inline void add_int(Properties *p, const char* name, int64_t value)
{
    IntData d = {};

    d.name = name;
    d.data.s64 = value;
    d.is_signed = true;
    p->ints.push_back(d);
}

static inline void add_double(Properties *p, const char* name, double value)
{
    DoubleData d = {};

    d.name = name;
    d.data = value;
    p->doubles.push_back(d);
}


static inline void add_date(Properties *p, const char* name, uint64_t value)
{
    IntData d = {};

    d.name = name;
    d.data.u64 = value;
    p->dates.push_back(d);
}

static inline void add_bool(Properties *p, const char* name, bool value)
{
    BoolData d = {};

    d.name = name;
    d.data = value;
    p->bools.push_back(d);
}

static inline int read_mob_id(Properties *p, Buffer *f, const char* name)
{
    BytesData mob_id;
    mob_id.name = name;
    mob_id.data.resize(32);
    uint8_t *m = &mob_id.data[0];

    read_assert_tag(f, 65);
    uint32_t smpte_label_len = read_u32le(f);

    if(smpte_label_len != 12) {
        fprintf(stderr, "mob_id smpte_label_len 12 != %d\n", smpte_label_len);
        f->error_message = ASSERT_MESSAGE;
        return -1;
    }

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
    uint32_t data4len = read_u32le(f);
    if(data4len != 8) {
        fprintf(stderr, "mob_id data4len 8 != %d\n", data4len);
        f->error_message = ASSERT_MESSAGE;
        return -1;
    }

    for (int i = 0; i < 8; i++) {
        *m++ = read_u8(f);
    }

    p->mob_ids.push_back(mob_id);

    return 0;
}

static inline int add_raw_uuid(Properties *p, const char * name, Buffer *f)
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

static inline vector<int64_t> & add_int_array(Properties *p, const char * name)
{
    p->arrays.push_back(IntArrayData());
    IntArrayData *d = &p->arrays[p->arrays.size()-1];
    d->name = name;
    return d->data;
}

static inline vector<uint8_t> & add_bytearray(Properties *p, const char * name)
{
    p->bytearrays.push_back(BytesData());
    BytesData *d = &p->bytearrays[p->bytearrays.size()-1];
    d->name = name;
    return d->data;
}


static int read_comp(Buffer *f, Properties *p)
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
                fprintf(stderr, "unknown ext tag: %d\n", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }

    return 0;
}

static int read_sequence(Buffer *f, Properties *p)
{
    read_comp(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x03);

    uint32_t count = read_u32le(f);
    p->reflists.push_back(RefListData());
    RefListData &reflist = p->reflists[p->reflists.size()-1];
    reflist.name = "components";
    reflist.data.reserve(count);
    for (size_t i =0; i < count; i++) {
        reflist.data.push_back(read_u32le(f));
    }

    read_assert_tag(f, 0x03);

    return 0;
}
static int read_clip(Buffer *f, Properties *p)
{
    read_comp(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);
    add_uint(p, "length", read_u32le(f)); // should this be a int?

    return 0;
}

static int read_filler(Buffer *f, Properties *p)
{
    read_clip(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    read_assert_tag(f, 0x03);
    return 0;
}

static int read_sourceclip(Buffer *f, Properties *p)
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
                fprintf(stderr, "unknown ext tag: %d\n", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }

    read_assert_tag(f, 0x03);

    return 0;
}

static int read_paramclip(Buffer *f, Properties *p)
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

    for (size_t i=0; i < point_count; i++) {
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
                fprintf(stderr, "unknown value_type: %d\n", value_type);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }

        uint16_t pp_count = read_u16le(f);
        cp->pp.resize(pp_count);
        for(int j = 0; j < pp_count; j++) {
            PerPoint *pp = &cp->pp[j];
            pp->code = (int16_t)read_u16le(f);
            pp->type = (ControlPointValueType)read_u16le(f);
            switch (pp->type) {
                case CP_TYPE_INT:
                    cp->value = read_u32le(f);
                    break;
                case CP_TYPE_DOUBLE:
                    cp->double_value = read_double_le(f);
                    break;
                default:
                    fprintf(stderr, "unknown value_type: %d\n", pp->type);
                    f->error_message = ASSERT_MESSAGE;
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
                fprintf(stderr, "unknown ext tag: %d\n", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }
    read_assert_tag(f, 0x03);

    return 0;
}

static int read_paramitem(Buffer *f, Properties *p)
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
            fprintf(stderr, "unknown value_type: %d\n", value_type);
            f->error_message = ASSERT_MESSAGE;
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
                fprintf(stderr, "unknown ext tag: %d", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }
    read_assert_tag(f, 0x03);
    return 0;
}

static int read_trackref(Buffer *f, Properties *p)
{
    read_clip(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    add_int(p, "relative_scope", (int16_t)read_u16le(f));
    add_int(p, "relative_track", (int16_t)read_u16le(f));
    read_assert_tag(f, 0x03);

    return 0;
}

static int read_trackgroup(Buffer *f, Properties *p)
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
            fprintf(stderr, "Unknown Track Flag: %d\n", flags);
            f->error_message = ASSERT_MESSAGE;
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
                fprintf(stderr, "unknown ext tag: %d\n", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }

    return 0;
}

static int read_trackeffect(Buffer *f, Properties *p)
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
                fprintf(stderr, "unknown ext tag: %d\n", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }

    return 0;
}

static int read_selector(Buffer *f, Properties *p)
{
    read_trackgroup(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    add_bool(p, "is_ganged", read_bool(f));
    add_uint(p, "selected",  read_u16le(f));

    read_assert_tag(f, 0x03);

    return 0;
}

static int read_composition(Buffer *f, Properties *p)
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
                fprintf(stderr, "unknown ext tag: %d\b",tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }

    read_assert_tag(f, 0x03);

    return 0;
}

static int read_media_descriptor(Buffer *f,  Properties *p)
{
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x03);

    add_uint(p, "mob_kind", read_u8(f));
    add_object_ref(p, "locator", read_u32le(f));
    add_bool(p, "intermediate", read_bool(f));
    add_object_ref(p, "physical_media", read_u32le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);

        if(tag == 0x01) {
            read_assert_tag(f, 65);
            uint32_t uuid_len = read_u32le(f);
            if (uuid_len != 16) {
                fprintf(stderr, "bad uuid len: %d\n", uuid_len);
                f->error_message = ASSERT_MESSAGE;
                return -1;
            }
            add_raw_uuid(p, "uuid",f);
        } else if (tag== 0x02) {
            read_assert_tag(f, 65);
            vector<uint8_t> &data = add_bytearray(p, "wchar");
            read_data32(f, data);
        } else if (tag == 0x03 ) {
            read_assert_tag(f, 72);
            add_object_ref(p, "attributes", read_u32le(f));
        } else {
            fprintf(stderr, "unknown ext tag: %d\n", tag);
            f->error_message = ASSERT_MESSAGE;
            return -1;
        }

    }
    return 0;
}

static int read_media_file_descriptor(Buffer *f,  Properties *p)
{
    check(read_media_descriptor(f, p));
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x03);

    add_double(p, "edit_rate", read_exp10_encoded_float(f));
    add_int(p, "length",      (int32_t)read_u32le(f));
    add_int(p, "is_omfi",     (int16_t)read_u16le(f));
    add_int(p, "data_offset", (int32_t)read_u32le(f));

    return 0;
}

static int read_did_descriptor(Buffer *f,  Properties *p)
{
    read_media_file_descriptor(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x02);

    add_int(p, "stored_height",      (int32_t)read_u32le(f));
    add_int(p, "stored_width",       (int32_t)read_u32le(f));

    add_int(p, "sampled_height",     (int32_t)read_u32le(f));
    add_int(p, "sampled_width",      (int32_t)read_u32le(f));

    add_int(p, "sampled_x_offset",   (int32_t)read_u32le(f));
    add_int(p, "sampled_y_offset",   (int32_t)read_u32le(f));

    add_int(p, "display_height",     (int32_t)read_u32le(f));
    add_int(p, "display_width",      (int32_t)read_u32le(f));

    add_int(p, "display_x_offset",   (int32_t)read_u32le(f));
    add_int(p, "display_y_offset",   (int32_t)read_u32le(f));

    add_int(p, "frame_layout",       (int16_t)read_u16le(f));

    vector<int64_t> &aspect = add_int_array(p, "aspect_ratio");
    aspect.push_back((int32_t)read_u32le(f));
    aspect.push_back((int32_t)read_u32le(f));

    vector<int64_t> &line_map = add_int_array(p, "line_map");

    size_t line_map_byte_size = read_u32le(f);
    for (size_t i = 0; i < line_map_byte_size/4; i++) {
        line_map.push_back((int32_t)read_u32le(f));
    }

    add_int(p, "alpha_transparency",   (int32_t)read_u32le(f));
    add_bool(p, "uniformness",         read_bool(f));
    add_int(p, "did_image_size",       (int32_t)read_u32le(f));

    add_object_ref(p, "next_did_desc", read_u32le(f));

    vector<uint8_t> &compress_method = add_bytearray(p, "compress_method");
    compress_method.resize(4);
    compress_method[3] = read_u8(f);
    compress_method[2] = read_u8(f);
    compress_method[1] = read_u8(f);
    compress_method[0] = read_u8(f);

    add_int(p, "resolution_id",          (int32_t)read_u32le(f));
    add_int(p, "image_alignment_factor", (int32_t)read_u32le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);

        if(tag == 0x01) {
            read_assert_tag(f, 69);
            add_int(p, "frame_index_byte_order", (int16_t)read_u16le(f));

        } else if (tag == 0x02) {
            read_assert_tag(f, 71);
            add_int(p, "frame_sample_size", (int32_t)read_u32le(f));

        } else if (tag == 0x03) {
            read_assert_tag(f, 71);
            add_int(p, "first_frame_offset", (int32_t)read_u32le(f));

        } else if (tag == 0x04) {
            read_assert_tag(f, 71);
            add_int(p, "client_fill_start", (int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            add_int(p, "client_fill_end", (int32_t)read_u32le(f));

        } else if (tag == 0x05) {
            read_assert_tag(f, 71);
            add_int(p, "offset_to_rle_frame_index", (int32_t)read_u32le(f));

        } else if (tag == 0x06) {
            read_assert_tag(f, 71);
            add_int(p, "frame_start_offset", (int32_t)read_u32le(f));

        } else if (tag == 0x08) {
            vector<int64_t> &valid_box = add_int_array(p, "valid_box");
            valid_box.reserve(8);

            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            valid_box.push_back((int32_t)read_u32le(f));

            vector<int64_t> &essence_box = add_int_array(p, "essence_box");
            essence_box.reserve(8);

            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            essence_box.push_back((int32_t)read_u32le(f));

            vector<int64_t> &source_box = add_int_array(p, "source_box");
            source_box.reserve(8);

            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            source_box.push_back((int32_t)read_u32le(f));

        } else if (tag == 9) {
            vector<int64_t> &framing_box = add_int_array(p, "framing_box");
            framing_box.reserve(8);

            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));
            read_assert_tag(f, 71);
            framing_box.push_back((int32_t)read_u32le(f));

            read_assert_tag(f, 71);
            add_int(p, "reformatting_option", (int32_t)read_u32le(f));

        } else if (tag == 10) {
            read_assert_tag(f, 80);
            add_raw_uuid(p, "transfer_characteristic", f);

        } else if (tag == 11) {
            read_assert_tag(f, 80);
            add_raw_uuid(p, "color_primaries", f);
            read_assert_tag(f, 80);
            add_raw_uuid(p, "coding_equations", f);

        } else if (tag == 12) {
            read_assert_tag(f, 80);
            add_raw_uuid(p, "essence_compression", f);

        } else if (tag == 14) {
            read_assert_tag(f, 68);
            add_int(p, "essence_element_size_kind", read_u8(f));

        } else if (tag == 15) {
            read_assert_tag(f, 66);
            add_bool(p, "frame_checked_with_mapper", read_bool(f));
        } else {
            fprintf(stderr, "unknown tag: %d\n", tag);
            f->error_message = ASSERT_MESSAGE;
            return -1;
        }
    }

    return 0;
}

static int read_cdci_descriptor(Buffer *f, Properties *p)
{
    read_did_descriptor(f, p);
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x02);

    add_uint(p, "horizontal_subsampling", read_u32le(f));
    add_uint(p, "vertical_subsampling", read_u32le(f));
    add_uint(p, "component_width", read_u32le(f));

    add_int(p, "color_sitting", (int16_t)read_u16le(f));
    add_uint(p, "black_ref_level", read_u32le(f));
    add_uint(p, "white_ref_level", read_u32le(f));
    add_uint(p, "color_range", read_u32le(f));

    add_int(p, "frame_index_offset", (int64_t)read_u64le(f));

    while (iter_ext(f)) {
        uint8_t tag = read_u8(f);
        switch (tag) {
            case 0x01:
                read_assert_tag(f, 72);
                add_uint(p, "alpha_sampled_width", read_u32le(f));
                break;
            case 0x02:
                read_assert_tag(f, 72);
                add_uint(p, "ignore_bw", read_u32le(f));
                break;
            default:
                fprintf(stderr, "unknown tag type: %d\n", tag);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
    }
    read_assert_tag(f, 0x03);
    return 0;
}

static int read_effectparamlist(Buffer *f, Properties *p)
{
    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x12);

    add_int(p, "orig_length",    (int32_t)read_u32le(f));
    add_int(p, "window_offset",  (int32_t)read_u32le(f));

    uint32_t parameter_count = read_u32le(f);
    add_int(p, "keyframe_size",  (int32_t)read_u32le(f));

    p->children.push_back(Properties::ChildData());
    Properties::ChildData &child = p->children[ p->children.size()-1];
    child.name = "parameters";

    vector <Properties> &parameters = child.data;
    parameters.resize(parameter_count);

    for (size_t i = 0; i < parameter_count; i++) {

        Properties &param = parameters[i];
        param.type = PARAM;

        add_int(&param, "percent_time",  (int32_t)read_u32le(f));
        add_int(&param, "level",         (int32_t)read_u32le(f));
        add_int(&param, "pos_x",         (int32_t)read_u32le(f));
        add_int(&param, "floor_x",       (int32_t)read_u32le(f));
        add_int(&param, "ceil_x",        (int32_t)read_u32le(f));
        add_int(&param, "pos_y",         (int32_t)read_u32le(f));
        add_int(&param, "floor_y",       (int32_t)read_u32le(f));
        add_int(&param, "ceil_y",        (int32_t)read_u32le(f));
        add_int(&param, "scale_x",       (int32_t)read_u32le(f));
        add_int(&param, "scale_y",       (int32_t)read_u32le(f));

        add_int(&param, "crop_left",      (int32_t)read_u32le(f));
        add_int(&param, "crop_right",     (int32_t)read_u32le(f));
        add_int(&param, "crop_top",       (int32_t)read_u32le(f));
        add_int(&param, "crop_bottom",    (int32_t)read_u32le(f));

        vector<int64_t> &box = add_int_array(&param, "box");
        box.reserve(4);
        box.push_back((int32_t)read_u32le(f));
        box.push_back((int32_t)read_u32le(f));
        box.push_back((int32_t)read_u32le(f));
        box.push_back((int32_t)read_u32le(f));

        add_bool(&param, "box_xscale", read_bool(f));
        add_bool(&param, "box_yscale", read_bool(f));
        add_bool(&param, "box_xpos",   read_bool(f));
        add_bool(&param, "box_ypos",   read_bool(f));

        add_int(&param, "border_width",  (int32_t)read_u32le(f));
        add_int(&param, "border_soft",   (int32_t)read_u32le(f));

        add_int(&param, "splill_gain2",   (int16_t)read_u16le(f));
        add_int(&param, "splill_gain",    (int16_t)read_u16le(f));
        add_int(&param, "splill_soft2",   (int16_t)read_u16le(f));
        add_int(&param, "splill_soft",    (int16_t)read_u16le(f));

        add_int(&param, "enable_key_flags",   (int8_t)read_u8(f));

        uint32_t color_count =read_u32le(f);
        vector<int64_t> &colors = add_int_array(&param, "colors");
        colors.reserve(color_count);

        for (size_t j=0; j < color_count; j++) {
            colors.push_back((int32_t)read_u32le(f));
        }

        uint32_t param_size = read_u32le(f);
        vector<uint8_t> &user_param = add_bytearray(&param, "user_param");
        user_param.resize(param_size);
        for (size_t j=0; j < param_size; j++) {
            user_param[j] = read_u8(f);
        }

        add_bool(&param, "selected",   read_bool(f));

    }

    read_assert_tag(f, 0x03);

    return 0;
}

static int read_attributes(Buffer *f, std::vector<AttrData> &d)
{

    read_assert_tag(f, 0x02);
    read_assert_tag(f, 0x01);

    size_t attr_count = read_u32le(f);
    d.resize(attr_count);

    if (attr_count == 0)
        return 0;

    AttrData *ptr = &d[0];

    for(size_t i =0; i < attr_count; i++) {
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
                fprintf(stderr, "unknown attr type: %d\n", (uint32_t)ptr->type);
                f->error_message = ASSERT_MESSAGE;
                return -1;
        }
         ptr++;
    }
    read_assert_tag(f, 0x03);

    return 0;
}
