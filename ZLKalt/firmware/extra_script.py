import os
Import("env")

# Remove default CRT and libraries
env.Append(LINKFLAGS=["-nostartfiles", "-nostdlib"])

def get_serial_defines():
    defines = []
    
    case_id = os.environ.get("CASE_ID")
    if case_id and len(case_id) == 4:
        defines.append(("CASE_ID_01", f"0x{case_id[0:2]}"))
        defines.append(("CASE_ID_23", f"0x{case_id[2:4]}"))
        
    ZL_NUM = os.environ.get("ZL_NUM")
    if ZL_NUM and len(ZL_NUM) == 9:
        defines.append(("ZL_NUM_0", f"0x0{ZL_NUM[0]}"))
        defines.append(("ZL_NUM_12", f"0x{ZL_NUM[1:3]}"))
        defines.append(("ZL_NUM_34", f"0x{ZL_NUM[3:5]}"))
        defines.append(("ZL_NUM_56", f"0x{ZL_NUM[5:7]}"))
        defines.append(("ZL_NUM_78", f"0x{ZL_NUM[7:9]}"))
        
    date = os.environ.get("DATE")
    if date and len(date) == 4:
        defines.append(("DATE_0", f"0x{date[0:2]}"))
        defines.append(("DATE_1", f"0x{date[2:4]}"))
        
    return defines

env.Append(CPPDEFINES=get_serial_defines())
