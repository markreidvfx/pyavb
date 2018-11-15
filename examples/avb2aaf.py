import avb
import aaf2
import sys

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
        descriptor["SampleRate"].value = "{}/{}".format(d.sample_rate, 1)
        descriptor["AudioSamplingRate"].value = "{}/{}".format(d.sample_rate, 1)
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
        aaf_mob.mob_id = comp.mob_id

        aaf_file.content.mobs.append(aaf_mob)


def avb2aaf_main(path):

    with avb.open(path) as avb_file:
        with aaf2.open(path + ".aaf", 'w') as aaf_file:
            avb2aaf(avb_file, aaf_file)



if __name__ == "__main__":

    avb2aaf_main(sys.argv[1])
