.. pyavb documentation master file, created by
   sphinx-quickstart on Thu Apr 11 17:50:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyavb's documentation!
=================================

Overview
--------

pyavb is a python module for the reading and writing Avid Bin Files (AVB) files.

Installation
------------

clone the latest development git master::

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
