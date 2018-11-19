from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import avb
import aaf2
import sys


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


def convert_component(aaf_file, segment):

    if type(segment) is avb.components.SourceClip:
        component = aaf_file.create.SourceClip()
        check_source_clip(segment)
        component['SourceID'].value = segment.mob_id
        component['StartTime'].value = segment.start_time
        component['SourceMobSlotID'].value = segment.track_id

    elif type(segment) is avb.components.Sequence:
        seq = aaf_file.create.Sequence()
        for item in segment.components():
            seq.components.append(convert_component(aaf_file, item))

        component = seq

    elif type(segment) is avb.components.Filler:
        component = aaf_file.create.Filler()

    elif type(segment) is avb.components.Timecode:
        component = aaf_file.create.Timecode()
        component['Start'].value = segment.start
        component['FPS'].value = segment.fps

    elif type(segment) is avb.components.Selector:
        component = aaf_file.create.Selector()
        selected = segment.selected
        selected_clip = None
        for i, item in enumerate(segment.components()):
            clip =  convert_component(aaf_file, item)
            if i == selected:
                selected_clip =clip
            else:
                component['Alternates'].append(clip)
        assert selected_clip
        component['Selected'].value = selected_clip

    else:
        # raise Exception(str(segment))
        # print("??", segment)
        component = aaf_file.create.Filler()

    component.media_kind = segment.media_kind
    component.length =  segment.length

    return component

def convert_slots(aaf_file, comp, mob):

    slot_id = 1
    for track in comp.tracks:
        print(" ",track.segment)
        # if not track.segment.media_kind in ('picture', 'sound'):
        #     continue
        # print(track.segment.media_kind)

        slot = aaf_file.create.TimelineMobSlot()
        slot.edit_rate = nice_edit_rate(track.segment.edit_rate)

        slot_id = track.index
        slot.slot_id = slot_id
        mob.slots.append(slot)

        slot.segment = convert_component(aaf_file, track.segment)
        slot_id += 1

def avb2aaf(avb_file, aaf_file):

    for comp in avb_file.content.components:
        if comp.mob_type == 'MasterMob':
            aaf_mob = aaf_file.create.MasterMob()
        elif comp.mob_type == 'SourceMob':
            aaf_mob = aaf_file.create.SourceMob()
            aaf_mob.descriptor = convert_descriptor(comp.descriptor.value, aaf_file)

        elif comp.mob_type == 'CompositionMob':
            aaf_mob = aaf_file.create.CompositionMob()

        aaf_mob.name = comp.name
        # if not aaf_mob.name:
        #     print(comp.mob_id)
            # raise Exception()

        aaf_mob.mob_id = comp.mob_id

        # attr_dict = comp.attribute_ref.value or {}
        # print(attr_dict)
        # user_attr_ref = attr_dict.get("_USER", None)
        # if user_attr_ref:
        #     print("  ", user_attr_ref.value)

        # aaf_mob.usage = comp.usage_code

        aaf_file.content.mobs.append(aaf_mob)
        print(aaf_mob)
        convert_slots(aaf_file, comp, aaf_mob)
        # aaf_file.save()

def avb2aaf_main(path):

    with avb.open(path) as avb_file:
        with aaf2.open(path + ".aaf", 'w') as aaf_file:

            avb_file.content.build_mob_dict()
            avb2aaf(avb_file, aaf_file)

            # aaf_file.content.dump()



if __name__ == "__main__":

    avb2aaf_main(sys.argv[1])
