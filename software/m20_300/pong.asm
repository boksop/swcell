; M20-300 16-bit instruction-word Pong core prototype.
; All game decisions below execute as CPU instructions; no OLED output yet.
; Six-key logical input: IN0 bits0/1=left up/down, bits2/3=right up/down.
; IN1 is sampled and retained, but its two action keys are reserved here.

.equ BALL_X,       0x00
.equ BALL_Y,       0x01
.equ VX,           0x02
.equ VY,           0x03
.equ PADDLE_L,     0x04
.equ PADDLE_R,     0x05
.equ SCORE_L_LO,   0x06
.equ SCORE_L_HI,   0x07
.equ SCORE_R_LO,   0x08
.equ SCORE_R_HI,   0x09
.equ EVENT,        0x0A
.equ KEYS0,        0x0B
.equ KEYS1,        0x0C
.equ CTRL,         0x20
.equ RETURN_ID,    0xF0

.org 0
boot:
    LDI 8
    ST BALL_X
    LDI 4
    ST BALL_Y
    LDI 0
    ST VX
    ST VY
    ST SCORE_L_LO
    ST SCORE_L_HI
    ST SCORE_R_LO
    ST SCORE_R_HI
    ST EVENT
    ST KEYS0
    ST KEYS1
    ST CTRL
    ST RETURN_ID
    LDI 2
    ST PADDLE_L
    ST PADDLE_R

tick:
    IN0
    ST KEYS0
    IN1
    ST KEYS1
    LDI 0
    ST EVENT

    ; First call: update left paddle at dynamic RAM address AR=04.
    LD KEYS0
    ANDI 3
    ST CTRL
    ARH 0
    ARL 4
    LDI 1
    ST RETURN_ID
    JMP update_paddle
after_left_paddle:
    ; Second call: update right paddle at AR=05 using key bits2/3.
    LD KEYS0
    SHR
    SHR
    ANDI 3
    ST CTRL
    ARH 0
    ARL 5
    LDI 2
    ST RETURN_ID
    JMP update_paddle
after_right_paddle:

    ; Vertical motion.  VY=0 means down, VY=1 means up.
    LD VY
    JZ move_down
move_up:
    LD BALL_Y
    JZ bounce_top
    SUBI 1
    ST BALL_Y
    JMP vertical_done
bounce_top:
    LDI 1
    ST BALL_Y
    LDI 0
    ST VY
    LDI 1
    ST EVENT
    JMP vertical_done
move_down:
    LD BALL_Y
    SUBI 7
    JZ bounce_bottom
    LD BALL_Y
    ADDI 1
    ST BALL_Y
    JMP vertical_done
bounce_bottom:
    LDI 6
    ST BALL_Y
    LDI 1
    ST VY
    LDI 1
    ST EVENT
vertical_done:

    ; Horizontal motion.  VX=0 means right, VX=1 means left.
    LD VX
    JZ move_right
move_left:
    LD BALL_X
    SUBI 1
    JZ left_contact
    ST BALL_X
    JMP tick_done
left_contact:
    ; A paddle is three cells high: top <= new_y < top+3.
    ; SUB C=no-borrow identifies new_y >= top without a B register.
    LD BALL_Y
    SUB PADDLE_L
    JC left_contact_lower_ok
    JMP right_scores
left_contact_lower_ok:
    SUBI 3
    JC right_scores
    ; BALL_X stays1 on a left-paddle bounce.
    LDI 0
    ST VX
    LD EVENT
    ADDI 2
    ST EVENT
    JMP tick_done
move_right:
    LD BALL_X
    SUBI 14
    JZ right_contact
    LD BALL_X
    ADDI 1
    ST BALL_X
    JMP tick_done
right_contact:
    LD BALL_Y
    SUB PADDLE_R
    JC right_contact_lower_ok
    JMP left_scores
right_contact_lower_ok:
    SUBI 3
    JC left_scores
    ; BALL_X stays14 on a right-paddle bounce.
    LDI 1
    ST VX
    LD EVENT
    ADDI 2
    ST EVENT
    JMP tick_done

right_scores:
    ; Increment little-nibble 8-bit score. LD/ST must preserve carry.
    LD SCORE_R_LO
    ADDI 1
    ST SCORE_R_LO
    LD SCORE_R_HI
    ADCI 0
    ST SCORE_R_HI
    LDI 8
    ST BALL_X
    LDI 4
    ST BALL_Y
    LDI 1
    ST VX
    LDI 0
    ST VY
    LDI 8
    ST EVENT
    JMP tick_done
left_scores:
    LD SCORE_L_LO
    ADDI 1
    ST SCORE_L_LO
    LD SCORE_L_HI
    ADCI 0
    ST SCORE_L_HI
    LDI 8
    ST BALL_X
    LDI 4
    ST BALL_Y
    LDI 0
    ST VX
    ST VY
    LDI 4
    ST EVENT
    JMP tick_done

tick_done:
    ; Test harness may observe this address, then resume the real loop.
    NOP
    JMP tick

update_paddle:
    ; Call ABI: AR=target paddle cell, CTRL=two direction bits,
    ; RETURN_ID=1 or2. Up+down (CTRL=3) cancels; CTRL=0 holds.
    ; Clobbers A/Z/C; preserves AR. No hardware CALL/RET is assumed.
    LD CTRL
    SUBI 1
    JZ paddle_up
    LD CTRL
    SUBI 2
    JZ paddle_down
    JMP return_dispatch
paddle_up:
    LD [AR]
    JZ return_dispatch
    SUBI 1
    ST [AR]
    JMP return_dispatch
paddle_down:
    LD [AR]
    SUBI 5
    JC return_dispatch
    LD [AR]
    ADDI 1
    ST [AR]
return_dispatch:
    LD RETURN_ID
    SUBI 1
    JZ after_left_paddle
    LD RETURN_ID
    SUBI 2
    JZ after_right_paddle
bad_return_id:
    ; This is a software ABI diagnostic halt, not a CPU return instruction.
    HALT
