from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import avb


modules = {}

for name, class_obj in avb.utils.AVBClassName_dict.items():

    mod = class_obj.__module__
    if mod not in modules:
        modules[mod] = []
    modules[mod].append(class_obj)

api_dir = os.path.join(os.path.dirname(__file__), 'api')
if not os.path.exists(api_dir):
    os.makedirs(api_dir)

with open(os.path.join(api_dir, 'avb.rst'), 'w') as root:
    root.write('avb package\n')
    root.write('============\n')
    root.write("\n")
    root.write('Submodules\n')
    root.write('----------\n')
    root.write("\n")
    root.write('.. toctree::\n')
    root.write("\n")

    for mod, classes in sorted(modules.items()):
        root.write('   ' + mod + '\n')
        with open(os.path.join(api_dir, mod + ".rst"), 'w') as f:
            title = mod
            f.write(title +"\n")
            f.write("=" * len(title) + '\n')
            f.write("\n")


            d = {class_obj.__name__:class_obj for class_obj in classes}
            for class_name, class_obj in sorted(d.items()):
                f.write(class_name + '\n')
                f.write('-'* len(class_name) + '\n')

                f.write("\n")
                f.write(".. autoclass:: " + mod +  '.' + class_name + "\n")
                f.write('   :members:\n')
                f.write('   :show-inheritance:\n')
                f.write("\n")

                if not class_obj.propertydefs:
                    continue

                f.write('Properties:\n')
                f.write("\n")

                f.write('==============================   ============\n')
                f.write('name                             type\n')
                f.write('==============================   ============\n')

                for pdef in class_obj.propertydefs:
                    f.write('{0:<32} {1}\n'.format(pdef.name, pdef.type ))

                f.write('==============================   ============\n')
                f.write("\n")
