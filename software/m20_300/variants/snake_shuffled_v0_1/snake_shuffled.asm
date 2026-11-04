; M20-300 16-bit ISA: all game decisions execute these machine instructions.
; No B/T/LR, no hardware calls, no host-side game operations.
.equ HEAD_LO, 0x00
.equ HEAD_HI, 0x01
.equ TAIL_LO, 0x02
.equ TAIL_HI, 0x03
.equ LEN_LO, 0x04
.equ LEN_HI, 0x05
.equ DIR, 0x06
.equ FOOD_X, 0x07
.equ FOOD_Y, 0x08
.equ SCORE_LO, 0x09
.equ SCORE_HI, 0x0A
.equ STATUS, 0x0B
.equ KEYS0, 0x0C
.equ KEYS1, 0x0D
.equ EVENT, 0x0E
.equ PROBES_LO, 0x0F
.equ PROBES_HI, 0x10
.equ NEXT_X, 0x11
.equ NEXT_Y, 0x12
.equ OLD_TAIL_X, 0x13
.equ OLD_TAIL_Y, 0x14
.equ GROW, 0x15
.equ TEMP, 0x16
.equ ADDR_LO, 0x17
.equ ADDR_HI, 0x18
.equ BIT_LO, 0x19
.equ BIT_HI, 0x1A
.equ MASK, 0x1B
.equ OCCUPIED, 0x1C
.equ LOOK_X, 0x1D
.equ LOOK_Y, 0x1E
.equ INDEX_LO, 0x1F
.equ INDEX_HI, 0x20
.equ TEMP2, 0x21
.equ FOOD_SEQ_LO, 0x22
.equ FOOD_SEQ_HI, 0x23
.equ RETURN_ID, 0xF0

boot:
    ; Clear all 256 nibble cells using CPU writes, including body/bitmap/scratch.
    ARL 0
    ARH 0
boot_clear:
    LDI 0
    ST [AR]
    INCAR
    MOVA ARL
    ANDI 15
    JZ boot_check_high
    JMP boot_clear
boot_check_high:
    MOVA ARH
    ANDI 15
    JZ boot_init
    JMP boot_clear
boot_init:
    LDI 2
    ST HEAD_LO
    ST 0x40
    LDI 3
    ST LEN_LO
    ST FOOD_Y
    ST 0x41
    ST 0x42
    ST 0x43
    ST 0x45
    LDI 4
    ST 0x44
    LDI 10
    ST FOOD_X
    ; Cells (2,3),(3,3) -> CC bits 2 and 3; cell (4,3) -> CD bit 0.
    LDI 12
    ST 0xCC
    LDI 1
    ST 0xCD
    LDI 4
    ST EVENT
    JMP tick_done

tick:
    IN0
    ST KEYS0
    IN1
    ST KEYS1
    ANDI 2
    JZ tick_no_restart
    JMP boot
tick_no_restart:
    LDI 0
    ST EVENT
    ST PROBES_LO
    ST PROBES_HI
    LD STATUS
    JZ tick_running
    JMP tick_done

tick_running:
    ; Priority: up, down, left, right. First pressed key is considered;
    ; if it reverses the current direction it is rejected without fallback.
    LD KEYS0
    ANDI 1
    JZ key_down
    LD DIR
    SUBI 1
    JZ direction_done
    LDI 3
    ST DIR
    JMP direction_done
key_down:
    LD KEYS0
    ANDI 2
    JZ key_left
    LD DIR
    SUBI 3
    JZ direction_done
    LDI 1
    ST DIR
    JMP direction_done
key_left:
    LD KEYS0
    ANDI 4
    JZ key_right
    LD DIR
    JZ direction_done
    LDI 2
    ST DIR
    JMP direction_done
key_right:
    LD KEYS0
    ANDI 8
    JZ direction_done
    LD DIR
    SUBI 2
    JZ direction_done
    LDI 0
    ST DIR

direction_done:
    ; Read the current head via dynamically generated 0x40 + 2*head_idx.
    LD HEAD_LO
    ST INDEX_LO
    LD HEAD_HI
    ST INDEX_HI
    LD INDEX_LO
    SHL
    ST ADDR_LO
    LD INDEX_HI
    ADC INDEX_HI
    ADDI 4
    ST ADDR_HI
    LD ADDR_LO
    MOVARL A
    LD ADDR_HI
    MOVARH A
    LD [AR]
    ST NEXT_X
    INCAR
    LD [AR]
    ST NEXT_Y

    ; Read the old tail; it is a special legal collision only when not growing.
    LD TAIL_LO
    ST INDEX_LO
    LD TAIL_HI
    ST INDEX_HI
    LD INDEX_LO
    SHL
    ST ADDR_LO
    LD INDEX_HI
    ADC INDEX_HI
    ADDI 4
    ST ADDR_HI
    LD ADDR_LO
    MOVARL A
    LD ADDR_HI
    MOVARH A
    LD [AR]
    ST OLD_TAIL_X
    INCAR
    LD [AR]
    ST OLD_TAIL_Y

    LD DIR
    JZ move_right
    SUBI 1
    JZ move_down
    SUBI 1
    JZ move_left
    JMP move_up
move_right:
    LD NEXT_X
    SUBI 15
    JZ die
    LD NEXT_X
    ADDI 1
    ST NEXT_X
    JMP moved
move_down:
    LD NEXT_Y
    SUBI 7
    JZ die
    LD NEXT_Y
    ADDI 1
    ST NEXT_Y
    JMP moved
move_left:
    LD NEXT_X
    JZ die
    SUBI 1
    ST NEXT_X
    JMP moved
move_up:
    LD NEXT_Y
    JZ die
    SUBI 1
    ST NEXT_Y

moved:
    LDI 0
    ST GROW
    LD NEXT_X
    CMP FOOD_X
    JZ compare_food_y
    JMP find_collision
compare_food_y:
    LD NEXT_Y
    CMP FOOD_Y
    JZ mark_grow
    JMP find_collision
mark_grow:
    LDI 1
    ST GROW
find_collision:
    LD NEXT_X
    ST LOOK_X
    LD NEXT_Y
    ST LOOK_Y
    LDI 1
    ST RETURN_ID
    JMP occupancy_lookup
after_collision_lookup:
    LD OCCUPIED
    JZ collision_ok
    LD GROW
    JZ compare_old_tail
    JMP die
compare_old_tail:
    LD NEXT_X
    CMP OLD_TAIL_X
    JZ compare_old_tail_y
    JMP die
compare_old_tail_y:
    LD NEXT_Y
    CMP OLD_TAIL_Y
    JZ collision_ok
    JMP die

collision_ok:
    LD GROW
    JZ remove_tail
    ; Protect against overwriting an already full 64-slot ring.
    LD LEN_HI
    SUBI 4
    JZ win
    JMP append_head
remove_tail:
    LD OLD_TAIL_X
    ST LOOK_X
    LD OLD_TAIL_Y
    ST LOOK_Y
    LDI 2
    ST RETURN_ID
    JMP occupancy_lookup
after_tail_lookup:
    ; AR still addresses the bitmap nibble returned by the shared routine.
    LD MASK
    NOT
    ST TEMP2
    LD [AR]
    AND TEMP2
    ST [AR]
    LD TAIL_LO
    ADDI 1
    ST TAIL_LO
    LD TAIL_HI
    ADCI 0
    ANDI 3
    ST TAIL_HI

append_head:
    LD HEAD_LO
    ADDI 1
    ST HEAD_LO
    LD HEAD_HI
    ADCI 0
    ANDI 3
    ST HEAD_HI
    LD HEAD_LO
    ST INDEX_LO
    LD HEAD_HI
    ST INDEX_HI
    LD INDEX_LO
    SHL
    ST ADDR_LO
    LD INDEX_HI
    ADC INDEX_HI
    ADDI 4
    ST ADDR_HI
    LD ADDR_LO
    MOVARL A
    LD ADDR_HI
    MOVARH A
    LD NEXT_X
    ST [AR]
    INCAR
    LD NEXT_Y
    ST [AR]
    LD NEXT_X
    ST LOOK_X
    LD NEXT_Y
    ST LOOK_Y
    LDI 3
    ST RETURN_ID
    JMP occupancy_lookup
after_head_lookup:
    LD [AR]
    OR MASK
    ST [AR]
    LD GROW
    JZ tick_done
    LD LEN_LO
    ADDI 1
    ST LEN_LO
    LD LEN_HI
    ADCI 0
    ST LEN_HI
    LD SCORE_LO
    ADDI 1
    ST SCORE_LO
    LD SCORE_HI
    ADCI 0
    ST SCORE_HI
    LD LEN_HI
    SUBI 4
    JZ win
    LDI 1
    ST EVENT
    ; Variant: cyclic fixed 128-position permutation, interpreted by CPU only.
food_next_candidate:
    LD FOOD_SEQ_LO
    ADDI 1
    ST FOOD_SEQ_LO
    LD FOOD_SEQ_HI
    ADCI 0
    ANDI 7
    ST FOOD_SEQ_HI
    JMP food_table_dispatch
food_table_return:
    LD PROBES_LO
    ADDI 1
    ST PROBES_LO
    LD PROBES_HI
    ADCI 0
    ST PROBES_HI
    LDI 4
    ST RETURN_ID
    JMP occupancy_lookup
after_food_lookup:
    LD OCCUPIED
    JZ food_found
    LD PROBES_HI
    SUBI 4
    JZ food_check_limit
    JMP food_next_candidate
food_check_limit:
    LD PROBES_LO
    SUBI 1
    JZ bitmap_fault
    JMP food_next_candidate
food_found:
    LD LOOK_X
    ST FOOD_X
    LD LOOK_Y
    ST FOOD_Y
    JMP tick_done

die:
    LDI 1
    ST STATUS
    LDI 2
    ST EVENT
    JMP tick_done
win:
    LDI 2
    ST STATUS
    LDI 3
    ST EVENT
    JMP tick_done
bitmap_fault:
    ; A legal <=64-cell snake cannot fill all 65 tested positions.
    LDI 3
    ST STATUS
    LDI 5
    ST EVENT
    JMP tick_done

tick_done:
    NOP
    JMP tick

; Shared software subroutine: input LOOK_X/LOOK_Y, output MASK/OCCUPIED,
; BIT_LO/BIT_HI and AR. Uses return_id in ordinary RAM, no hardware LR.
occupancy_lookup:
    ; bitmap byte/nibble address = C0 + 4*y + floor(x/4).
    LD LOOK_Y
    SHL
    SHL
    ST BIT_LO
    LDI 0
    ADCI 0
    ADDI 12
    ST BIT_HI
    LD LOOK_X
    SHR
    SHR
    ADD BIT_LO
    ST BIT_LO
    LD LOOK_X
    ANDI 3
    JZ mask_1
    SUBI 1
    JZ mask_2
    SUBI 1
    JZ mask_4
    LDI 8
    JMP mask_ready
mask_1:
    LDI 1
    JMP mask_ready
mask_2:
    LDI 2
    JMP mask_ready
mask_4:
    LDI 4
mask_ready:
    ST MASK
    LD BIT_LO
    MOVARL A
    LD BIT_HI
    MOVARH A
    LD [AR]
    AND MASK
    JZ occupancy_zero
    LDI 1
    ST OCCUPIED
    JMP software_return
occupancy_zero:
    LDI 0
    ST OCCUPIED
software_return:
    LD RETURN_ID
    SUBI 1
    JZ after_collision_lookup
    SUBI 1
    JZ after_tail_lookup
    SUBI 1
    JZ after_head_lookup
    SUBI 1
    JZ after_food_lookup
    ; Invalid return id is an explicit diagnostic termination.
    HALT

; Code table: ISA has no data load from ROM. Branches select constants.
food_table_dispatch:
    LD FOOD_SEQ_HI
    SUBI 0
    JZ food_table_hi_0
    SUBI 1
    JZ food_table_hi_1
    SUBI 1
    JZ food_table_hi_2
    SUBI 1
    JZ food_table_hi_3
    SUBI 1
    JZ food_table_hi_4
    SUBI 1
    JZ food_table_hi_5
    SUBI 1
    JZ food_table_hi_6
    SUBI 1
    JZ food_table_hi_7
    JMP bitmap_fault
food_table_hi_0:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_0
    SUBI 1
    JZ food_entry_1
    SUBI 1
    JZ food_entry_2
    SUBI 1
    JZ food_entry_3
    SUBI 1
    JZ food_entry_4
    SUBI 1
    JZ food_entry_5
    SUBI 1
    JZ food_entry_6
    SUBI 1
    JZ food_entry_7
    SUBI 1
    JZ food_entry_8
    SUBI 1
    JZ food_entry_9
    SUBI 1
    JZ food_entry_10
    SUBI 1
    JZ food_entry_11
    SUBI 1
    JZ food_entry_12
    SUBI 1
    JZ food_entry_13
    SUBI 1
    JZ food_entry_14
    SUBI 1
    JZ food_entry_15
    JMP bitmap_fault
food_table_hi_1:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_16
    SUBI 1
    JZ food_entry_17
    SUBI 1
    JZ food_entry_18
    SUBI 1
    JZ food_entry_19
    SUBI 1
    JZ food_entry_20
    SUBI 1
    JZ food_entry_21
    SUBI 1
    JZ food_entry_22
    SUBI 1
    JZ food_entry_23
    SUBI 1
    JZ food_entry_24
    SUBI 1
    JZ food_entry_25
    SUBI 1
    JZ food_entry_26
    SUBI 1
    JZ food_entry_27
    SUBI 1
    JZ food_entry_28
    SUBI 1
    JZ food_entry_29
    SUBI 1
    JZ food_entry_30
    SUBI 1
    JZ food_entry_31
    JMP bitmap_fault
food_table_hi_2:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_32
    SUBI 1
    JZ food_entry_33
    SUBI 1
    JZ food_entry_34
    SUBI 1
    JZ food_entry_35
    SUBI 1
    JZ food_entry_36
    SUBI 1
    JZ food_entry_37
    SUBI 1
    JZ food_entry_38
    SUBI 1
    JZ food_entry_39
    SUBI 1
    JZ food_entry_40
    SUBI 1
    JZ food_entry_41
    SUBI 1
    JZ food_entry_42
    SUBI 1
    JZ food_entry_43
    SUBI 1
    JZ food_entry_44
    SUBI 1
    JZ food_entry_45
    SUBI 1
    JZ food_entry_46
    SUBI 1
    JZ food_entry_47
    JMP bitmap_fault
food_table_hi_3:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_48
    SUBI 1
    JZ food_entry_49
    SUBI 1
    JZ food_entry_50
    SUBI 1
    JZ food_entry_51
    SUBI 1
    JZ food_entry_52
    SUBI 1
    JZ food_entry_53
    SUBI 1
    JZ food_entry_54
    SUBI 1
    JZ food_entry_55
    SUBI 1
    JZ food_entry_56
    SUBI 1
    JZ food_entry_57
    SUBI 1
    JZ food_entry_58
    SUBI 1
    JZ food_entry_59
    SUBI 1
    JZ food_entry_60
    SUBI 1
    JZ food_entry_61
    SUBI 1
    JZ food_entry_62
    SUBI 1
    JZ food_entry_63
    JMP bitmap_fault
food_table_hi_4:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_64
    SUBI 1
    JZ food_entry_65
    SUBI 1
    JZ food_entry_66
    SUBI 1
    JZ food_entry_67
    SUBI 1
    JZ food_entry_68
    SUBI 1
    JZ food_entry_69
    SUBI 1
    JZ food_entry_70
    SUBI 1
    JZ food_entry_71
    SUBI 1
    JZ food_entry_72
    SUBI 1
    JZ food_entry_73
    SUBI 1
    JZ food_entry_74
    SUBI 1
    JZ food_entry_75
    SUBI 1
    JZ food_entry_76
    SUBI 1
    JZ food_entry_77
    SUBI 1
    JZ food_entry_78
    SUBI 1
    JZ food_entry_79
    JMP bitmap_fault
food_table_hi_5:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_80
    SUBI 1
    JZ food_entry_81
    SUBI 1
    JZ food_entry_82
    SUBI 1
    JZ food_entry_83
    SUBI 1
    JZ food_entry_84
    SUBI 1
    JZ food_entry_85
    SUBI 1
    JZ food_entry_86
    SUBI 1
    JZ food_entry_87
    SUBI 1
    JZ food_entry_88
    SUBI 1
    JZ food_entry_89
    SUBI 1
    JZ food_entry_90
    SUBI 1
    JZ food_entry_91
    SUBI 1
    JZ food_entry_92
    SUBI 1
    JZ food_entry_93
    SUBI 1
    JZ food_entry_94
    SUBI 1
    JZ food_entry_95
    JMP bitmap_fault
food_table_hi_6:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_96
    SUBI 1
    JZ food_entry_97
    SUBI 1
    JZ food_entry_98
    SUBI 1
    JZ food_entry_99
    SUBI 1
    JZ food_entry_100
    SUBI 1
    JZ food_entry_101
    SUBI 1
    JZ food_entry_102
    SUBI 1
    JZ food_entry_103
    SUBI 1
    JZ food_entry_104
    SUBI 1
    JZ food_entry_105
    SUBI 1
    JZ food_entry_106
    SUBI 1
    JZ food_entry_107
    SUBI 1
    JZ food_entry_108
    SUBI 1
    JZ food_entry_109
    SUBI 1
    JZ food_entry_110
    SUBI 1
    JZ food_entry_111
    JMP bitmap_fault
food_table_hi_7:
    LD FOOD_SEQ_LO
    SUBI 0
    JZ food_entry_112
    SUBI 1
    JZ food_entry_113
    SUBI 1
    JZ food_entry_114
    SUBI 1
    JZ food_entry_115
    SUBI 1
    JZ food_entry_116
    SUBI 1
    JZ food_entry_117
    SUBI 1
    JZ food_entry_118
    SUBI 1
    JZ food_entry_119
    SUBI 1
    JZ food_entry_120
    SUBI 1
    JZ food_entry_121
    SUBI 1
    JZ food_entry_122
    SUBI 1
    JZ food_entry_123
    SUBI 1
    JZ food_entry_124
    SUBI 1
    JZ food_entry_125
    SUBI 1
    JZ food_entry_126
    SUBI 1
    JZ food_entry_127
    JMP bitmap_fault
food_entry_0:
    LDI 10
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_1:
    LDI 2
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_2:
    LDI 13
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_3:
    LDI 5
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_4:
    LDI 1
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_5:
    LDI 14
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_6:
    LDI 7
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_7:
    LDI 11
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_8:
    LDI 3
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_9:
    LDI 15
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_10:
    LDI 0
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_11:
    LDI 8
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_12:
    LDI 11
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_13:
    LDI 12
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_14:
    LDI 14
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_15:
    LDI 8
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_16:
    LDI 6
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_17:
    LDI 10
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_18:
    LDI 3
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_19:
    LDI 4
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_20:
    LDI 13
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_21:
    LDI 13
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_22:
    LDI 0
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_23:
    LDI 6
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_24:
    LDI 13
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_25:
    LDI 1
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_26:
    LDI 0
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_27:
    LDI 13
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_28:
    LDI 5
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_29:
    LDI 6
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_30:
    LDI 3
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_31:
    LDI 0
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_32:
    LDI 8
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_33:
    LDI 2
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_34:
    LDI 14
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_35:
    LDI 4
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_36:
    LDI 1
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_37:
    LDI 5
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_38:
    LDI 14
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_39:
    LDI 13
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_40:
    LDI 15
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_41:
    LDI 8
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_42:
    LDI 7
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_43:
    LDI 10
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_44:
    LDI 15
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_45:
    LDI 9
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_46:
    LDI 4
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_47:
    LDI 8
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_48:
    LDI 1
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_49:
    LDI 11
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_50:
    LDI 0
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_51:
    LDI 15
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_52:
    LDI 4
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_53:
    LDI 11
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_54:
    LDI 12
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_55:
    LDI 4
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_56:
    LDI 3
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_57:
    LDI 3
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_58:
    LDI 4
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_59:
    LDI 12
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_60:
    LDI 10
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_61:
    LDI 11
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_62:
    LDI 2
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_63:
    LDI 2
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_64:
    LDI 9
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_65:
    LDI 10
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_66:
    LDI 9
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_67:
    LDI 0
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_68:
    LDI 8
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_69:
    LDI 7
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_70:
    LDI 5
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_71:
    LDI 5
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_72:
    LDI 9
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_73:
    LDI 2
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_74:
    LDI 14
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_75:
    LDI 12
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_76:
    LDI 6
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_77:
    LDI 14
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_78:
    LDI 2
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_79:
    LDI 11
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_80:
    LDI 12
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_81:
    LDI 4
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_82:
    LDI 6
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_83:
    LDI 9
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_84:
    LDI 13
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_85:
    LDI 11
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_86:
    LDI 15
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_87:
    LDI 0
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_88:
    LDI 12
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_89:
    LDI 10
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_90:
    LDI 0
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_91:
    LDI 1
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_92:
    LDI 1
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_93:
    LDI 7
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_94:
    LDI 7
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_95:
    LDI 6
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_96:
    LDI 3
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_97:
    LDI 15
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_98:
    LDI 14
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_99:
    LDI 15
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_100:
    LDI 1
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_101:
    LDI 5
    ST LOOK_X
    LDI 0
    ST LOOK_Y
    JMP food_table_return
food_entry_102:
    LDI 2
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_103:
    LDI 3
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_104:
    LDI 11
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_105:
    LDI 7
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_106:
    LDI 7
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_107:
    LDI 9
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_108:
    LDI 10
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_109:
    LDI 8
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_110:
    LDI 3
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_111:
    LDI 12
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_112:
    LDI 14
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_113:
    LDI 5
    ST LOOK_X
    LDI 4
    ST LOOK_Y
    JMP food_table_return
food_entry_114:
    LDI 7
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_115:
    LDI 6
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_116:
    LDI 2
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_117:
    LDI 8
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
food_entry_118:
    LDI 15
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_119:
    LDI 10
    ST LOOK_X
    LDI 1
    ST LOOK_Y
    JMP food_table_return
food_entry_120:
    LDI 1
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_121:
    LDI 9
    ST LOOK_X
    LDI 7
    ST LOOK_Y
    JMP food_table_return
food_entry_122:
    LDI 12
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_123:
    LDI 6
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_124:
    LDI 5
    ST LOOK_X
    LDI 2
    ST LOOK_Y
    JMP food_table_return
food_entry_125:
    LDI 13
    ST LOOK_X
    LDI 6
    ST LOOK_Y
    JMP food_table_return
food_entry_126:
    LDI 9
    ST LOOK_X
    LDI 5
    ST LOOK_Y
    JMP food_table_return
food_entry_127:
    LDI 4
    ST LOOK_X
    LDI 3
    ST LOOK_Y
    JMP food_table_return
