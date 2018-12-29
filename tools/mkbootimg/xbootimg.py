#!/usr/bin/env python
"""Splits an Android boot.img into its various parts.

   You can put it back together using `cat`.
"""
from __future__ import division, print_function

import sys

from construct import Array, Bytes, ULInt32, Struct
import yaml

_BOOTIMGHDR = Struct("boot_img_hdr",
                      Bytes("magic", 8),
                      ULInt32("kernel_size"),
                      ULInt32("kernel_addr"),
                      ULInt32("ramdisk_size"),
                      ULInt32("ramdisk_addr"),
                      ULInt32("second_size"),
                      ULInt32("second_addr"),
                      ULInt32("tags_addr"),
                      ULInt32("page_size"),
                      Array(2, ULInt32("unused")),
                      Bytes("name", 16),
                      Bytes("cmdline", 512),
                      Array(8, ULInt32("id")),
                      Bytes("extra_cmdline", 1024))

_HEADERLEN = _BOOTIMGHDR.sizeof()

_OUT = "{filename}_{start:08x}-{end:08x}.{name}"


def header_to_yaml(filename):
    with open(filename, 'rb') as f:
        s = f.read(_HEADERLEN)
    h = _BOOTIMGHDR.parse(s)
    fields = 'name,kernel_size,kernel_addr,ramdisk_size,ramdisk_addr,second_size,second_addr,tags_addr,cmdline,id,extra_cmdline'
    for k in fields.split(','):
        print('%s -> %s' % (k, h[k]))
    with open(filename + '.header.yaml', 'wb') as f:
        f.write(yaml.dump(dict([(k, h[k]) for k in fields.split(',')]), default_flow_style=False))


def extract_bootimg(filename):
    """Extract an Android boot image."""
    s = open(filename, 'rb').read()
    h = (_BOOTIMGHDR.parse(s))

    page_size = h.page_size

    print("pagesize %d" % page_size)
    n = (h.kernel_size + page_size - 1) // page_size
    m = (h.ramdisk_size + page_size - 1) // page_size
    o = (h.second_size + page_size - 1) // page_size
    pages = 1 + n + m + o

    PARTS = [('header',  (0, _HEADERLEN)),
             ('kernel',  (1, h.kernel_size)),
             ('ramdisk', (1 + n, h.ramdisk_size)),
             ('second',  (1 + n + m, h.second_size))]

    # Write the header, kernel, ramdisk, and second stages,
    # as well as the material between them.
    end = 0
    for name, (page, size) in PARTS:
        start = page * page_size
        if start > end:
            outname = _OUT.format(start=end, end=start, filename=filename, name='pad')
            with open(outname, 'wb') as f:
                f.write(s[end:start])
        end = start + size
        outname = _OUT.format(start=start, end=end, filename=filename, name=name)
        with open(outname, 'wb') as f:
            f.write(s[start:end])
    # Write the part after the second stage.
    if end < len(s):
        outname = _OUT.format(start=end, end=len(s), filename=filename, name='fin')
        with open(outname, 'wb') as f:
            f.write(s[end:])

if __name__ == '__main__':
    extract_bootimg(sys.argv[1])
    header_to_yaml(sys.argv[1])
