#!/usr/bin/python

import os

shell_str = """
    #!/bin/bash
    function printcolor(){
        printf "\e[1;33m[debug]\e[0m\e[1;31m$1\n\e[0m"
    }

    function main(){
        start_time=$(date +%s)
        printcolor "*******************"
        cpu_num=$(grep -c processor /proc/cpuinfo)
        cpu_num=$[cpu_num*2]
        cpu_num=8
        sleep 3
        end_time=$(date +%s)
        time_elapse=$((end_time-start_time))
        printcolor $time_elapse
        printcolor "*******************"

    }
    main $*
    """

result = os.system("bash -c '%s'" % shell_str)
if result != 0:
    print "Error"
