import json

WIDTHS=dict(game=1,frame_game=1,frame_valid=1,frame_ticks=16,debug=24,micro=16,retired=16,
            reads=16,writes=16,ticks=16,errors=16,oled_frames=8,cycle_ticks=4,phase_trace=2,ram=256)

def parse_record(raw):
    row=json.loads(raw)
    if not isinstance(row,dict) or row.get('type')!='M20_V3_STATE' or row.get('build') not in ('M20V3F01','M20V3F02','M20V3F03','M20V3F04','M20V3F05','M20V3F06','M20V3S01'):
        raise ValueError('not M20 V3 telemetry')
    result=dict(row)
    for key,width in WIDTHS.items():
        value=row.get(key)
        if not isinstance(value,str) or len(value)!=width or any(c not in '0123456789abcdefABCDEF' for c in value):
            raise ValueError('bad hexadecimal field '+key)
        if key!='ram':result[key]=int(value,16)
    if any(result[k]>1 for k in ('game','frame_game','frame_valid')) or result['cycle_ticks']<50:
        raise ValueError('bad game or period')
    if result['frame_ticks']>result['ticks']:raise ValueError('RAM epoch from future')
    debug=result['debug']
    result.update(pc=(debug>>69)&4095,ar=(debug>>61)&255,a=(debug>>57)&15,
                  z=(debug>>56)&1,c=(debug>>55)&1,gpo=(debug>>51)&15,ustate=(debug>>48)&7,
                  rom_word=(debug>>32)&65535,ram_addr=(debug>>24)&255,
                  ram_wdata=(debug>>20)&15,ram_rdata=(debug>>16)&15,
                  ram_ce=(debug>>15)&1,ram_oe=(debug>>14)&1,ram_we=(debug>>13)&1,
                  keys=(debug>>7)&63,master_hold=(debug>>6)&1,slave_open=(debug>>5)&1,
                  active=(debug>>4)&1,reset=(debug>>3)&1,run=(debug>>2)&1,halted=(debug>>1)&1,trapped=debug&1)
    result['ram_cells']=[int(c,16) for c in row['ram'][::-1]]
    result['queued_keys']=(debug>>91)&15
    result['input_overflows']=(debug>>81)&1023
    if result['queued_keys']>8:raise ValueError('invalid input queue depth')
    return result
