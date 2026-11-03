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
    ; Search starts at old_food+1, wraps over all 128 legal field positions.
    LD FOOD_X
    ST LOOK_X
    LD FOOD_Y
    ST LOOK_Y
food_next_candidate:
    LD LOOK_X
    ADDI 1
    ST LOOK_X
    LD LOOK_Y
    ADCI 0
    ANDI 7
    ST LOOK_Y
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
