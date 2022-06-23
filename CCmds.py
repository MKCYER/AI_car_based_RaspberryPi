'''
Control Byte
 +------+------+------+------+------+------+------+------+------+
 | bit8 | bit7 | bit6 | bit5 | bit4 | bit3 | bit2 | bit1 | bit0 |
 +------+------+------+------+------+------+------+------+------+

 bit0：模式控制
       bit4：停止
       bit5：手动控制
       bit6：自动巡线
       bit7：自动避障

 bit1：移动控制
       bit3：停止
       bit4：前进
       bit5：后退
       bit6：左转
       bit7：右转

 bit2：云台控制
      bit3：停止
      bit4：上
      bit5：下
      bit6：左
      bit7：右
 bit3：PING请求/响应
'''
class CCmds:
    MODE_CONTROL = 0x01
    MOVE_CONTROL = 0x02
    CAMERA_CONTROL = 0x04
    PING = 0x08

    MODE_STOP = 0x10
    MODE_MANUAL_CONTROL = 0x20
    MODE_AUTO_WIRE = 0x40
    MODE_AUTO_MOVE = 0x80

    MOVE_STOP = 0x08
    MOVE_FORWARD = 0x10
    MOVE_BACK = 0x20
    MOVE_LEFT = 0x40
    MOVE_RIGHT = 0x80

    CAMERA_UP = 0x10
    CAMERA_DOWN = 0x20
    CAMERA_LEFT = 0x40
    CAMERA_RIGHT = 0x80

def Cmd2Bytes(cmds):
    return cmds.to_bytes(1, 'big')
