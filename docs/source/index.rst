.. pyavb documentation master file, created by
   sphinx-quickstart on Thu Apr 11 17:50:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyavb's documentation!
=================================

Overview
--------

pyavb is a python module for reading and writing Avid Bin Files (AVB) files.


Notice
------

This project is in no way affiliated, nor endorsed in any way with Avid, and their name and all product names are registered brand names and trademarks that belong to them.

Installation
------------

You can install pyavb via::

  pip install pyavb

or clone the latest development git master::

  git clone https://github.com/markreidvfx/pyavb
  cd pyavb
  python setup.py install

Quickstart
----------


Reading::

  import avb

  with avb.open("/path/to/file.avb") as f:

    for mob in f.content.mobs:
      print(mob.name)
      for track in mob.track:
          print(track.component)


.. toctree::
   :maxdepth: 4
   :caption: Contents:

   api/avb

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Further Reading
===============

pyavb was initially started using these projects as reference

- `AVBParser <http://www.medien.ifi.lmu.de/team/raphael.wimmer/projects/avb_parser>`_
- `Media Decomposer <https://code.google.com/archive/p/media-decomposer>`_

More datatypes and names have been discovered via this avid console command::

  EnableBinXMLDump true

The xml dumping can be buggy, if it fails you might need to set this to disabled too::

  SwitchBinSaveWorkflow