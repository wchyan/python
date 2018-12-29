#!/usr/bin/python
###############################################################################
###
### (c) 2012 by Ollopa / www.isysop.com
###
### Python script to pack and unpack U-Boot uImage files
###
###

import os  
from os.path import join, getsize, exists
import hashlib
from struct import *
from optparse import OptionParser

# From mkbootimg source code in Android sources.
# system/core/mkbootimg/mkbootimg.c
# system/core/mkbooting/bootimg.h

# #define BOOT_MAGIC "ANDROID!"
# #define BOOT_MAGIC_SIZE 8
# #define BOOT_NAME_SIZE 16
# #define BOOT_ARGS_SIZE 512
# #define BOOT_EXTRA_ARGS_SIZE 1024

# struct boot_img_hdr
# {
#     unsigned char magic[BOOT_MAGIC_SIZE];
#     unsigned kernel_size;  /* size in bytes */
#     unsigned kernel_addr;  /* physical load addr */
#     unsigned ramdisk_size; /* size in bytes */
#     unsigned ramdisk_addr; /* physical load addr */
#     unsigned second_size;  /* size in bytes */
#     unsigned second_addr;  /* physical load addr */
#     unsigned tags_addr;    /* physical addr for kernel tags */
#     unsigned page_size;    /* flash page size we assume */
#     unsigned unused[2];    /* future expansion: should be 0 */
#     unsigned char name[BOOT_NAME_SIZE]; /* asciiz product name */
#     unsigned char cmdline[BOOT_ARGS_SIZE];
#     unsigned id[8]; /* timestamp / checksum / sha1 / etc */
#     unsigned char extra_cmdline[BOOT_EXTRA_ARGS_SIZE];
# };

HEADER_FORMAT = '8B10I16s512s32B1024s' ### (Little-endian, 12 ULONGS, 16, 512, 32-byte string)

def write_padding(fd, pagesize, itemsize):
    pagemask = pagesize - 1
    if(itemsize & pagemask) == 0:
        return
    count = pagesize - (itemsize & pagemask)
    for i in range(0, count):
        fd.write(b'0')

def imageCreate(options):
    ifh = open(options.output, 'w+b')
    kernel_size = 0
    ramdisk_size = 0
    second_size = 0

    if exists(options.kernel):
        kernel_size =  getsize(options.kernel)
    else:
        print("%s is not exist" % options.kernel)
        return
    if exists(options.ramdisk):
        ramdisk_size =  getsize(options.ramdisk)
    else:
        print("%s is not exist" % options.kernel)
        return

    if exists(options.secondimg):
        second_size =  getsize(options.secondimg)

    kernel_data = ''
    ramdisk_data = ''
    second_data = ''

    sha1 = hashlib.sha1();
    with open(options.kernel, 'r') as data:
        kernel_data = data.read()
        sha1.update(kernel_data)
        sha1.update(bytearray(unpack('>4B', pack('I', kernel_size))))
    with open(options.ramdisk, 'r') as data:
        ramdisk_data = data.read()
        sha1.update(ramdisk_data)
        sha1.update(bytearray(unpack('>4B', pack('I', ramdisk_size))))
    if exists(options.secondimg):
        with open(options.secondimg, 'r') as data:
            second_data = data.read()
    sha1.update(second_data)
    sha1.update(bytearray(unpack('>4B', pack('I', second_size))))
    id = sha1.hexdigest()
    id_num = []
    for i in range(0, 40, 2):
        id_num.append(int(id[i: i + 2], 16))
    kernel_base = options.base + options.kernel_offset
    ramdisk_base = options.base + options.ramdisk_offset
    second_base = options.base + options.second_offset
    tags_base = options.base + options.tags_offset
    cmdline = options.cmdline
    extra_cmdline = '\0' * 1024
    if len(options.cmdline) > 512:
        cmdline = options.cmdline[0:512]
        extra_cmdline = options.cmdline[512:]

    header = pack(HEADER_FORMAT,
            0x41, 0x4e, 0x44, 0x52,
            0x4f, 0x49, 0x44, 0x21, #magic 'ANDROID!'
            kernel_size, kernel_base,
            ramdisk_size, ramdisk_base,
            second_size, second_base,
            tags_base,
            options.pagesize,
            0, 0, #unused
            options.board,
            cmdline,
            id_num[0], id_num[1], id_num[2], id_num[3],
            id_num[4], id_num[5], id_num[6], id_num[7],
            id_num[8], id_num[9], id_num[10], id_num[11],
            id_num[12], id_num[13], id_num[14], id_num[15],
            id_num[16], id_num[17], id_num[18], id_num[19],
            0, 0, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0,
            extra_cmdline)
    ifh.write(header)
    write_padding(ifh, options.pagesize, len(header))
    ifh.write(kernel_data)
    write_padding(ifh, options.pagesize, kernel_size)
    ifh.write(ramdisk_data)
    write_padding(ifh, options.pagesize, ramdisk_size)
    ifh.write(second_data)
    write_padding(ifh, options.pagesize, second_size)
    ifh.close()

def usage():
    print("usage: mkbootimg\n" \
    "       --kernel <filename>\n" \
    "       --ramdisk <filename>\n" \
    "       [ --second <2ndbootloader-filename> ]\n" \
    "       [ --cmdline <kernel-commandline> ]\n" \
    "       [ --board <boardname> ]\n" \
    "       [ --base <address> ]\n" \
    "       [ --pagesize <pagesize> ]\n" \
    "       -o|--output <filename>\n")

def main():
    parser = OptionParser() #usage())
    parser.add_option("--kernel", dest = "kernel", help = "set kernel image")
    parser.add_option("--ramdisk", dest = "ramdisk", help = "set ramdisk image")
    parser.add_option("--second", dest = "secondimg", default = '', help = "set second image")
    parser.add_option("--cmdline", dest = "cmdline", default = '', help = "set cmd line")
    parser.add_option("--base", dest = "base", default = 0x10000000, help = "set base address")
    parser.add_option("--kernel_offset", dest = "kernel_offset", default = 0x00008000, help = "set kernel offset")
    parser.add_option("--ramdisk_offset", dest = "ramdisk_offset", default = 0x01000000, help = "set ramdisk offset")
    parser.add_option("--second_offset", dest = "second_offset", default = 0x00F00000, help = "set second image offset")
    parser.add_option("--tags_offset", dest = "tags_offset", default = 0x00000100, help = "set tags offset")
    parser.add_option("--board", dest = "board", default = '', help = "set board name")
    parser.add_option("--pagesize", dest = "pagesize", default = 2048, help = "set page size")
    parser.add_option("-o", "--output", dest = "output", help = "set output file name")

    (options, args) = parser.parse_args()

    if (options.kernel == None or options.ramdisk == None or options.output == None):
       usage()
       return
    if ((options.pagesize != 2048) and (options.pagesize != 4096)
            and (options.pagesize != 8192) and (pagesize != 16384)):
        print("page size should be 2048|4096|8192|16384")
        return

    imageCreate(options)

    return

if __name__ == "__main__":
   main()
