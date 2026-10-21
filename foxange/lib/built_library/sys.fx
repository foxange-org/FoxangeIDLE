@import onec
# sys pkg
def set_int_max_digits(int size)->None:
    run_to_python(f"
    import sys
    sys.set_int_max_str_digits({size})
    ")
def system(str command):
    return run_to_python(f"
    import os
    os.system({command})
    ")
