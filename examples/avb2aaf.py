from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import avb
import aaf2
import sys

def register_definitions(f):
    op_def = f.create.OperationDef('89d9b67e-5584-302d-9abd-8bd330c46841', 'VideoDissolve_2', '')
    f.dictionary.register_def(op_def)

    op_def.media_kind = 'picture'
    op_def['IsTimeWarp'].value = False
    op_def['Bypass'].value = 1
    op_def['NumberInputs'].value = 2
    op_def['OperationCategory'].value = 'OperationCategory_Effect'

    param_byteorder = f.create.ParameterDef("c0038672-a8cf-11d3-a05b-006094eb75cb", "AvidParameterByteOrder", "", 'AvidBagOfBits')
    f.dictionary.register_def(param_byteorder)

    param_effect_id = f.create.ParameterDef("93994bd6-a81d-11d3-a05b-006094eb75cb", "AvidEffectID", "", 'aafUInt16')
    f.dictionary.register_def(param_effect_id)

    op_def.parameters.extend([param_byteorder, param_effect_id])

    # note not part of VideoDissolve_2 op_def but still used...
    opacity_param = f.create.ParameterDef('8d56813d-847e-11d5-935a-50f857c10000', 'AFX_FG_KEY_OPACITY_U', '', 'Rational')
    f.dictionary.register_def(opacity_param)

    linear = f.create.InterpolationDef('5b6c85a4-0ede-11d3-80a9-006008143e6f', 'LinearInterp', '')
    f.dictionary.register_def(linear)

    op_def = f.create.OperationDef('0c3bea41-fc05-11d2-8a29-0050040ef7d2', 'Audio Dissolve', '')
    f.dictionary.register_def(op_def)

    op_def.media_kind = 'sound'
    op_def['IsTimeWarp'].value = False
    op_def['Bypass'].value = 1
    op_def['NumberInputs'].value = 2
    op_def['OperationCategory'].value = 'OperationCategory_Effect'
    op_def.parameters.extend([param_byteorder, param_effect_id])

def nice_edit_rate(rate):
    if rate == 24:
        return "24/1"
    elif rate ==  23.976:
        return "24000/1001"
    elif rate == 30:
        return "30/1"

    return "%d/%d" % (int(rate * 1000), 1000)

def convert_descriptor(d, aaf_file):
    descriptor = None
    if type(d) is avb.essence.MediaDescriptor:
        descriptor = aaf_file.create.ImportDescriptor()
        return descriptor

    elif type(d) is avb.essence.TapeDescriptor:
        descriptor = aaf_file.create.TapeDescriptor()
        return descriptor

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

        elif type(d) is avb.essence.RGBADescriptor:
            descriptor = aaf_file.create.RGBADescriptor()
            descriptor['PixelLayout'].value = d.pixel_layout
        else:
            raise ValueError("unhandled digtial image descriptor")

        descriptor['StoredHeight'].value = d.stored_height
        descriptor['StoredWidth'].value = d.stored_width
        descriptor['ImageAspectRatio'].value = "{}/{}".format(*d.aspect_ratio)
        descriptor['FrameLayout'].value = d.frame_layout
        descriptor['VideoLineMap'].value = d.line_map
        descriptor['SampleRate'].value = 0

    else:
        raise ValueError("unhandle descriptor")


    descriptor["Length"].value = d.length

    return descriptor

def check_source_clip(clip):
    if clip.mob_id.int:
        mob = clip.root.content.mob_dict[clip.mob_id]
        source_track = None
        for track in mob.tracks:
            if track.index == clip.track_id:
                source_track = track
                break
        assert source_track
    else:
        assert clip.track_id == 0


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

def convert_component(f, avb_component):

    # print(avb_component)
    #
    if type(avb_component) is avb.components.SourceClip:
        aaf_component = f.create.SourceClip()
    #     check_source_clip(segment)
        aaf_component['SourceID'].value = avb_component.mob_id
        aaf_component['StartTime'].value = avb_component.start_time
        aaf_component['SourceMobSlotID'].value = avb_component.track_id

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

    else:
        # raise Exception(str(segment))
        # print("??", segment)
        aaf_component = f.create.Filler()

    aaf_component.media_kind = avb_component.media_kind
    aaf_component.length =  avb_component.length

    return aaf_component

def convert_slots(aaf_file, comp, aaf_mob):

    slot_id = 1
    for track in comp.tracks:
        if not track.component.media_kind in ('picture', 'sound'):
            continue

        # if

        # print(track, track.component)
        # print(track.segment.media_kind)

        slot = aaf_file.create.TimelineMobSlot()
        slot.edit_rate = track.component.edit_rate
        slot.segment = convert_component(aaf_file, track.component)
        slot.slot_id = track.index

        aaf_mob.slots.append(slot)
        slot_id += 1

def convert_composition(mob, aaf_file):
    if mob.mob_type == 'MasterMob':
        aaf_mob = aaf_file.create.MasterMob()
    elif mob.mob_type == 'SourceMob':
        aaf_mob = aaf_file.create.SourceMob()
        aaf_mob.descriptor = convert_descriptor(mob.descriptor, aaf_file)
    elif mob.mob_type == 'CompositionMob':
        aaf_mob = aaf_file.create.CompositionMob()


    aaf_mob.name = mob.name or ""
    # aaf_mob.mob_id = mob.mob_id
    aaf_file.content.mobs.append(aaf_mob)
    convert_slots(aaf_file, mob, aaf_mob)
    print(aaf_mob)


def avb2aaf(avb_file, aaf_file):

    for mob in avb_file.content.toplevel():
        convert_composition(mob, aaf_file)

def avb2aaf_main(path):

    with avb.open(path) as avb_file:
        with aaf2.open(path + ".aaf", 'w') as aaf_file:
            register_definitions(aaf_file)
            avb_file.content.build_mob_dict()
            avb2aaf(avb_file, aaf_file)

            aaf_file.content.dump()



if __name__ == "__main__":

    avb2aaf_main(sys.argv[1])
