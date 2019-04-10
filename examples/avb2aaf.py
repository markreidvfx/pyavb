from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import avb
import aaf2
from aaf2.rational import AAFRational
from aaf2.mobid import MobID
import sys
from uuid import UUID
import urllib

def register_definitions(f):
    op_def = f.create.OperationDef('89d9b67e-5584-302d-9abd-8bd330c46841', 'VideoDissolve_2', '')
    f.dictionary.register_def(op_def)

    op_def.media_kind = 'picture'
    op_def['IsTimeWarp'].value = False
    op_def['Bypass'].value = 1
    op_def['NumberInputs'].value = 2
    op_def['OperationCategory'].value = 'OperationCategory_Effect'

    param_byteorder = f.create.ParameterDef("c0038672-a8cf-11d3-a05b-006094eb75cb", "AvidParameterByteOrder", "", 'aafUInt16')
    f.dictionary.register_def(param_byteorder)

    param_effect_id = f.create.ParameterDef("93994bd6-a81d-11d3-a05b-006094eb75cb", "AvidEffectID", "", 'AvidBagOfBits')
    f.dictionary.register_def(param_effect_id)

    op_def.parameters.extend([param_byteorder, param_effect_id])

    # note not part of VideoDissolve_2 op_def but still used...
    opacity_param = f.create.ParameterDef('8d56813d-847e-11d5-935a-50f857c10000', 'AFX_FG_KEY_OPACITY_U', '', 'Rational')
    f.dictionary.register_def(opacity_param)

    linear = f.create.InterpolationDef('5b6c85a4-0ede-11d3-80a9-006008143e6f', 'LinearInterp', '')
    f.dictionary.register_def(linear)

    cubic = f.create.InterpolationDef('a04a5439-8a0e-4cb7-975f-a5b255866883', 'AvidCubicInterpolator', '')
    f.dictionary.register_def(cubic)

    constant = f.create.InterpolationDef('5b6c85a5-0ede-11d3-80a9-006008143e6f', 'ConstantInterp', '')
    f.dictionary.register_def(constant)

    bezier = f.create.InterpolationDef('df394eda-6ac6-4566-8dbe-f28b0bdd781a', 'AvidBezierInterpolator', '')
    f.dictionary.register_def(bezier)

    nointerp = f.create.InterpolationDef('5b6c85a3-0ede-11d3-80a9-006008143e6f', 'NoInterp', '')
    f.dictionary.register_def(nointerp)

    op_def = f.create.OperationDef('0c3bea41-fc05-11d2-8a29-0050040ef7d2', 'Audio Dissolve', '')
    f.dictionary.register_def(op_def)

    op_def.media_kind = 'sound'
    op_def['IsTimeWarp'].value = False
    op_def['Bypass'].value = 1
    op_def['NumberInputs'].value = 2
    op_def['OperationCategory'].value = 'OperationCategory_Effect'
    op_def.parameters.extend([param_byteorder, param_effect_id])

    op_def = f.create.OperationDef('9d2ea890-0968-11d3-8a38-0050040ef7d2', 'Motion Control', '')
    f.dictionary.register_def(op_def)

    op_def.media_kind = 'picture'
    op_def['IsTimeWarp'].value = True
    op_def['Bypass'].value = 0
    op_def['NumberInputs'].value = 1
    op_def['OperationCategory'].value = 'OperationCategory_Effect'


    param = f.create.ParameterDef("f7ffed29-fc8e-43ed-943a-4b57b5c157ee", "AvidMotionPulldown", "", 'aafInt32')
    f.dictionary.register_def(param)
    op_def.parameters.append(param)

    param = f.create.ParameterDef("8dde1839-6862-4874-a1e9-4fbd1164f22a", "AvidMotionOutputFormat", "", 'aafInt32')
    f.dictionary.register_def(param)
    op_def.parameters.append(param)

    param = f.create.ParameterDef("5b22ff71-c51b-11d3-a069-006094eb75cb", "AvidPhase", "", 'aafInt32')
    f.dictionary.register_def(param)
    op_def.parameters.append(param)

    param = f.create.ParameterDef("72559a80-24d7-11d3-8a50-0050040ef7d2", "SpeedRatio", "", 'Rational')
    f.dictionary.register_def(param)
    op_def.parameters.append(param)

    param = f.create.ParameterDef("1c5a02d5-e503-4ca6-8617-d7914bb8ac03", "AvidMotionInputFormat", "", 'Rational')
    f.dictionary.register_def(param)
    op_def.parameters.append(param)

    # used on Motion Control but not part of op_def
    param = f.create.ParameterDef("8d56827c-847e-11d5-935a-50f857c10000", "PARAM_SPEED_MAP_U", "", 'Rational')
    f.dictionary.register_def(param)

    param = f.create.ParameterDef("8d56827d-847e-11d5-935a-50f857c10000", "PARAM_SPEED_OFFSET_MAP_U", "", 'Rational')
    f.dictionary.register_def(param)

    param = f.create.ParameterDef("8d568283-847e-11d5-935a-50f857c10000", "PARAM_PULLDOWN_PHASE_U", "", 'Rational')
    f.dictionary.register_def(param)

    param = f.create.ParameterDef('8d56830e-847e-11d5-935a-50f857c10000', 'PP_IN_TANGENT_POS_U',  '', 'Rational')
    f.dictionary.register_def(param)
    param = f.create.ParameterDef('8d56830f-847e-11d5-935a-50f857c10000', 'PP_IN_TANGENT_VAL_U',  '', 'Rational')
    f.dictionary.register_def(param)
    param = f.create.ParameterDef('8d568310-847e-11d5-935a-50f857c10000', 'PP_OUT_TANGENT_POS_U', '', 'Rational')
    f.dictionary.register_def(param)
    param = f.create.ParameterDef('8d568311-847e-11d5-935a-50f857c10000', 'PP_OUT_TANGENT_VAL_U', '', 'Rational')
    f.dictionary.register_def(param)
    param = f.create.ParameterDef('8d568312-847e-11d5-935a-50f857c10000', 'PP_TANGENT_MODE_U',    '', 'Rational')
    f.dictionary.register_def(param)
    param = f.create.ParameterDef('8d568313-847e-11d5-935a-50f857c10000', 'PP_BASE_FRAME_U',      '', 'Rational')
    f.dictionary.register_def(param)

    op_def = f.create.OperationDef('2db619ef-7210-4e89-95d7-970336d72e8c', 'Title_2', "")
    op_def.media_kind = 'picture'
    op_def['NumberInputs'].value = 3
    op_def['IsTimeWarp'].value = False
    op_def['Bypass'].value = 0
    op_def['OperationCategory'].value = "OperationCategory_Effect"
    f.dictionary.register_def(op_def)

    param = f.create.ParameterDef('1fdd2907-e48c-11d3-a078-006094eb75cb', 'AvidGraphicFXAttr', '', 'AvidBagOfBits')
    f.dictionary.register_def(param)

    op_def.parameters.extend([param, param_byteorder, param_effect_id])

def nice_edit_rate(rate):
    if rate == 24:
        return "24/1"
    elif rate ==  23.976:
        return "24000/1001"
    elif rate == 30:
        return "30/1"

    return "%d/%d" % (int(rate * 1000), 1000)

def pretty_value(value):
    if isinstance(value, bytearray):
        return "bytearray(%d)" % len(value)
        # return ''.join(format(x, '02x') for x in value)
    return value


def avb_dump(obj, space=""):

    propertie_keys = []
    property_data = None
    if isinstance(obj, avb.core.AVBObject):
        print(space, unicode(obj))
        space += "  "
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
    else:
        print(space, obj)
        return

    for key in propertie_keys:
        value = property_data[key]
        if isinstance(value, (avb.core.AVBObject, dict)):
            print("%s%s:" % (space, key))
            avb_dump(value, space + " ")
        elif isinstance(value, list):
            print("%s%s:" % (space, key))
            for item in value:
                avb_dump(item, space + " ")
        else:
            if value is not None:
                print("%s%s:" % (space, key), pretty_value(value))

def convert_descriptor(d, aaf_file):
    descriptor = None
    if type(d) is avb.essence.MediaDescriptor:
        descriptor = aaf_file.create.ImportDescriptor()

    elif type(d) is avb.essence.TapeDescriptor:
        descriptor = aaf_file.create.TapeDescriptor()

    elif type(d) is avb.essence.PCMADescriptor:
        descriptor = aaf_file.create.PCMDescriptor()
        descriptor['AverageBPS'].value = d.average_bps
        descriptor['BlockAlign'].value = d.block_align
        descriptor["SampleRate"].value = nice_edit_rate(d.sample_rate)
        descriptor["AudioSamplingRate"].value = nice_edit_rate(d.sample_rate)
        descriptor["QuantizationBits"].value = d.quantization_bits

        descriptor["Channels"].value = 1

    elif isinstance(d, avb.essence.DIDDescriptor):
        if type(d) is avb.essence.CDCIDescriptor:
            descriptor = aaf_file.create.CDCIDescriptor()
            descriptor['ComponentWidth'].value = d.component_width
            descriptor['HorizontalSubsampling'].value = d.horizontal_subsampling
            descriptor['VerticalSubsampling'].value = d.vertical_subsampling
            descriptor['ResolutionID'].value = d.resolution_id
            descriptor['ImageAlignmentFactor'].value = d.image_alignment_factor
            # avb_dump(d)

        elif type(d) is avb.essence.RGBADescriptor:
            descriptor = aaf_file.create.RGBADescriptor()
            descriptor['PixelLayout'].value = d.pixel_layout
        else:
            avb_dump(d)
            raise ValueError("unhandled digtial image descriptor")

        descriptor['StoredHeight'].value = d.stored_height
        descriptor['StoredWidth'].value = d.stored_width
        descriptor['ImageAspectRatio'].value = "{}/{}".format(*d.aspect_ratio)
        descriptor['FrameLayout'].value = d.frame_layout
        descriptor['VideoLineMap'].value = d.line_map
        descriptor['SampleRate'].value = 0

    elif isinstance(d, avb.essence.MultiDescriptor):
        descriptor = aaf_file.create.MultipleDescriptor()
        descriptor['SampleRate'].value = 0
        for item in d.descriptors:
            descriptor['FileDescriptors'].append(convert_descriptor(item, aaf_file))
    else:
        avb_dump(d)
        raise ValueError("unhandle descriptor")

    if hasattr(d, 'length'):
        descriptor["Length"].value = d.length

    if d.physical_media:
        loc = d.physical_media.locator
        path = loc.path
        url = "file:///"+ urllib.pathname2url(path)
        n = aaf_file.create.NetworkLocator()
        n['URLString'].value = url
        descriptor['Locator'].append(n)

    return descriptor

def remap_track_id(track_id, media_kind,  avb_mob):
    for i,track in enumerate(iter_tracks(avb_mob)):
        if track_id == track.index and media_kind == track.component.media_kind:
            return i+1

    raise Exception()

def iter_tracks(avb_mob):
    track_types = ('picture', 'sound','edgecode', 'timecode', 'DescriptiveMetadata')
    track_dict = {}
    for track in avb_mob.tracks:
        media_kind = track.component.media_kind
        if media_kind not in track_dict:
            track_dict[media_kind] = []
        track_dict[media_kind].append(track)

    for track_type in track_types:
        tracks = track_dict.get(track_type, [])
        for track in tracks:
            yield track

def zero_mob_id(mob_id):
    material = mob_id.material.uuid
    lo = material.time_low
    hi = material.time_mid + (material.time_hi_version << 16)
    if lo == 0 and hi == 0:
        return True
    return False

def check_source_clip(f, avb_source_clip):
    mob_id = MobID(bytes_le=avb_source_clip.mob_id.bytes_le)
    if zero_mob_id(mob_id):
        return 0
    avb_mob = avb_source_clip.root.content.mob_dict[avb_source_clip.mob_id]
    if mob_id in f.content.mobs:
        mob = f.content.mobs[mob_id]
    else:
        mob = convert_composition(f, avb_mob)

    try:
        slot_id = remap_track_id(avb_source_clip.track_id, avb_source_clip.media_kind, avb_mob)
        source_slot = mob.slot_at(slot_id)
    except:
        avb_dump(avb_mob)
        avb_dump(avb_source_clip)
        for i, track in enumerate(avb_mob.tracks):
            print(i+1, track.index, track.component.media_kind)

        for slot in mob.slots:
            print(slot)

        print(avb_source_clip.track_id, avb_source_clip.media_kind)
        raise

    return slot_id

def convert_source_clip(f, avb_source_clip):
    slot_id = check_source_clip(f, avb_source_clip)

    mob_id = MobID(bytes_le= avb_source_clip.mob_id.bytes_le)
    if zero_mob_id(mob_id):
        mob_id = MobID()

    aaf_component = f.create.SourceClip()
    aaf_component['SourceID'].value = mob_id
    aaf_component['StartTime'].value = avb_source_clip.start_time
    aaf_component['SourceMobSlotID'].value = slot_id

    return aaf_component

def convert_sequence(aaf_file, avb_sequence):
    aaf_sequence = aaf_file.create.Sequence()
    for avb_component in avb_sequence.components:
        # avb puts 0 length filler on head and tail of sequence
        if avb_component.length <= 0:
            continue

        aaf_sequence.components.append(convert_component(aaf_file, avb_component))

    return aaf_sequence

def convert_selector(f, avb_selector):

    selector = f.create.Selector()
    selected = avb_selector.selected
    selected_clip = None
    for i, item in enumerate(avb_selector.components()):
        clip =  convert_component(f, item)
        if i == selected:
            selected_clip =clip
        else:
            selector['Alternates'].append(clip)
    assert selected_clip
    selector['Selected'].value = selected_clip

    return selector

def convert_transistion(f, avb_transistion):
    transition = f.create.Transition()

    transition['CutPoint'].value = 0
    if avb_transistion.media_kind == 'picture':
        op_group = f.create.OperationGroup('VideoDissolve_2')
    else:
        op_group = f.create.OperationGroup('Audio Dissolve')

    transition['OperationGroup'].value = op_group

    return transition

def convert_capture_mask(f, capture_mask):
    return convert_component(f, capture_mask.tracks[0].component)

def convert_edgecode(f, avb_edgecode):
    edgecode = f.create.EdgeCode()
    edgecode['Start'].value = avb_edgecode.start_ec
    edgecode['FilmKind'].value = avb_edgecode.film_kind
    edgecode['CodeFormat'].value = avb_edgecode.code_format
    edgecode['Header'].value = avb_edgecode.header
    return edgecode

def sequ_first_item(avb_component):

    if avb_component.class_id != b'SEQU':
        return avb_component

    for item in avb_component.components:
        if item.length > 0:
            return item

    raise Exception()

def convert_title(f, avb_title):
    # avb_dump(avb_title)

    fx_attr = avb_title.attributes.get('AGraphicFXAttr', None)
    if not fx_attr:
        return f.create.Filler()

    pict_data = fx_attr.pict_data
    if not pict_data:
        return f.create.Filler()

    pict_data = bytearray(pict_data)

    op = f.create.OperationGroup('Title_2')
    if len(pict_data) > 0xFFFF:
        stream = op['OpGroupGraphicsParamStream'].open('w')
        stream.write(pict_data)
    else:
        param = f.create.ConstantValue('AvidGraphicFXAttr', bytearray(pict_data))
        op.parameters.append(param)

    param = f.create.ConstantValue('AvidEffectID', bytearray(b'EFF2_BLEND_GRAPHIC\x00'))
    op.parameters.append(param)

    for track in avb_title.tracks:
        comp = convert_component(f, track.component)
        op.segments.append(comp)

    return op


def convert_track_effect(f, avb_effect):
    # print(avb_effect.effect_id)

    if avb_effect.effect_id in (b'EFF2_BLEND_RESIZE', b'EFF2_LUTSFX'):

        # avb_dump(avb_effect)
        track = avb_effect.tracks[0]
        return convert_component(f, sequ_first_item(track.component))

    elif avb_effect.effect_id  == b'EFF2_BLEND_GRAPHIC':
        return convert_title(f, avb_effect)

    # print('------')
    elif avb_effect.effect_id == b'Audio Pan Volume':
        return convert_component(f, sequ_first_item(avb_effect.tracks[0].component))

    elif avb_effect.effect_id == b'EFF2_RGB_COLOR_CORRECTION':

         track = avb_effect.tracks[0]
         return convert_component(f, sequ_first_item(track.component))

    else:
        # avb_dump(avb_effect)
        # print(avb_effect.effect_id)
        track = avb_effect.tracks[0]
        return convert_component(f, sequ_first_item(track.component))

    #
    return aaf_component

def convert_essence_group(f, avb_essence_group):
    # avb_dump(avb_essence_group)
    e = f.create.EssenceGroup()
    for track in avb_essence_group.tracks:
        c = convert_component(f, track.component)
        e['Choices'].append(c)

    e['EssenceGroupType'].value = avb_essence_group.rep_set_type

    return e

interp_kinds = {
2: 'ConstantInterp',
3: 'LinearInterp',
5: 'AvidBezierInterpolator',
6: 'AvidCubicInterpolator',
}

extrap_kinds = {
1: UUID('0e24dd54-66cd-4f1a-b0a0-670ac3a7a0b3'),
}

pp_codes = {
5:  'PP_IN_TANGENT_POS_U',
6:  'PP_IN_TANGENT_VAL_U',
7:  'PP_OUT_TANGENT_POS_U',
8:  'PP_OUT_TANGENT_VAL_U',
9:  'PP_TANGENT_MODE_U',
14: 'PP_BASE_FRAME_U',
}

def convert_parameter(f, name, param):
    try:
        interpdef = interp_kinds[param.control_track.interp_kind]
    except:
        avb_dump(param)
        print(param.control_track.interp_kind)
        raise

    if interpdef in ('ConstantInterp', ):
        assert len(param.control_track.control_points) == 1
        p = param.control_track.control_points[0]
        var = f.create.ConstantValue(name, p.value)
        return var

    var = f.create.VaryingValue(name, interpdef)
    var['VVal_Extrapolation'].value = extrap_kinds[param.control_track.extrap_kind]
    var['VVal_FieldCount'].value = 1

    for p in param.control_track.control_points:
        t = AAFRational(p.offset[0], p.offset[1])
        try:
            point = var.add_keyframe(t, p.value, 'RelativeFixed')
        except:
            print(p.value)
            avb_dump(param)
            raise
        bezier_controls = []
        for pp in p.pp:
            pp_control = f.create.ConstantValue(pp_codes[pp.code], pp.value)
            bezier_controls.append(pp_control)

        point['ControlPointPointProperties'].extend(bezier_controls)

            # print(pp_codes[pp.code], pp_control)
        # print(t, p.value, point)
    return var


def convert_motion_effect(f, avb_effect):
    # avb_dump(avb_effect)

    op_group = f.create.OperationGroup("Motion Control")

    for param in avb_effect.param_list:
        # avb_dump(param)

        var = None
        if param.uuid == UUID("8d56827c-847e-11d5-935a-50f857c10000"):
            var = convert_parameter(f, 'PARAM_SPEED_MAP_U', param)
        elif param.uuid == UUID("8d56827d-847e-11d5-935a-50f857c10000"):
            var = convert_parameter(f, 'PARAM_SPEED_OFFSET_MAP_U', param)
        # elif param.uuid == UUID("8d568283-847e-11d5-935a-50f857c10000"):
        #     var = convert_parameter(f, "PARAM_PULLDOWN_PHASE_U", param)
        # # else:
        #     avb_dump(avb_effect)
        if var:
            op_group.parameters.append(var)

    track = avb_effect.tracks[0]
    ratio = avb_effect.speed_ratio
    param = f.create.ConstantValue("SpeedRatio", AAFRational(ratio[0], ratio[1]))
    op_group.parameters.append(param)

    attr = avb_effect.attributes.get('_MFX_INPUT_FORMAT', None)
    if attr is not None:
        param = f.create.ConstantValue('AvidMotionInputFormat', attr)
        op_group.parameters.append(param)

    attr = avb_effect.attributes.get('_MFX_OUTPUT_FORMAT', None)
    if attr is not None:
        param = f.create.ConstantValue('AvidMotionOutputFormat', attr)
        op_group.parameters.append(param)

    segment = convert_component(f, track.component)
    op_group['InputSegments'].append(segment)

    return op_group

def convert_component(f, avb_component):

    # avb_dump(avb_component)

    if type(avb_component) is avb.components.SourceClip:
        aaf_component = convert_source_clip(f, avb_component)

    elif type(avb_component) is avb.components.Sequence:
        aaf_component = convert_sequence(f, avb_component)

    elif type(avb_component) is avb.components.Filler:
        aaf_component = f.create.Filler()
    elif type(avb_component) is avb.trackgroups.TransitionEffect:
        aaf_component = convert_transistion(f, avb_component)

    elif type(avb_component) is avb.components.Timecode:
        aaf_component = f.create.Timecode()
        aaf_component['Start'].value = avb_component.start
        aaf_component['FPS'].value = avb_component.fps

    elif type(avb_component) is avb.trackgroups.Selector:
        aaf_component = convert_selector(f, avb_component)

    elif isinstance(avb_component, avb.trackgroups.TrackEffect):
        aaf_component = convert_track_effect(f, avb_component)

    elif isinstance(avb_component, avb.trackgroups.CaptureMask):
        aaf_component = convert_capture_mask(f, avb_component)
    elif isinstance(avb_component, avb.components.Edgecode):
        aaf_component = convert_edgecode(f, avb_component)
    elif isinstance(avb_component, avb.trackgroups.MotionEffect):
        aaf_component = convert_motion_effect(f, avb_component)
    elif isinstance(avb_component, avb.trackgroups.EssenceGroup):
        aaf_component = convert_essence_group(f, avb_component)
    else:
        # avb_dump(avb_component)
        # raise Exception(str(segment))
        # print("??", segment)
        aaf_component = f.create.Filler()

    aaf_component.media_kind = avb_component.media_kind
    aaf_component.length =  avb_component.length
    # print(aaf_component)
    return aaf_component

def convert_marker(f, avb_marker):
    # avb_dump(avb_marker)

    attrs = avb_marker.attributes or {}
    marker = f.create.DescriptiveMarker()

    marker['CommentMarkerTime'].value = attrs.get('_ATN_CRM_TIME', None)
    marker['CommentMarkerDate'].value = attrs.get('_ATN_CRM_DATE', None)
    marker['CommentMarkerUser'].value = attrs.get('_ATN_CRM_USER', None)

    marker['Comment'].value = attrs.get('_ATN_CRM_COM', None)

    c = avb_marker.color
    marker['CommentMarkerColor'].value = {'red': c[0], 'green': c[1], 'blue': c[2]}

    for key, value in attrs.items():
        tag = f.create.TaggedValue(key, value)
        marker['CommentMarkerAttributeList'].append(tag)

    database_id = attrs.get('_ATN_CRM_ID', None)
    if database_id:
        tag = f.create.TaggedValue('DatabaseID', database_id)
        marker['UserComments'].append(tag)


    # marker.dump()
    # raise Exception()
    return marker


def get_avb_component_markers(c):
    attributes = c.attributes or {}
    markers = attributes.get('_TMP_CRM',  [])
    if isinstance(c, avb.components.Sequence):
        for item in c.components:
            more_markers = get_avb_component_markers(item)
            markers.extend(more_markers)

    elif isinstance(c, avb.trackgroups.TrackGroup):
        for track in c.tracks:
            if not hasattr(track, 'component'):
                continue

            more_markers = get_avb_component_markers(track.component)
            markers.extend(more_markers)

        # if more_markers:
        #     avb_dump(c)

    return markers

def convert_markers(f, avb_component, described_slots):

    components = []
    if isinstance(avb_component, avb.components.Sequence):
        components = avb_component.components
    else:
        components = [avb_component]

    pos = 0
    marker_list = []
    for item in components:

        if isinstance(item, avb.trackgroups.TransitionEffect):
            pos -= item.length

        markers = get_avb_component_markers(item)

        for marker in markers:
            # avb_dump(marker)
            aaf_marker = convert_marker(f, marker)
            aaf_marker['Position'].value = pos + marker.comp_offset
            aaf_marker['DescribedSlots'].value = described_slots
            # aaf_marker.dump()
            # raise Exception()
            marker_list.append(aaf_marker)
        if not isinstance(item, avb.trackgroups.TransitionEffect):
            pos += item.length

    return marker_list

def convert_slots(aaf_file, comp, aaf_mob):

    marker_slot_id = 1000

    slot_list = set()
    for i, track in enumerate(iter_tracks(comp)):

        media_kind = track.component.media_kind
        if media_kind in ('picture', 'sound','edgecode', 'timecode'):
            slot = aaf_file.create.TimelineMobSlot()

            # raise Exception()
        elif media_kind in ('DescriptiveMetadata', ):
            slot = aaf_file.create.EventMobSlot()
        else:
            raise Exception("Unknown media_kind: %s" % track.component.media_kind)

        # print(track.index, track.component.media_kind)
        # slot_list.add(track.index)
        slot_id = i + 1
        slot.edit_rate = track.component.edit_rate
        slot.slot_id = slot_id
        slot.segment = convert_component(aaf_file, track.component)
        aaf_mob.slots.append(slot)

        markers = convert_markers(aaf_file, track.component, described_slots=[slot.slot_id])
        if markers:
            # print_markers(track, markers)
            event_slot = aaf_file.create.EventMobSlot()
            event_slot.edit_rate = track.component.edit_rate
            event_slot.slot_id = marker_slot_id
            event_slot.segment = aaf_file.create.Sequence()
            event_slot.segment.media_kind = 'DescriptiveMetadata'
            event_slot.segment.components.extend(markers)
            marker_slot_id += 1
            # print(markers)
            # raise Exception()
            aaf_mob.slots.append(event_slot)

def print_markers(track, markers):
    media_kind = track.component.media_kind

    for aaf_marker in markers:

        if media_kind == 'picture':
            track_name = "V%d" % track.index
        elif media_kind == 'sound':
            track_name = 'A%d' % track.index
        else:
            track_name = "%d" % track.index

        marker_color = ""
        for item in aaf_marker['CommentMarkerAttributeList'].value:
            if item['Name'].value == '_ATN_CRM_COLOR':
                marker_color = item['Value'].value or ""
                break

        marker_values  = (aaf_marker['CommentMarkerUser'].value,
                          aaf_marker['Position'].value,
                          track_name, marker_color,
                          aaf_marker['Comment'].value or "")
        marker_string = "\t".join([str(item) for item in (marker_values)])
        print(marker_string)

def convert_composition(f, avb_mob):
    mob_id = MobID(bytes_le=avb_mob.mob_id.bytes_le)
    if mob_id in f.content.mobs:
        return f.content.mobs.get(mob_id)

    if avb_mob.mob_type == 'MasterMob':
        if avb_mob.name:
            pass
            # print(mob_id, avb_mob.name)
        aaf_mob = f.create.MasterMob()
        aaf_mob.mob_id = mob_id
    elif avb_mob.mob_type == 'SourceMob':
        aaf_mob = f.create.SourceMob()
        aaf_mob.descriptor = convert_descriptor(avb_mob.descriptor, f)
        aaf_mob.mob_id = mob_id
    elif avb_mob.mob_type == 'CompositionMob':
        aaf_mob = f.create.CompositionMob()

        # use exsiting mob_id for non toplevel comps
        if avb_mob.usage is not None:
            aaf_mob.mob_id = mob_id
            aaf_mob['AppCode'].value = 1

        if avb_mob.usage_code == 0:
            aaf_mob.usage = "Usage_TopLevel"

    # avb_dump(avb_mob)
    aaf_mob.name = avb_mob.name or ""

    f.content.mobs.append(aaf_mob)
    convert_slots(f, avb_mob, aaf_mob)

    for key, value in avb_mob.attributes.get('_USER', {}).items():
        tag  = f.create.TaggedValue(key, value)
        aaf_mob.comments.append(tag)

    return aaf_mob


def avb2aaf(aaf_file, avb_file):

    for mob in avb_file.content.toplevel():
        print(mob.name)
        convert_composition(aaf_file, mob)
        # break

def avb2aaf_main(path):

    with avb.open(path) as avb_file:
        with aaf2.open(path + ".aaf", 'w') as aaf_file:
            register_definitions(aaf_file)
            avb_file.content.build_mob_dict()
            avb2aaf(aaf_file, avb_file)

    # with aaf2.open(path + ".aaf", 'r') as aaf_file:
    #     aaf_file.content.dump()



if __name__ == "__main__":

    avb2aaf_main(sys.argv[1])
