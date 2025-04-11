# This module is used to record the string mapping in the binary.

import csv
from capa.features.address import FileOffsetAddress
import pefile


class StringMap:
    def __init__(self):
        self.map = {}
        
    def add(self, pointer_addr, string_addr, string, vw):
        self.map[pointer_addr] = (string_addr, self.va_to_file_offset(vw, string_addr), string)
        
    def write_to(self, file_path):
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write each key and its tuple values as a row
            for key, (val1, val2, val3) in self.map.items():
                writer.writerow([key, val1, FileOffsetAddress(val2[0] + _text_base[val2[1]]), val3])
                
    def va_to_file_offset(self, vw, va):
        """
        Convert a virtual address (va) to the corresponding file offset using the workspace's memory maps.
        
        :param vw: The Vivisect workspace.
        :param va: The virtual address to convert.
        :return: The corresponding file offset, or None if not found.
        """
        sa, _, sname, _= vw.getSegment(va)
        return va - sa, sname
                

_instance = None
_text_base = None

def get_string_map():
    global _instance
    if _instance is None:
        _instance = StringMap()
    return _instance

def set_text_base(buf):
    global _text_base, _instance
    if _text_base is None:
        _text_base = {}
        pe = pefile.PE(data=buf)
        for section in pe.sections:
            _text_base[section.Name.rstrip(b"\x00").decode('utf-8')] = section.PointerToRawData
