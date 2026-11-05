.equ HI, 224
.equ LO, 225
.equ DC, 226
.equ SHIFT, 227
.equ BITS, 228
.equ HALF, 229
.equ PIX, 230
.equ X, 231
.equ Y, 232
.equ REP, 233
.equ PAGE, 234
.equ COL, 235
.equ ROW, 236
.equ CAND0, 36
.equ CAND1, 37
.equ STABLE0, 38
.equ STABLE1, 39
.equ PREV0, 40
.equ PREV1, 41
.equ EDGE0, 42
.equ EDGE1, 43
.equ COUNT, 44
.equ MODE, 45
.equ SELECT, 46
.equ COMBO0, 47
.equ COMBO1, 48
.equ COMBO2, 49
.equ DLY0, 50
.equ DLY1, 51
.equ RELEASE0, 52
.equ RELEASE1, 53
.equ OLDX, 54
.equ OLDY, 55
.equ OLDL, 56
.equ OLDR, 57
.equ TICKS, 58
.equ TEMP, 59
.equ PENDING, 60
.equ PLAYKEYS, 61
.equ TICKHI, 62
boot:
ARH 0
ARL 0
clear_ram:
LDI 0
ST [AR]
INCAR
MOVA ARL
ANDI 15
JZ clear_hi
JMP clear_ram
clear_hi:
MOVA ARH
ANDI 15
JZ oled_init
JMP clear_ram
oled_init:
LDI 10
ST HI
LDI 14
ST LO
LDI 0
ST DC
LDI 0
ST 237
LDI 0
ST 238
JMP spi
cont_0:
LDI 13
ST HI
LDI 5
ST LO
LDI 0
ST DC
LDI 1
ST 237
LDI 0
ST 238
JMP spi
cont_1:
LDI 8
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 2
ST 237
LDI 0
ST 238
JMP spi
cont_2:
LDI 10
ST HI
LDI 8
ST LO
LDI 0
ST DC
LDI 3
ST 237
LDI 0
ST 238
JMP spi
cont_3:
LDI 3
ST HI
LDI 15
ST LO
LDI 0
ST DC
LDI 4
ST 237
LDI 0
ST 238
JMP spi
cont_4:
LDI 13
ST HI
LDI 3
ST LO
LDI 0
ST DC
LDI 5
ST 237
LDI 0
ST 238
JMP spi
cont_5:
LDI 0
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 6
ST 237
LDI 0
ST 238
JMP spi
cont_6:
LDI 4
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 7
ST 237
LDI 0
ST 238
JMP spi
cont_7:
LDI 8
ST HI
LDI 13
ST LO
LDI 0
ST DC
LDI 8
ST 237
LDI 0
ST 238
JMP spi
cont_8:
LDI 1
ST HI
LDI 4
ST LO
LDI 0
ST DC
LDI 9
ST 237
LDI 0
ST 238
JMP spi
cont_9:
LDI 2
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 10
ST 237
LDI 0
ST 238
JMP spi
cont_10:
LDI 0
ST HI
LDI 2
ST LO
LDI 0
ST DC
LDI 11
ST 237
LDI 0
ST 238
JMP spi
cont_11:
LDI 10
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 12
ST 237
LDI 0
ST 238
JMP spi
cont_12:
LDI 12
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 13
ST 237
LDI 0
ST 238
JMP spi
cont_13:
LDI 13
ST HI
LDI 10
ST LO
LDI 0
ST DC
LDI 14
ST 237
LDI 0
ST 238
JMP spi
cont_14:
LDI 1
ST HI
LDI 2
ST LO
LDI 0
ST DC
LDI 15
ST 237
LDI 0
ST 238
JMP spi
cont_15:
LDI 8
ST HI
LDI 1
ST LO
LDI 0
ST DC
LDI 0
ST 237
LDI 1
ST 238
JMP spi
cont_16:
LDI 7
ST HI
LDI 15
ST LO
LDI 0
ST DC
LDI 1
ST 237
LDI 1
ST 238
JMP spi
cont_17:
LDI 13
ST HI
LDI 9
ST LO
LDI 0
ST DC
LDI 2
ST 237
LDI 1
ST 238
JMP spi
cont_18:
LDI 15
ST HI
LDI 1
ST LO
LDI 0
ST DC
LDI 3
ST 237
LDI 1
ST 238
JMP spi
cont_19:
LDI 13
ST HI
LDI 11
ST LO
LDI 0
ST DC
LDI 4
ST 237
LDI 1
ST 238
JMP spi
cont_20:
LDI 4
ST HI
LDI 0
ST LO
LDI 0
ST DC
LDI 5
ST 237
LDI 1
ST 238
JMP spi
cont_21:
LDI 10
ST HI
LDI 4
ST LO
LDI 0
ST DC
LDI 6
ST 237
LDI 1
ST 238
JMP spi
cont_22:
LDI 10
ST HI
LDI 6
ST LO
LDI 0
ST DC
LDI 7
ST 237
LDI 1
ST 238
JMP spi
cont_23:
LDI 2
ST HI
LDI 14
ST LO
LDI 0
ST DC
LDI 8
ST 237
LDI 1
ST 238
JMP spi
cont_24:
LDI 0
ST 239
JMP clear_screen
cont_25:
LDI 10
ST HI
LDI 15
ST LO
LDI 0
ST DC
LDI 9
ST 237
LDI 1
ST 238
JMP spi
cont_26:
menu_enter:
LDI 0
ST MODE
LDI 0
ST STABLE0
LDI 0
ST STABLE1
LDI 0
ST EDGE0
LDI 0
ST EDGE1
LDI 0
ST PENDING
LDI 0
ST COUNT
LDI 1
ST 239
JMP clear_screen
cont_27:
LDI 2
ST X
LDI 0
ST Y
LDI 0
ST 240
JMP address
cont_28:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 10
ST 237
LDI 1
ST 238
JMP spi
cont_29:
LDI 0
ST HI
LDI 2
ST LO
LDI 4
ST DC
LDI 11
ST 237
LDI 1
ST 238
JMP spi
cont_30:
LDI 0
ST HI
LDI 12
ST LO
LDI 4
ST DC
LDI 12
ST 237
LDI 1
ST 238
JMP spi
cont_31:
LDI 0
ST HI
LDI 2
ST LO
LDI 4
ST DC
LDI 13
ST 237
LDI 1
ST 238
JMP spi
cont_32:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 14
ST 237
LDI 1
ST 238
JMP spi
cont_33:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 15
ST 237
LDI 1
ST 238
JMP spi
cont_34:
LDI 6
ST HI
LDI 2
ST LO
LDI 4
ST DC
LDI 0
ST 237
LDI 2
ST 238
JMP spi
cont_35:
LDI 5
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 1
ST 237
LDI 2
ST 238
JMP spi
cont_36:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 2
ST 237
LDI 2
ST 238
JMP spi
cont_37:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 3
ST 237
LDI 2
ST 238
JMP spi
cont_38:
LDI 4
ST HI
LDI 6
ST LO
LDI 4
ST DC
LDI 4
ST 237
LDI 2
ST 238
JMP spi
cont_39:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 5
ST 237
LDI 2
ST 238
JMP spi
cont_40:
LDI 3
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 6
ST 237
LDI 2
ST 238
JMP spi
cont_41:
LDI 5
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 7
ST 237
LDI 2
ST 238
JMP spi
cont_42:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 8
ST 237
LDI 2
ST 238
JMP spi
cont_43:
LDI 4
ST HI
LDI 5
ST LO
LDI 4
ST DC
LDI 9
ST 237
LDI 2
ST 238
JMP spi
cont_44:
LDI 3
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 10
ST 237
LDI 2
ST 238
JMP spi
cont_45:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 11
ST 237
LDI 2
ST 238
JMP spi
cont_46:
LDI 2
ST X
LDI 2
ST Y
LDI 1
ST 240
JMP address
cont_47:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 12
ST 237
LDI 2
ST 238
JMP spi
cont_48:
LDI 0
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 13
ST 237
LDI 2
ST 238
JMP spi
cont_49:
LDI 0
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 14
ST 237
LDI 2
ST 238
JMP spi
cont_50:
LDI 0
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 15
ST 237
LDI 2
ST 238
JMP spi
cont_51:
LDI 0
ST HI
LDI 6
ST LO
LDI 4
ST DC
LDI 0
ST 237
LDI 3
ST 238
JMP spi
cont_52:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 1
ST 237
LDI 3
ST 238
JMP spi
cont_53:
LDI 3
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 2
ST 237
LDI 3
ST 238
JMP spi
cont_54:
LDI 4
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 3
ST 237
LDI 3
ST 238
JMP spi
cont_55:
LDI 4
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 4
ST 237
LDI 3
ST 238
JMP spi
cont_56:
LDI 4
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 5
ST 237
LDI 3
ST 238
JMP spi
cont_57:
LDI 3
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 6
ST 237
LDI 3
ST 238
JMP spi
cont_58:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 7
ST 237
LDI 3
ST 238
JMP spi
cont_59:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 8
ST 237
LDI 3
ST 238
JMP spi
cont_60:
LDI 0
ST HI
LDI 2
ST LO
LDI 4
ST DC
LDI 9
ST 237
LDI 3
ST 238
JMP spi
cont_61:
LDI 0
ST HI
LDI 4
ST LO
LDI 4
ST DC
LDI 10
ST 237
LDI 3
ST 238
JMP spi
cont_62:
LDI 0
ST HI
LDI 8
ST LO
LDI 4
ST DC
LDI 11
ST 237
LDI 3
ST 238
JMP spi
cont_63:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 12
ST 237
LDI 3
ST 238
JMP spi
cont_64:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 13
ST 237
LDI 3
ST 238
JMP spi
cont_65:
LDI 3
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 14
ST 237
LDI 3
ST 238
JMP spi
cont_66:
LDI 4
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 15
ST 237
LDI 3
ST 238
JMP spi
cont_67:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 0
ST 237
LDI 4
ST 238
JMP spi
cont_68:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 1
ST 237
LDI 4
ST 238
JMP spi
cont_69:
LDI 7
ST HI
LDI 10
ST LO
LDI 4
ST DC
LDI 2
ST 237
LDI 4
ST 238
JMP spi
cont_70:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 3
ST 237
LDI 4
ST 238
JMP spi
cont_71:
LDI 2
ST X
LDI 4
ST Y
LDI 2
ST 240
JMP address
cont_72:
LDI 4
ST HI
LDI 6
ST LO
LDI 4
ST DC
LDI 4
ST 237
LDI 4
ST 238
JMP spi
cont_73:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 5
ST 237
LDI 4
ST 238
JMP spi
cont_74:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 6
ST 237
LDI 4
ST 238
JMP spi
cont_75:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 7
ST 237
LDI 4
ST 238
JMP spi
cont_76:
LDI 3
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 8
ST 237
LDI 4
ST 238
JMP spi
cont_77:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 9
ST 237
LDI 4
ST 238
JMP spi
cont_78:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 10
ST 237
LDI 4
ST 238
JMP spi
cont_79:
LDI 0
ST HI
LDI 2
ST LO
LDI 4
ST DC
LDI 11
ST 237
LDI 4
ST 238
JMP spi
cont_80:
LDI 0
ST HI
LDI 4
ST LO
LDI 4
ST DC
LDI 12
ST 237
LDI 4
ST 238
JMP spi
cont_81:
LDI 0
ST HI
LDI 8
ST LO
LDI 4
ST DC
LDI 13
ST 237
LDI 4
ST 238
JMP spi
cont_82:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 14
ST 237
LDI 4
ST 238
JMP spi
cont_83:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 15
ST 237
LDI 4
ST 238
JMP spi
cont_84:
LDI 7
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 0
ST 237
LDI 5
ST 238
JMP spi
cont_85:
LDI 0
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 1
ST 237
LDI 5
ST 238
JMP spi
cont_86:
LDI 0
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 2
ST 237
LDI 5
ST 238
JMP spi
cont_87:
LDI 0
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 3
ST 237
LDI 5
ST 238
JMP spi
cont_88:
LDI 7
ST HI
LDI 14
ST LO
LDI 4
ST DC
LDI 4
ST 237
LDI 5
ST 238
JMP spi
cont_89:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 5
ST 237
LDI 5
ST 238
JMP spi
cont_90:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 6
ST 237
LDI 5
ST 238
JMP spi
cont_91:
LDI 0
ST HI
LDI 8
ST LO
LDI 4
ST DC
LDI 7
ST 237
LDI 5
ST 238
JMP spi
cont_92:
LDI 1
ST HI
LDI 4
ST LO
LDI 4
ST DC
LDI 8
ST 237
LDI 5
ST 238
JMP spi
cont_93:
LDI 2
ST HI
LDI 2
ST LO
LDI 4
ST DC
LDI 9
ST 237
LDI 5
ST 238
JMP spi
cont_94:
LDI 4
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 10
ST 237
LDI 5
ST 238
JMP spi
cont_95:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 11
ST 237
LDI 5
ST 238
JMP spi
cont_96:
LDI 7
ST HI
LDI 15
ST LO
LDI 4
ST DC
LDI 12
ST 237
LDI 5
ST 238
JMP spi
cont_97:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 13
ST 237
LDI 5
ST 238
JMP spi
cont_98:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 14
ST 237
LDI 5
ST 238
JMP spi
cont_99:
LDI 4
ST HI
LDI 9
ST LO
LDI 4
ST DC
LDI 15
ST 237
LDI 5
ST 238
JMP spi
cont_100:
LDI 4
ST HI
LDI 1
ST LO
LDI 4
ST DC
LDI 0
ST 237
LDI 6
ST 238
JMP spi
cont_101:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 1
ST 237
LDI 6
ST 238
JMP spi
cont_102:
menu_redraw:
LDI 0
ST X
LDI 2
ST Y
LDI 0
ST PIX
LD SELECT
JZ mark_pong
JMP pong_mark_ready
mark_pong:
LDI 15
ST PIX
pong_mark_ready:
LDI 0
ST 241
JMP cell
cont_103:
LDI 0
ST X
LDI 4
ST Y
LDI 0
ST PIX
LD SELECT
JZ snake_mark_ready
LDI 15
ST PIX
snake_mark_ready:
LDI 1
ST 241
JMP cell
cont_104:
menu_loop:
LDI 0
ST 242
JMP poll_wait
cont_105:
LD EDGE0
ST TEMP
LDI 0
ST EDGE0
LD TEMP
ANDI 3
JZ menu_action
LD SELECT
XORI 1
ST SELECT
JMP menu_redraw
menu_action:
LD EDGE1
ST TEMP
LDI 0
ST EDGE1
LD TEMP
ANDI 2
JZ menu_a
LDI 0
ST SELECT
JMP menu_redraw
menu_a:
LD TEMP
ANDI 1
JZ menu_loop
LDI 2
ST 239
JMP clear_screen
cont_106:
LDI 15
ST OLDL
LDI 15
ST OLDR
LD SELECT
JZ launch_pong
launch_snake:
LDI 2
ST MODE
LDI 0
ST PENDING
ST PLAYKEYS
JMP S_boot
launch_pong:
LDI 1
ST MODE
LDI 15
ST OLDL
ST OLDR
LDI 0
ST PENDING
ST PLAYKEYS
JMP P_boot
game_after_tick:
LD MODE
SUBI 1
JZ draw_pong
JMP draw_snake
draw_pong:
LD OLDX
ST X
LD OLDY
ST Y
LDI 0
ST PIX
LDI 2
ST 241
JMP cell
cont_107:
LD OLDL
CMP P_PADDLE_L
JZ paddle_skip_0
LD OLDL
SUBI 15
JZ paddle_first_0
LDI 0
ST X
LD OLDL
ST Y
LDI 0
ST PIX
LDI 0
ST 243
JMP paddle
cont_108:
paddle_first_0:
LDI 0
ST X
LD P_PADDLE_L
ST Y
ST OLDL
LDI 15
ST PIX
LDI 1
ST 243
JMP paddle
cont_109:
paddle_skip_0:
LD OLDR
CMP P_PADDLE_R
JZ paddle_skip_15
LD OLDR
SUBI 15
JZ paddle_first_15
LDI 15
ST X
LD OLDR
ST Y
LDI 0
ST PIX
LDI 2
ST 243
JMP paddle
cont_110:
paddle_first_15:
LDI 15
ST X
LD P_PADDLE_R
ST Y
ST OLDR
LDI 15
ST PIX
LDI 3
ST 243
JMP paddle
cont_111:
paddle_skip_15:
LD P_BALL_X
ST X
ST OLDX
LD P_BALL_Y
ST Y
ST OLDY
LDI 6
ST PIX
LDI 3
ST 241
JMP cell
cont_112:
LDI 5
ST X
LDI 0
ST Y
LDI 3
ST 240
JMP address
cont_113:
LD P_SCORE_L_HI
ST PIX
LDI 0
ST 244
JMP hex_digit
cont_114:
LD P_SCORE_L_LO
ST PIX
LDI 1
ST 244
JMP hex_digit
cont_115:
LDI 10
ST X
LDI 0
ST Y
LDI 4
ST 240
JMP address
cont_116:
LD P_SCORE_R_HI
ST PIX
LDI 2
ST 244
JMP hex_digit
cont_117:
LD P_SCORE_R_LO
ST PIX
LDI 3
ST 244
JMP hex_digit
cont_118:
JMP game_delay
draw_snake:
LD S_EVENT
ANDI 15
JZ erase_tail
JMP tail_erased
erase_tail:
LD S_OLD_TAIL_X
ST X
LD S_OLD_TAIL_Y
ST Y
LDI 0
ST PIX
LDI 4
ST 241
JMP cell
cont_119:
tail_erased:
LD S_EVENT
SUBI 4
JZ snake_initial
JMP snake_current
snake_initial:
LDI 2
ST X
LDI 3
ST Y
LDI 15
ST PIX
LDI 5
ST 241
JMP cell
cont_120:
LDI 3
ST X
LDI 3
ST Y
LDI 15
ST PIX
LDI 6
ST 241
JMP cell
cont_121:
LDI 4
ST X
LDI 3
ST Y
LDI 15
ST PIX
LDI 7
ST 241
JMP cell
cont_122:
snake_current:
LD S_HEAD_LO
SHL
ST TEMP
LD S_HEAD_HI
ADC S_HEAD_HI
ADDI 4
MOVARH A
LD TEMP
MOVARL A
LD [AR]
ST X
INCAR
LD [AR]
ST Y
LDI 15
ST PIX
LDI 8
ST 241
JMP cell
cont_123:
LD S_FOOD_X
ST X
LD S_FOOD_Y
ST Y
LDI 6
ST PIX
LDI 9
ST 241
JMP cell
cont_124:
game_delay:
LDI 0
ST TICKS
LDI 0
ST TICKHI
game_poll:
LDI 1
ST 242
JMP poll_wait
cont_125:
LD EDGE1
ST TEMP
LDI 0
ST EDGE1
ST EDGE0
LD TEMP
ANDI 2
JZ game_a
JMP menu_enter
game_a:
LD TEMP
ANDI 1
JZ game_time
JMP restart_game
game_time_jump:
LD MODE
SUBI 1
JZ launch_pong
JMP launch_snake
game_time:
LD COMBO2
SUBI 2
JC menu_enter
LD TICKS
ADDI 1
ST TICKS
LD TICKHI
ADCI 0
ST TICKHI
LD MODE
SUBI 1
JZ pong_time
LD TICKHI
SUBI 2
JC snake_time_low
JMP game_poll
snake_time_low:
LD TICKS
SUBI 8
JC game_tick
JMP game_poll
pong_time:
LD TICKHI
SUBI 1
JC game_tick
JMP game_poll
game_tick:
LD PENDING
ANDI 15
JZ use_level
ST PLAYKEYS
JMP clear_pending
use_level:
LD STABLE0
ST PLAYKEYS
clear_pending:
LDI 0
ST PENDING
LD MODE
SUBI 1
JZ P_tick
JMP S_tick
restart_game:
LDI 3
ST 239
JMP clear_screen
cont_126:
JMP game_time_jump
spi:
LDI 0
ST HALF
LD HI
ST SHIFT
spi_half:
LDI 4
ST BITS
spi_bit:
LD SHIFT
ANDI 8
JZ spi_zero
LDI 1
JMP spi_level
spi_zero:
LDI 0
spi_level:
OR DC
OUT
ADDI 2
OUT
SUBI 2
OUT
LD SHIFT
SHL
ST SHIFT
LD BITS
SUBI 1
ST BITS
JZ spi_half_done
JMP spi_bit
spi_half_done:
LD HALF
ANDI 1
JZ spi_low
LD DC
ADDI 8
OUT
LD 238
SUBI 0
JZ ret_spi_0
LD 238
SUBI 1
JZ ret_spi_1
LD 238
SUBI 2
JZ ret_spi_2
LD 238
SUBI 3
JZ ret_spi_3
LD 238
SUBI 4
JZ ret_spi_4
LD 238
SUBI 5
JZ ret_spi_5
LD 238
SUBI 6
JZ ret_spi_6
LD 238
SUBI 7
JZ ret_spi_7
LD 238
SUBI 8
JZ ret_spi_8
LD 238
SUBI 9
JZ ret_spi_9
HALT
ret_spi_0:
LD 237
ANDI 15
JZ cont_0
SUBI 1
JZ cont_1
SUBI 1
JZ cont_2
SUBI 1
JZ cont_3
SUBI 1
JZ cont_4
SUBI 1
JZ cont_5
SUBI 1
JZ cont_6
SUBI 1
JZ cont_7
SUBI 1
JZ cont_8
SUBI 1
JZ cont_9
SUBI 1
JZ cont_10
SUBI 1
JZ cont_11
SUBI 1
JZ cont_12
SUBI 1
JZ cont_13
SUBI 1
JZ cont_14
SUBI 1
JZ cont_15
HALT
ret_spi_1:
LD 237
ANDI 15
JZ cont_16
SUBI 1
JZ cont_17
SUBI 1
JZ cont_18
SUBI 1
JZ cont_19
SUBI 1
JZ cont_20
SUBI 1
JZ cont_21
SUBI 1
JZ cont_22
SUBI 1
JZ cont_23
SUBI 1
JZ cont_24
SUBI 1
JZ cont_26
SUBI 1
JZ cont_29
SUBI 1
JZ cont_30
SUBI 1
JZ cont_31
SUBI 1
JZ cont_32
SUBI 1
JZ cont_33
SUBI 1
JZ cont_34
HALT
ret_spi_2:
LD 237
ANDI 15
JZ cont_35
SUBI 1
JZ cont_36
SUBI 1
JZ cont_37
SUBI 1
JZ cont_38
SUBI 1
JZ cont_39
SUBI 1
JZ cont_40
SUBI 1
JZ cont_41
SUBI 1
JZ cont_42
SUBI 1
JZ cont_43
SUBI 1
JZ cont_44
SUBI 1
JZ cont_45
SUBI 1
JZ cont_46
SUBI 1
JZ cont_48
SUBI 1
JZ cont_49
SUBI 1
JZ cont_50
SUBI 1
JZ cont_51
HALT
ret_spi_3:
LD 237
ANDI 15
JZ cont_52
SUBI 1
JZ cont_53
SUBI 1
JZ cont_54
SUBI 1
JZ cont_55
SUBI 1
JZ cont_56
SUBI 1
JZ cont_57
SUBI 1
JZ cont_58
SUBI 1
JZ cont_59
SUBI 1
JZ cont_60
SUBI 1
JZ cont_61
SUBI 1
JZ cont_62
SUBI 1
JZ cont_63
SUBI 1
JZ cont_64
SUBI 1
JZ cont_65
SUBI 1
JZ cont_66
SUBI 1
JZ cont_67
HALT
ret_spi_4:
LD 237
ANDI 15
JZ cont_68
SUBI 1
JZ cont_69
SUBI 1
JZ cont_70
SUBI 1
JZ cont_71
SUBI 1
JZ cont_73
SUBI 1
JZ cont_74
SUBI 1
JZ cont_75
SUBI 1
JZ cont_76
SUBI 1
JZ cont_77
SUBI 1
JZ cont_78
SUBI 1
JZ cont_79
SUBI 1
JZ cont_80
SUBI 1
JZ cont_81
SUBI 1
JZ cont_82
SUBI 1
JZ cont_83
SUBI 1
JZ cont_84
HALT
ret_spi_5:
LD 237
ANDI 15
JZ cont_85
SUBI 1
JZ cont_86
SUBI 1
JZ cont_87
SUBI 1
JZ cont_88
SUBI 1
JZ cont_89
SUBI 1
JZ cont_90
SUBI 1
JZ cont_91
SUBI 1
JZ cont_92
SUBI 1
JZ cont_93
SUBI 1
JZ cont_94
SUBI 1
JZ cont_95
SUBI 1
JZ cont_96
SUBI 1
JZ cont_97
SUBI 1
JZ cont_98
SUBI 1
JZ cont_99
SUBI 1
JZ cont_100
HALT
ret_spi_6:
LD 237
ANDI 15
JZ cont_101
SUBI 1
JZ cont_102
SUBI 1
JZ cont_127
SUBI 1
JZ cont_128
SUBI 1
JZ cont_129
SUBI 1
JZ cont_131
SUBI 1
JZ cont_137
SUBI 1
JZ cont_140
SUBI 1
JZ cont_141
SUBI 1
JZ cont_142
SUBI 1
JZ cont_143
SUBI 1
JZ cont_144
SUBI 1
JZ cont_145
SUBI 1
JZ cont_146
SUBI 1
JZ cont_147
SUBI 1
JZ cont_148
HALT
ret_spi_7:
LD 237
ANDI 15
JZ cont_149
SUBI 1
JZ cont_150
SUBI 1
JZ cont_151
SUBI 1
JZ cont_152
SUBI 1
JZ cont_153
SUBI 1
JZ cont_154
SUBI 1
JZ cont_155
SUBI 1
JZ cont_156
SUBI 1
JZ cont_157
SUBI 1
JZ cont_158
SUBI 1
JZ cont_159
SUBI 1
JZ cont_160
SUBI 1
JZ cont_161
SUBI 1
JZ cont_162
SUBI 1
JZ cont_163
SUBI 1
JZ cont_164
HALT
ret_spi_8:
LD 237
ANDI 15
JZ cont_165
SUBI 1
JZ cont_166
SUBI 1
JZ cont_167
SUBI 1
JZ cont_168
SUBI 1
JZ cont_169
SUBI 1
JZ cont_170
SUBI 1
JZ cont_171
SUBI 1
JZ cont_172
SUBI 1
JZ cont_173
SUBI 1
JZ cont_174
SUBI 1
JZ cont_175
SUBI 1
JZ cont_176
SUBI 1
JZ cont_177
SUBI 1
JZ cont_178
SUBI 1
JZ cont_179
SUBI 1
JZ cont_180
HALT
ret_spi_9:
LD 237
ANDI 15
JZ cont_181
SUBI 1
JZ cont_182
SUBI 1
JZ cont_183
SUBI 1
JZ cont_184
SUBI 1
JZ cont_185
SUBI 1
JZ cont_186
SUBI 1
JZ cont_187
SUBI 1
JZ cont_188
HALT
spi_low:
LDI 1
ST HALF
LD LO
ST SHIFT
JMP spi_half
address:
LDI 11
ST HI
LD Y
ANDI 7
ST LO
LDI 0
ST DC
LDI 2
ST 237
LDI 6
ST 238
JMP spi
cont_127:
LDI 0
ST HI
LD X
ANDI 1
SHL
SHL
SHL
ST LO
LDI 3
ST 237
LDI 6
ST 238
JMP spi
cont_128:
LDI 1
ST HI
LD X
SHR
ST LO
LDI 4
ST 237
LDI 6
ST 238
JMP spi
cont_129:
ret_address_0:
LD 240
ANDI 15
JZ cont_28
SUBI 1
JZ cont_47
SUBI 1
JZ cont_72
SUBI 1
JZ cont_113
SUBI 1
JZ cont_116
SUBI 1
JZ cont_130
SUBI 1
JZ cont_136
HALT
cell:
LDI 5
ST 240
JMP address
cont_130:
LDI 8
ST REP
cell_loop:
LD PIX
SUBI 6
JZ cell_plus
LD PIX
ST HI
ST LO
JMP cell_byte
cell_plus:
LDI 0
ST HI
ST LO
LD REP
SUBI 6
JZ plus_vertical
ADDI 1
JZ plus_horizontal
ADDI 1
JZ plus_horizontal
ADDI 1
JZ plus_vertical
JMP cell_byte
plus_vertical:
LDI 1
ST HI
LDI 8
ST LO
JMP cell_byte
plus_horizontal:
LDI 7
ST HI
LDI 14
ST LO
cell_byte:
LDI 4
ST DC
LDI 5
ST 237
LDI 6
ST 238
JMP spi
cont_131:
LD REP
SUBI 1
ST REP
JZ cell_done
JMP cell_loop
cell_done:
LDI 0
ST 245
JMP poll_keys
cont_132:
ret_cell_0:
LD 241
ANDI 15
JZ cont_103
SUBI 1
JZ cont_104
SUBI 1
JZ cont_107
SUBI 1
JZ cont_112
SUBI 1
JZ cont_119
SUBI 1
JZ cont_120
SUBI 1
JZ cont_121
SUBI 1
JZ cont_122
SUBI 1
JZ cont_123
SUBI 1
JZ cont_124
SUBI 1
JZ cont_133
SUBI 1
JZ cont_134
SUBI 1
JZ cont_135
HALT
paddle:
LD Y
ST ROW
LDI 10
ST 241
JMP cell
cont_133:
LD ROW
ADDI 1
ST Y
LDI 11
ST 241
JMP cell
cont_134:
LD ROW
ADDI 2
ST Y
LDI 12
ST 241
JMP cell
cont_135:
ret_paddle_0:
LD 243
ANDI 15
JZ cont_108
SUBI 1
JZ cont_109
SUBI 1
JZ cont_110
SUBI 1
JZ cont_111
HALT
clear_screen:
LDI 0
ST PAGE
clear_page:
LD PAGE
ST Y
LDI 0
ST X
LDI 6
ST 240
JMP address
cont_136:
LDI 0
ST COL
clear_cell:
LDI 8
ST REP
clear_byte:
LDI 0
ST HI
LDI 0
ST LO
LDI 4
ST DC
LDI 6
ST 237
LDI 6
ST 238
JMP spi
cont_137:
LD REP
SUBI 1
ST REP
JZ clear_next
JMP clear_byte
clear_next:
LDI 1
ST 245
JMP poll_keys
cont_138:
LD COL
ADDI 1
ST COL
JZ clear_next_page
JMP clear_cell
clear_next_page:
LD PAGE
ADDI 1
ST PAGE
SUBI 8
JZ clear_done
JMP clear_page
clear_done:
ret_clear_screen_0:
LD 239
ANDI 15
JZ cont_25
SUBI 1
JZ cont_27
SUBI 1
JZ cont_106
SUBI 1
JZ cont_126
HALT
poll_wait:
LDI 0
ST DLY0
LDI 0
ST DLY1
wait_inner:
LD DLY0
ADDI 1
ST DLY0
JZ wait_hi
JMP wait_inner
wait_hi:
LD DLY1
ADDI 1
ST DLY1
JZ wait_done
JMP wait_inner
wait_done:
LDI 2
ST 245
JMP poll_keys
cont_139:
LD STABLE0
ANDI 3
SUBI 3
JZ combo_count
LDI 0
ST COMBO0
ST COMBO1
ST COMBO2
JMP poll_done
combo_count:
LD COMBO2
SUBI 2
JC poll_done
LD COMBO0
ADDI 1
ST COMBO0
LD COMBO1
ADCI 0
ST COMBO1
LD COMBO2
ADCI 0
ST COMBO2
poll_done:
ret_poll_wait_0:
LD 242
ANDI 15
JZ cont_105
SUBI 1
JZ cont_125
HALT
hex_digit:
LDI 0
ST HI
LDI 4
ST DC
LD PIX
SUBI 0
JZ hex_0
LD PIX
SUBI 1
JZ hex_1
LD PIX
SUBI 2
JZ hex_2
LD PIX
SUBI 3
JZ hex_3
LD PIX
SUBI 4
JZ hex_4
LD PIX
SUBI 5
JZ hex_5
LD PIX
SUBI 6
JZ hex_6
LD PIX
SUBI 7
JZ hex_7
LD PIX
SUBI 8
JZ hex_8
LD PIX
SUBI 9
JZ hex_9
LD PIX
SUBI 10
JZ hex_10
LD PIX
SUBI 11
JZ hex_11
LD PIX
SUBI 12
JZ hex_12
LD PIX
SUBI 13
JZ hex_13
LD PIX
SUBI 14
JZ hex_14
LD PIX
SUBI 15
JZ hex_15
HALT
hex_0:
LDI 15
ST LO
LDI 7
ST 237
LDI 6
ST 238
JMP spi
cont_140:
LDI 9
ST LO
LDI 8
ST 237
LDI 6
ST 238
JMP spi
cont_141:
LDI 15
ST LO
LDI 9
ST 237
LDI 6
ST 238
JMP spi
cont_142:
JMP hex_return
hex_1:
LDI 0
ST LO
LDI 10
ST 237
LDI 6
ST 238
JMP spi
cont_143:
LDI 15
ST LO
LDI 11
ST 237
LDI 6
ST 238
JMP spi
cont_144:
LDI 0
ST LO
LDI 12
ST 237
LDI 6
ST 238
JMP spi
cont_145:
JMP hex_return
hex_2:
LDI 13
ST LO
LDI 13
ST 237
LDI 6
ST 238
JMP spi
cont_146:
LDI 11
ST LO
LDI 14
ST 237
LDI 6
ST 238
JMP spi
cont_147:
LDI 0
ST LO
LDI 15
ST 237
LDI 6
ST 238
JMP spi
cont_148:
JMP hex_return
hex_3:
LDI 9
ST LO
LDI 0
ST 237
LDI 7
ST 238
JMP spi
cont_149:
LDI 11
ST LO
LDI 1
ST 237
LDI 7
ST 238
JMP spi
cont_150:
LDI 15
ST LO
LDI 2
ST 237
LDI 7
ST 238
JMP spi
cont_151:
JMP hex_return
hex_4:
LDI 7
ST LO
LDI 3
ST 237
LDI 7
ST 238
JMP spi
cont_152:
LDI 4
ST LO
LDI 4
ST 237
LDI 7
ST 238
JMP spi
cont_153:
LDI 15
ST LO
LDI 5
ST 237
LDI 7
ST 238
JMP spi
cont_154:
JMP hex_return
hex_5:
LDI 11
ST LO
LDI 6
ST 237
LDI 7
ST 238
JMP spi
cont_155:
LDI 9
ST LO
LDI 7
ST 237
LDI 7
ST 238
JMP spi
cont_156:
LDI 13
ST LO
LDI 8
ST 237
LDI 7
ST 238
JMP spi
cont_157:
JMP hex_return
hex_6:
LDI 15
ST LO
LDI 9
ST 237
LDI 7
ST 238
JMP spi
cont_158:
LDI 9
ST LO
LDI 10
ST 237
LDI 7
ST 238
JMP spi
cont_159:
LDI 13
ST LO
LDI 11
ST 237
LDI 7
ST 238
JMP spi
cont_160:
JMP hex_return
hex_7:
LDI 1
ST LO
LDI 12
ST 237
LDI 7
ST 238
JMP spi
cont_161:
LDI 1
ST LO
LDI 13
ST 237
LDI 7
ST 238
JMP spi
cont_162:
LDI 15
ST LO
LDI 14
ST 237
LDI 7
ST 238
JMP spi
cont_163:
JMP hex_return
hex_8:
LDI 15
ST LO
LDI 15
ST 237
LDI 7
ST 238
JMP spi
cont_164:
LDI 11
ST LO
LDI 0
ST 237
LDI 8
ST 238
JMP spi
cont_165:
LDI 15
ST LO
LDI 1
ST 237
LDI 8
ST 238
JMP spi
cont_166:
JMP hex_return
hex_9:
LDI 7
ST LO
LDI 2
ST 237
LDI 8
ST 238
JMP spi
cont_167:
LDI 5
ST LO
LDI 3
ST 237
LDI 8
ST 238
JMP spi
cont_168:
LDI 15
ST LO
LDI 4
ST 237
LDI 8
ST 238
JMP spi
cont_169:
JMP hex_return
hex_10:
LDI 15
ST LO
LDI 5
ST 237
LDI 8
ST 238
JMP spi
cont_170:
LDI 5
ST LO
LDI 6
ST 237
LDI 8
ST 238
JMP spi
cont_171:
LDI 15
ST LO
LDI 7
ST 237
LDI 8
ST 238
JMP spi
cont_172:
JMP hex_return
hex_11:
LDI 15
ST LO
LDI 8
ST 237
LDI 8
ST 238
JMP spi
cont_173:
LDI 10
ST LO
LDI 9
ST 237
LDI 8
ST 238
JMP spi
cont_174:
LDI 14
ST LO
LDI 10
ST 237
LDI 8
ST 238
JMP spi
cont_175:
JMP hex_return
hex_12:
LDI 15
ST LO
LDI 11
ST 237
LDI 8
ST 238
JMP spi
cont_176:
LDI 9
ST LO
LDI 12
ST 237
LDI 8
ST 238
JMP spi
cont_177:
LDI 9
ST LO
LDI 13
ST 237
LDI 8
ST 238
JMP spi
cont_178:
JMP hex_return
hex_13:
LDI 15
ST LO
LDI 14
ST 237
LDI 8
ST 238
JMP spi
cont_179:
LDI 9
ST LO
LDI 15
ST 237
LDI 8
ST 238
JMP spi
cont_180:
LDI 6
ST LO
LDI 0
ST 237
LDI 9
ST 238
JMP spi
cont_181:
JMP hex_return
hex_14:
LDI 15
ST LO
LDI 1
ST 237
LDI 9
ST 238
JMP spi
cont_182:
LDI 11
ST LO
LDI 2
ST 237
LDI 9
ST 238
JMP spi
cont_183:
LDI 9
ST LO
LDI 3
ST 237
LDI 9
ST 238
JMP spi
cont_184:
JMP hex_return
hex_15:
LDI 15
ST LO
LDI 4
ST 237
LDI 9
ST 238
JMP spi
cont_185:
LDI 3
ST LO
LDI 5
ST 237
LDI 9
ST 238
JMP spi
cont_186:
LDI 1
ST LO
LDI 6
ST 237
LDI 9
ST 238
JMP spi
cont_187:
JMP hex_return
hex_return:
LDI 0
ST LO
LDI 7
ST 237
LDI 9
ST 238
JMP spi
cont_188:
ret_hex_digit_0:
LD 244
ANDI 15
JZ cont_114
SUBI 1
JZ cont_115
SUBI 1
JZ cont_117
SUBI 1
JZ cont_118
HALT
poll_keys:
LD STABLE0
ST PREV0
LD STABLE1
ST PREV1
IN0
ST TEMP
CMP CAND0
JZ poll_bank1
ST CAND0
LDI 0
ST COUNT
poll_bank1:
IN1
ST TEMP
CMP CAND1
JZ poll_equal
ST CAND1
LDI 0
ST COUNT
poll_equal:
LD COUNT
SUBI 3
JC poll_edges
LD COUNT
ADDI 1
ST COUNT
SUBI 3
JZ accept_keys
JMP poll_edges
accept_keys:
LD CAND0
ST STABLE0
LD CAND1
ST STABLE1
poll_edges:
LD STABLE0
NOT
AND PREV0
ST RELEASE0
LD STABLE1
NOT
AND PREV1
ST RELEASE1
LD PREV0
NOT
AND STABLE0
OR EDGE0
ST EDGE0
LD PREV1
NOT
AND STABLE1
OR EDGE1
ST EDGE1
LD STABLE0
CMP PREV0
JZ keys_done
LD STABLE0
ANDI 15
JZ keys_done
ST PENDING
keys_done:
ret_poll_keys_0:
LD 245
ANDI 15
JZ cont_132
SUBI 1
JZ cont_138
SUBI 1
JZ cont_139
HALT
.equ P_BALL_X,       0x00
.equ P_BALL_Y,       0x01
.equ P_VX,           0x02
.equ P_VY,           0x03
.equ P_PADDLE_L,     0x04
.equ P_PADDLE_R,     0x05
.equ P_SCORE_L_LO,   0x06
.equ P_SCORE_L_HI,   0x07
.equ P_SCORE_R_LO,   0x08
.equ P_SCORE_R_HI,   0x09
.equ P_EVENT,        0x0A
.equ P_KEYS0,        0x0B
.equ P_KEYS1,        0x0C
.equ P_CTRL,         0x20
.equ P_RETURN_ID,    0x3F

P_boot:
LDI 8
ST P_BALL_X
LDI 4
ST P_BALL_Y
LDI 0
ST P_VX
ST P_VY
ST P_SCORE_L_LO
ST P_SCORE_L_HI
ST P_SCORE_R_LO
ST P_SCORE_R_HI
ST P_EVENT
ST P_KEYS0
ST P_KEYS1
ST P_CTRL
ST P_RETURN_ID
LDI 2
ST P_PADDLE_L
ST P_PADDLE_R

P_tick:
LD PLAYKEYS
ST P_KEYS0
LD STABLE1
ST P_KEYS1
LDI 0
ST P_EVENT


LD P_KEYS0
ANDI 3
ST P_CTRL
ARH 0
ARL 4
LDI 1
ST P_RETURN_ID
JMP P_update_paddle
P_after_left_paddle:

LD P_KEYS0
SHR
SHR
ANDI 3
ST P_CTRL
ARH 0
ARL 5
LDI 2
ST P_RETURN_ID
JMP P_update_paddle
P_after_right_paddle:


LD P_VY
JZ P_move_down
P_move_up:
LD P_BALL_Y
JZ P_bounce_top
SUBI 1
ST P_BALL_Y
JMP P_vertical_done
P_bounce_top:
LDI 1
ST P_BALL_Y
LDI 0
ST P_VY
LDI 1
ST P_EVENT
JMP P_vertical_done
P_move_down:
LD P_BALL_Y
SUBI 7
JZ P_bounce_bottom
LD P_BALL_Y
ADDI 1
ST P_BALL_Y
JMP P_vertical_done
P_bounce_bottom:
LDI 6
ST P_BALL_Y
LDI 1
ST P_VY
LDI 1
ST P_EVENT
P_vertical_done:


LD P_VX
JZ P_move_right
P_move_left:
LD P_BALL_X
SUBI 1
JZ P_left_contact
ST P_BALL_X
JMP P_tick_done
P_left_contact:


LD P_BALL_Y
SUB P_PADDLE_L
JC P_left_contact_lower_ok
JMP P_right_scores
P_left_contact_lower_ok:
SUBI 3
JC P_right_scores

LDI 0
ST P_VX
LD P_EVENT
ADDI 2
ST P_EVENT
JMP P_tick_done
P_move_right:
LD P_BALL_X
SUBI 14
JZ P_right_contact
LD P_BALL_X
ADDI 1
ST P_BALL_X
JMP P_tick_done
P_right_contact:
LD P_BALL_Y
SUB P_PADDLE_R
JC P_right_contact_lower_ok
JMP P_left_scores
P_right_contact_lower_ok:
SUBI 3
JC P_left_scores

LDI 1
ST P_VX
LD P_EVENT
ADDI 2
ST P_EVENT
JMP P_tick_done

P_right_scores:

LD P_SCORE_R_LO
ADDI 1
ST P_SCORE_R_LO
LD P_SCORE_R_HI
ADCI 0
ST P_SCORE_R_HI
LDI 8
ST P_BALL_X
LDI 4
ST P_BALL_Y
LDI 1
ST P_VX
LDI 0
ST P_VY
LDI 8
ST P_EVENT
JMP P_tick_done
P_left_scores:
LD P_SCORE_L_LO
ADDI 1
ST P_SCORE_L_LO
LD P_SCORE_L_HI
ADCI 0
ST P_SCORE_L_HI
LDI 8
ST P_BALL_X
LDI 4
ST P_BALL_Y
LDI 0
ST P_VX
ST P_VY
LDI 4
ST P_EVENT
JMP P_tick_done

P_tick_done:
JMP game_after_tick

P_update_paddle:



LD P_CTRL
SUBI 1
JZ P_paddle_up
LD P_CTRL
SUBI 2
JZ P_paddle_down
JMP P_return_dispatch
P_paddle_up:
LD [AR]
JZ P_return_dispatch
SUBI 1
ST [AR]
JMP P_return_dispatch
P_paddle_down:
LD [AR]
SUBI 5
JC P_return_dispatch
LD [AR]
ADDI 1
ST [AR]
P_return_dispatch:
LD P_RETURN_ID
SUBI 1
JZ P_after_left_paddle
LD P_RETURN_ID
SUBI 2
JZ P_after_right_paddle
P_bad_return_id:

HALT
.equ S_HEAD_LO, 0x00
.equ S_HEAD_HI, 0x01
.equ S_TAIL_LO, 0x02
.equ S_TAIL_HI, 0x03
.equ S_LEN_LO, 0x04
.equ S_LEN_HI, 0x05
.equ S_DIR, 0x06
.equ S_FOOD_X, 0x07
.equ S_FOOD_Y, 0x08
.equ S_SCORE_LO, 0x09
.equ S_SCORE_HI, 0x0A
.equ S_STATUS, 0x0B
.equ S_KEYS0, 0x0C
.equ S_KEYS1, 0x0D
.equ S_EVENT, 0x0E
.equ S_PROBES_LO, 0x0F
.equ S_PROBES_HI, 0x10
.equ S_NEXT_X, 0x11
.equ S_NEXT_Y, 0x12
.equ S_OLD_TAIL_X, 0x13
.equ S_OLD_TAIL_Y, 0x14
.equ S_GROW, 0x15
.equ S_TEMP, 0x16
.equ S_ADDR_LO, 0x17
.equ S_ADDR_HI, 0x18
.equ S_BIT_LO, 0x19
.equ S_BIT_HI, 0x1A
.equ S_MASK, 0x1B
.equ S_OCCUPIED, 0x1C
.equ S_LOOK_X, 0x1D
.equ S_LOOK_Y, 0x1E
.equ S_INDEX_LO, 0x1F
.equ S_INDEX_HI, 0x20
.equ S_TEMP2, 0x21
.equ S_FOOD_SEQ_LO, 0x22
.equ S_FOOD_SEQ_HI, 0x23
.equ S_RETURN_ID, 0x3F

S_boot:
ARH 0
ARL 0
S_clear:
LDI 0
ST [AR]
INCAR
MOVA ARH
SUBI 2
JZ S_clear_low
SUBI 12
JZ S_boot_init
JMP S_clear
S_clear_low:
MOVA ARL
SUBI 4
JZ S_skip_system
JMP S_clear
S_skip_system:
ARH 4
ARL 0
JMP S_clear
S_boot_init:
LDI 2
ST S_HEAD_LO
ST 0x40
LDI 3
ST S_LEN_LO
ST S_FOOD_Y
ST 0x41
ST 0x42
ST 0x43
ST 0x45
LDI 4
ST 0x44
LDI 10
ST S_FOOD_X

LDI 12
ST 0xCC
LDI 1
ST 0xCD
LDI 4
ST S_EVENT
JMP S_tick_done

S_tick:
LD PLAYKEYS
ST S_KEYS0
LD STABLE1
ST S_KEYS1
ANDI 2
JZ S_tick_no_restart
JMP S_boot
S_tick_no_restart:
LDI 0
ST S_EVENT
ST S_PROBES_LO
ST S_PROBES_HI
LD S_STATUS
JZ S_tick_running
JMP S_tick_done

S_tick_running:


LD S_KEYS0
ANDI 1
JZ S_key_down
LD S_DIR
SUBI 1
JZ S_direction_done
LDI 3
ST S_DIR
JMP S_direction_done
S_key_down:
LD S_KEYS0
ANDI 2
JZ S_key_left
LD S_DIR
SUBI 3
JZ S_direction_done
LDI 1
ST S_DIR
JMP S_direction_done
S_key_left:
LD S_KEYS0
ANDI 4
JZ S_key_right
LD S_DIR
JZ S_direction_done
LDI 2
ST S_DIR
JMP S_direction_done
S_key_right:
LD S_KEYS0
ANDI 8
JZ S_direction_done
LD S_DIR
SUBI 2
JZ S_direction_done
LDI 0
ST S_DIR

S_direction_done:

LD S_HEAD_LO
ST S_INDEX_LO
LD S_HEAD_HI
ST S_INDEX_HI
LD S_INDEX_LO
SHL
ST S_ADDR_LO
LD S_INDEX_HI
ADC S_INDEX_HI
ADDI 4
ST S_ADDR_HI
LD S_ADDR_LO
MOVARL A
LD S_ADDR_HI
MOVARH A
LD [AR]
ST S_NEXT_X
INCAR
LD [AR]
ST S_NEXT_Y


LD S_TAIL_LO
ST S_INDEX_LO
LD S_TAIL_HI
ST S_INDEX_HI
LD S_INDEX_LO
SHL
ST S_ADDR_LO
LD S_INDEX_HI
ADC S_INDEX_HI
ADDI 4
ST S_ADDR_HI
LD S_ADDR_LO
MOVARL A
LD S_ADDR_HI
MOVARH A
LD [AR]
ST S_OLD_TAIL_X
INCAR
LD [AR]
ST S_OLD_TAIL_Y

LD S_DIR
JZ S_move_right
SUBI 1
JZ S_move_down
SUBI 1
JZ S_move_left
JMP S_move_up
S_move_right:
LD S_NEXT_X
SUBI 15
JZ S_die
LD S_NEXT_X
ADDI 1
ST S_NEXT_X
JMP S_moved
S_move_down:
LD S_NEXT_Y
SUBI 7
JZ S_die
LD S_NEXT_Y
ADDI 1
ST S_NEXT_Y
JMP S_moved
S_move_left:
LD S_NEXT_X
JZ S_die
SUBI 1
ST S_NEXT_X
JMP S_moved
S_move_up:
LD S_NEXT_Y
JZ S_die
SUBI 1
ST S_NEXT_Y

S_moved:
LDI 0
ST S_GROW
LD S_NEXT_X
CMP S_FOOD_X
JZ S_compare_food_y
JMP S_find_collision
S_compare_food_y:
LD S_NEXT_Y
CMP S_FOOD_Y
JZ S_mark_grow
JMP S_find_collision
S_mark_grow:
LDI 1
ST S_GROW
S_find_collision:
LD S_NEXT_X
ST S_LOOK_X
LD S_NEXT_Y
ST S_LOOK_Y
LDI 1
ST S_RETURN_ID
JMP S_occupancy_lookup
S_after_collision_lookup:
LD S_OCCUPIED
JZ S_collision_ok
LD S_GROW
JZ S_compare_old_tail
JMP S_die
S_compare_old_tail:
LD S_NEXT_X
CMP S_OLD_TAIL_X
JZ S_compare_old_tail_y
JMP S_die
S_compare_old_tail_y:
LD S_NEXT_Y
CMP S_OLD_TAIL_Y
JZ S_collision_ok
JMP S_die

S_collision_ok:
LD S_GROW
JZ S_remove_tail

LD S_LEN_HI
SUBI 4
JZ S_win
JMP S_append_head
S_remove_tail:
LD S_OLD_TAIL_X
ST S_LOOK_X
LD S_OLD_TAIL_Y
ST S_LOOK_Y
LDI 2
ST S_RETURN_ID
JMP S_occupancy_lookup
S_after_tail_lookup:

LD S_MASK
NOT
ST S_TEMP2
LD [AR]
AND S_TEMP2
ST [AR]
LD S_TAIL_LO
ADDI 1
ST S_TAIL_LO
LD S_TAIL_HI
ADCI 0
ANDI 3
ST S_TAIL_HI

S_append_head:
LD S_HEAD_LO
ADDI 1
ST S_HEAD_LO
LD S_HEAD_HI
ADCI 0
ANDI 3
ST S_HEAD_HI
LD S_HEAD_LO
ST S_INDEX_LO
LD S_HEAD_HI
ST S_INDEX_HI
LD S_INDEX_LO
SHL
ST S_ADDR_LO
LD S_INDEX_HI
ADC S_INDEX_HI
ADDI 4
ST S_ADDR_HI
LD S_ADDR_LO
MOVARL A
LD S_ADDR_HI
MOVARH A
LD S_NEXT_X
ST [AR]
INCAR
LD S_NEXT_Y
ST [AR]
LD S_NEXT_X
ST S_LOOK_X
LD S_NEXT_Y
ST S_LOOK_Y
LDI 3
ST S_RETURN_ID
JMP S_occupancy_lookup
S_after_head_lookup:
LD [AR]
OR S_MASK
ST [AR]
LD S_GROW
JZ S_tick_done
LD S_LEN_LO
ADDI 1
ST S_LEN_LO
LD S_LEN_HI
ADCI 0
ST S_LEN_HI
LD S_SCORE_LO
ADDI 1
ST S_SCORE_LO
LD S_SCORE_HI
ADCI 0
ST S_SCORE_HI
LD S_LEN_HI
SUBI 4
JZ S_win
LDI 1
ST S_EVENT

S_food_next_candidate:
LD S_FOOD_SEQ_LO
ADDI 1
ST S_FOOD_SEQ_LO
LD S_FOOD_SEQ_HI
ADCI 0
ANDI 7
ST S_FOOD_SEQ_HI
JMP S_food_table_dispatch
S_food_table_return:
LD S_PROBES_LO
ADDI 1
ST S_PROBES_LO
LD S_PROBES_HI
ADCI 0
ST S_PROBES_HI
LDI 4
ST S_RETURN_ID
JMP S_occupancy_lookup
S_after_food_lookup:
LD S_OCCUPIED
JZ S_food_found
LD S_PROBES_HI
SUBI 4
JZ S_food_check_limit
JMP S_food_next_candidate
S_food_check_limit:
LD S_PROBES_LO
SUBI 1
JZ S_bitmap_fault
JMP S_food_next_candidate
S_food_found:
LD S_LOOK_X
ST S_FOOD_X
LD S_LOOK_Y
ST S_FOOD_Y
JMP S_tick_done

S_die:
LDI 1
ST S_STATUS
LDI 2
ST S_EVENT
JMP S_tick_done
S_win:
LDI 2
ST S_STATUS
LDI 3
ST S_EVENT
JMP S_tick_done
S_bitmap_fault:

LDI 3
ST S_STATUS
LDI 5
ST S_EVENT
JMP S_tick_done

S_tick_done:
JMP game_after_tick



S_occupancy_lookup:

LD S_LOOK_Y
SHL
SHL
ST S_BIT_LO
LDI 0
ADCI 0
ADDI 12
ST S_BIT_HI
LD S_LOOK_X
SHR
SHR
ADD S_BIT_LO
ST S_BIT_LO
LD S_LOOK_X
ANDI 3
JZ S_mask_1
SUBI 1
JZ S_mask_2
SUBI 1
JZ S_mask_4
LDI 8
JMP S_mask_ready
S_mask_1:
LDI 1
JMP S_mask_ready
S_mask_2:
LDI 2
JMP S_mask_ready
S_mask_4:
LDI 4
S_mask_ready:
ST S_MASK
LD S_BIT_LO
MOVARL A
LD S_BIT_HI
MOVARH A
LD [AR]
AND S_MASK
JZ S_occupancy_zero
LDI 1
ST S_OCCUPIED
JMP S_software_return
S_occupancy_zero:
LDI 0
ST S_OCCUPIED
S_software_return:
LD S_RETURN_ID
SUBI 1
JZ S_after_collision_lookup
SUBI 1
JZ S_after_tail_lookup
SUBI 1
JZ S_after_head_lookup
SUBI 1
JZ S_after_food_lookup

HALT


S_food_table_dispatch:
LD S_FOOD_SEQ_HI
SUBI 0
JZ S_food_table_hi_0
SUBI 1
JZ S_food_table_hi_1
SUBI 1
JZ S_food_table_hi_2
SUBI 1
JZ S_food_table_hi_3
SUBI 1
JZ S_food_table_hi_4
SUBI 1
JZ S_food_table_hi_5
SUBI 1
JZ S_food_table_hi_6
SUBI 1
JZ S_food_table_hi_7
JMP S_bitmap_fault
S_food_table_hi_0:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_0
SUBI 1
JZ S_food_entry_1
SUBI 1
JZ S_food_entry_2
SUBI 1
JZ S_food_entry_3
SUBI 1
JZ S_food_entry_4
SUBI 1
JZ S_food_entry_5
SUBI 1
JZ S_food_entry_6
SUBI 1
JZ S_food_entry_7
SUBI 1
JZ S_food_entry_8
SUBI 1
JZ S_food_entry_9
SUBI 1
JZ S_food_entry_10
SUBI 1
JZ S_food_entry_11
SUBI 1
JZ S_food_entry_12
SUBI 1
JZ S_food_entry_13
SUBI 1
JZ S_food_entry_14
SUBI 1
JZ S_food_entry_15
JMP S_bitmap_fault
S_food_table_hi_1:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_16
SUBI 1
JZ S_food_entry_17
SUBI 1
JZ S_food_entry_18
SUBI 1
JZ S_food_entry_19
SUBI 1
JZ S_food_entry_20
SUBI 1
JZ S_food_entry_21
SUBI 1
JZ S_food_entry_22
SUBI 1
JZ S_food_entry_23
SUBI 1
JZ S_food_entry_24
SUBI 1
JZ S_food_entry_25
SUBI 1
JZ S_food_entry_26
SUBI 1
JZ S_food_entry_27
SUBI 1
JZ S_food_entry_28
SUBI 1
JZ S_food_entry_29
SUBI 1
JZ S_food_entry_30
SUBI 1
JZ S_food_entry_31
JMP S_bitmap_fault
S_food_table_hi_2:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_32
SUBI 1
JZ S_food_entry_33
SUBI 1
JZ S_food_entry_34
SUBI 1
JZ S_food_entry_35
SUBI 1
JZ S_food_entry_36
SUBI 1
JZ S_food_entry_37
SUBI 1
JZ S_food_entry_38
SUBI 1
JZ S_food_entry_39
SUBI 1
JZ S_food_entry_40
SUBI 1
JZ S_food_entry_41
SUBI 1
JZ S_food_entry_42
SUBI 1
JZ S_food_entry_43
SUBI 1
JZ S_food_entry_44
SUBI 1
JZ S_food_entry_45
SUBI 1
JZ S_food_entry_46
SUBI 1
JZ S_food_entry_47
JMP S_bitmap_fault
S_food_table_hi_3:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_48
SUBI 1
JZ S_food_entry_49
SUBI 1
JZ S_food_entry_50
SUBI 1
JZ S_food_entry_51
SUBI 1
JZ S_food_entry_52
SUBI 1
JZ S_food_entry_53
SUBI 1
JZ S_food_entry_54
SUBI 1
JZ S_food_entry_55
SUBI 1
JZ S_food_entry_56
SUBI 1
JZ S_food_entry_57
SUBI 1
JZ S_food_entry_58
SUBI 1
JZ S_food_entry_59
SUBI 1
JZ S_food_entry_60
SUBI 1
JZ S_food_entry_61
SUBI 1
JZ S_food_entry_62
SUBI 1
JZ S_food_entry_63
JMP S_bitmap_fault
S_food_table_hi_4:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_64
SUBI 1
JZ S_food_entry_65
SUBI 1
JZ S_food_entry_66
SUBI 1
JZ S_food_entry_67
SUBI 1
JZ S_food_entry_68
SUBI 1
JZ S_food_entry_69
SUBI 1
JZ S_food_entry_70
SUBI 1
JZ S_food_entry_71
SUBI 1
JZ S_food_entry_72
SUBI 1
JZ S_food_entry_73
SUBI 1
JZ S_food_entry_74
SUBI 1
JZ S_food_entry_75
SUBI 1
JZ S_food_entry_76
SUBI 1
JZ S_food_entry_77
SUBI 1
JZ S_food_entry_78
SUBI 1
JZ S_food_entry_79
JMP S_bitmap_fault
S_food_table_hi_5:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_80
SUBI 1
JZ S_food_entry_81
SUBI 1
JZ S_food_entry_82
SUBI 1
JZ S_food_entry_83
SUBI 1
JZ S_food_entry_84
SUBI 1
JZ S_food_entry_85
SUBI 1
JZ S_food_entry_86
SUBI 1
JZ S_food_entry_87
SUBI 1
JZ S_food_entry_88
SUBI 1
JZ S_food_entry_89
SUBI 1
JZ S_food_entry_90
SUBI 1
JZ S_food_entry_91
SUBI 1
JZ S_food_entry_92
SUBI 1
JZ S_food_entry_93
SUBI 1
JZ S_food_entry_94
SUBI 1
JZ S_food_entry_95
JMP S_bitmap_fault
S_food_table_hi_6:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_96
SUBI 1
JZ S_food_entry_97
SUBI 1
JZ S_food_entry_98
SUBI 1
JZ S_food_entry_99
SUBI 1
JZ S_food_entry_100
SUBI 1
JZ S_food_entry_101
SUBI 1
JZ S_food_entry_102
SUBI 1
JZ S_food_entry_103
SUBI 1
JZ S_food_entry_104
SUBI 1
JZ S_food_entry_105
SUBI 1
JZ S_food_entry_106
SUBI 1
JZ S_food_entry_107
SUBI 1
JZ S_food_entry_108
SUBI 1
JZ S_food_entry_109
SUBI 1
JZ S_food_entry_110
SUBI 1
JZ S_food_entry_111
JMP S_bitmap_fault
S_food_table_hi_7:
LD S_FOOD_SEQ_LO
SUBI 0
JZ S_food_entry_112
SUBI 1
JZ S_food_entry_113
SUBI 1
JZ S_food_entry_114
SUBI 1
JZ S_food_entry_115
SUBI 1
JZ S_food_entry_116
SUBI 1
JZ S_food_entry_117
SUBI 1
JZ S_food_entry_118
SUBI 1
JZ S_food_entry_119
SUBI 1
JZ S_food_entry_120
SUBI 1
JZ S_food_entry_121
SUBI 1
JZ S_food_entry_122
SUBI 1
JZ S_food_entry_123
SUBI 1
JZ S_food_entry_124
SUBI 1
JZ S_food_entry_125
SUBI 1
JZ S_food_entry_126
SUBI 1
JZ S_food_entry_127
JMP S_bitmap_fault
S_food_entry_0:
LDI 10
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_1:
LDI 2
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_2:
LDI 13
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_3:
LDI 5
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_4:
LDI 1
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_5:
LDI 14
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_6:
LDI 7
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_7:
LDI 11
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_8:
LDI 3
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_9:
LDI 15
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_10:
LDI 0
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_11:
LDI 8
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_12:
LDI 11
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_13:
LDI 12
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_14:
LDI 14
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_15:
LDI 8
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_16:
LDI 6
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_17:
LDI 10
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_18:
LDI 3
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_19:
LDI 4
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_20:
LDI 13
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_21:
LDI 13
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_22:
LDI 0
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_23:
LDI 6
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_24:
LDI 13
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_25:
LDI 1
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_26:
LDI 0
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_27:
LDI 13
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_28:
LDI 5
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_29:
LDI 6
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_30:
LDI 3
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_31:
LDI 0
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_32:
LDI 8
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_33:
LDI 2
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_34:
LDI 14
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_35:
LDI 4
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_36:
LDI 1
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_37:
LDI 5
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_38:
LDI 14
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_39:
LDI 13
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_40:
LDI 15
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_41:
LDI 8
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_42:
LDI 7
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_43:
LDI 10
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_44:
LDI 15
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_45:
LDI 9
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_46:
LDI 4
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_47:
LDI 8
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_48:
LDI 1
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_49:
LDI 11
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_50:
LDI 0
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_51:
LDI 15
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_52:
LDI 4
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_53:
LDI 11
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_54:
LDI 12
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_55:
LDI 4
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_56:
LDI 3
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_57:
LDI 3
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_58:
LDI 4
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_59:
LDI 12
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_60:
LDI 10
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_61:
LDI 11
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_62:
LDI 2
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_63:
LDI 2
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_64:
LDI 9
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_65:
LDI 10
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_66:
LDI 9
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_67:
LDI 0
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_68:
LDI 8
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_69:
LDI 7
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_70:
LDI 5
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_71:
LDI 5
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_72:
LDI 9
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_73:
LDI 2
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_74:
LDI 14
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_75:
LDI 12
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_76:
LDI 6
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_77:
LDI 14
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_78:
LDI 2
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_79:
LDI 11
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_80:
LDI 12
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_81:
LDI 4
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_82:
LDI 6
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_83:
LDI 9
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_84:
LDI 13
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_85:
LDI 11
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_86:
LDI 15
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_87:
LDI 0
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_88:
LDI 12
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_89:
LDI 10
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_90:
LDI 0
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_91:
LDI 1
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_92:
LDI 1
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_93:
LDI 7
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_94:
LDI 7
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_95:
LDI 6
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_96:
LDI 3
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_97:
LDI 15
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_98:
LDI 14
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_99:
LDI 15
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_100:
LDI 1
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_101:
LDI 5
ST S_LOOK_X
LDI 0
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_102:
LDI 2
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_103:
LDI 3
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_104:
LDI 11
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_105:
LDI 7
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_106:
LDI 7
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_107:
LDI 9
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_108:
LDI 10
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_109:
LDI 8
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_110:
LDI 3
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_111:
LDI 12
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_112:
LDI 14
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_113:
LDI 5
ST S_LOOK_X
LDI 4
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_114:
LDI 7
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_115:
LDI 6
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_116:
LDI 2
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_117:
LDI 8
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_118:
LDI 15
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_119:
LDI 10
ST S_LOOK_X
LDI 1
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_120:
LDI 1
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_121:
LDI 9
ST S_LOOK_X
LDI 7
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_122:
LDI 12
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_123:
LDI 6
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_124:
LDI 5
ST S_LOOK_X
LDI 2
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_125:
LDI 13
ST S_LOOK_X
LDI 6
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_126:
LDI 9
ST S_LOOK_X
LDI 5
ST S_LOOK_Y
JMP S_food_table_return
S_food_entry_127:
LDI 4
ST S_LOOK_X
LDI 3
ST S_LOOK_Y
JMP S_food_table_return
