# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" Plugin that wraps the freeimage lib. The wrapper for Freeimage is
part of the core of imageio, but it's functionality is exposed via
the plugin system (therefore this plugin is very thin).
"""

from imageio import Format, formats
from imageio import base
from imageio import fi
import ctypes


class FreeimageFormat(Format):
    """ This is the default format used for FreeImage.
    """
    
    def __init__(self, name, description, extensions, fif):
        Format.__init__(self, name, 'FI: '+description, extensions)
        self._fif = fif
    
    @property
    def fif(self):
        return self._fif
    
    def _get_reader_class(self):
        return Reader
    
    def _get_writer_class(self):
        return Writer 
    
    def _can_read(self, request):
        if fi and request.expect in [None, base.EXPECT_IM, base.EXPECT_MIM]:
            if not hasattr(request, '_fif'):
                request._fif = fi.getFIF(request.filename, 'r')
            if request._fif == self.fif:
                return True
                # Note: adding as a potential format and then returning False
                # will give preference to other formats that can read the file.
                #request.add_potential_format(self)
    
    def _can_save(self, request):
        if fi and request.expect in [None, base.EXPECT_IM, base.EXPECT_MIM]:
            if not hasattr(request, '_fif'):
                request._fif = fi.getFIF(request.filename, 'w')
            if request._fif is self.fif:
                return True


# todo: reader and writer use filenames directly if possible, so that
# when only reading meta data, or not all files from a multi-page file,
# the performance is increased.
class Reader(base.Reader):
    
    def _mshape(self):
        return 1
    
    def _get_kwargs(self, flags=0):
        return flags
    
    def _read_data(self, *indices, **kwargs):
        bb = self.request.get_bytes()
        flags = self._get_kwargs(**kwargs)
        
        # todo: Allow special cases with kwrags
#         return fi.read(self.request.filename, flags, bytes=bb,
#                                                     ftype=self.format.fif)
        
        bm = fi.create_bitmap(self.request.filename, self.format.fif, flags)
        bm.load_from_bytes(bb)
        im = bm.read_image_data()
        bm.close()
        return im
    
        
    def _read_info(self, *indices, **kwargs):
        bb = self.request.get_bytes()
        flags = self._get_kwargs(**kwargs)
        
#         return fi.read_metadata(self.request.filename, bytes=bb, 
#                                                     ftype=self.format.fif)
       
        bm = fi.create_bitmap(self.request.filename, self.format.fif, flags)
        bm.load_from_bytes(bb)
        meta = bm.read_meta_data()
        bm.close()
        return meta
    
  
class Writer(base.Writer):
    
    def _get_kwargs(self, flags=0):
        return flags
    
    def _save_data(self, im, *indices, **kwargs):
        flags = self._get_kwargs(**kwargs)
        
#         bb = fi.write(self.request.filename, im, flags, bytes=True,
#                                                     ftype=self.format.fif)
        bm = fi.create_bitmap(self.request.filename, self.format.fif, flags)
        bm.allocate(im)
        bm.write_image_data(im)
        if hasattr(im, 'meta'):
            bm.write_meta_data(im.meta)
        # todo: adding of meta data is task of base Write class, not plugins.
        bb = bm.save_to_bytes()
        bm.close()
        
        self.request.set_bytes(bb)
    
    def _save_info(self, *indices, **kwargs):
        raise NotImplemented()

# todo: implement separate Formats for some FreeImage file formats



def create_freeimage_formats():
    
    # Freeimage available?
    if fi is None:
        return 
    
    # Init
    lib = fi._lib
    
    # Create formats        
    for i in range(lib.FreeImage_GetFIFCount()):
        if lib.FreeImage_IsPluginEnabled(i):                
            # Get info
            name = lib.FreeImage_GetFormatFromFIF(i).decode('ascii')
            des = lib.FreeImage_GetFIFDescription(i).decode('ascii')
            ext = lib.FreeImage_GetFIFExtensionList(i).decode('ascii')
            # Create Format and add (in two ways)
            format = FreeimageFormat(name, des, ext, i)
            formats.add_format(format)

create_freeimage_formats()
