from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import avb
import sys

if bytes is not str:
    unicode = str

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
                # print(space, item)
                pass
                avb_dump(item, space + " ")
        else:
            if value is not None:
                print("%s%s:" % (space, key), pretty_value(value))

def frames_to_timecode(frames, fps=24):
    s, f = divmod(frames, fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return '{1:02d}:{2:02d}:{3:02d}:{4:02d}'.format(d, h,m,s,f)

def print_marker(pos, marker, track):
    if track.component.media_kind == 'picture':
        track_name= "V%d" % track.index
    elif track.component.media_kind == 'sound':
        track_name= "A%d" % track.index
    else:
        track_name= "%d" % track.index

    user =  marker.attributes.get("_ATN_CRM_USER", '')
    color = marker.attributes.get("_ATN_CRM_COLOR", '')
    comment = marker.attributes.get("_ATN_CRM_COM", '')

    line = '  {:<25} {} {:<5} {:<10} {}'
    print(line.format(user, frames_to_timecode(pos), track_name, color.lower(), comment))

def get_component_markers(c):
    if 'attributes' not in c.property_data:
        return []

    attributes = c.attributes or {}
    markers = attributes.get('_TMP_CRM',  [])
    if isinstance(c, avb.components.Sequence):
        for item in c.components:
            more_markers = get_component_markers(item)
            markers.extend(more_markers)

    elif isinstance(c, avb.trackgroups.TrackGroup):
        for track in c.tracks:
            if 'component' not in track.property_data:
                continue

            more_markers = get_component_markers(track.component)
            markers.extend(more_markers)

    return markers

def find_track_markers(track, start=0):
    components = []
    if isinstance(track.component, avb.components.Sequence):
        components = track.component.components
    else:
        components = [track.component]

    pos = start
    marker_list = []
    for item in components:

        if isinstance(item, avb.trackgroups.TransitionEffect):
            pos -= item.length

        markers = get_component_markers(item)

        for marker in markers:
            print_marker(pos + marker.comp_offset, marker, track)
            marker_list.append([  pos + marker.comp_offset, marker ])
        if not isinstance(item, avb.trackgroups.TransitionEffect):
            pos += item.length

    return marker_list

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


def dump_markers(mob):
    timcodes = {}
    for i, track in enumerate(iter_tracks(mob)):
        if track.media_kind == 'timecode':
            if not isinstance(track.component, avb.components.Timecode):
                # avb_dump(track)
                continue

            fps = track.component.fps
            start = track.component.start
            timcodes[fps] = start
            # avb_dump(track)
            # print(fps, start, frames_to_timecode(start, fps))

    for i, track in enumerate(iter_tracks(mob)):
        edit_rate = track.component.edit_rate
        tc_rate = int(edit_rate + 0.5)
        start = timcodes.get(tc_rate, 0)
        markers = find_track_markers(track, start)

def main(path):
    with avb.open(path) as f:
        for mob in f.content.toplevel():
            print(mob.name)
            dump_markers(mob)
            # break

if __name__ == "__main__":

    main(sys.argv[1])
