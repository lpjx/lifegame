#-*- coding:utf8 -*-
import pygame, sys, time
import pymysql
import numpy as np
from pygame.locals import *

def selectmap(id):
    conn=pymysql.connect(host="127.0.0.1",
                     port=3306,
                     user="root",
                     passwd='',
                     db="lifegame",
                     charset='utf8'
                     )
    cursor=conn.cursor()
    sql="select path from map where id=%d"%id
    #setattr(1, id, id1)
    cursor.execute(sql)
        
#     print(cursor.rowcount)
    rs=cursor.fetchall()
    cursor.close()
    conn.close()
    for row in rs:
        return "%s"%row
#     rs=cursor.fetchmany(3)
#     print(rs)
#     rs=cursor.fetchall()
#     print(rs)
def count():
    conn=pymysql.connect(host="127.0.0.1",
                     port=3306,
                     user="root",
                     passwd='',
                     db="lifegame",
                     charset='utf8'
                     )
    cursor=conn.cursor()
    sql="select count(*) from map"
    cursor.execute(sql)
    rs=cursor.fetchall()
    cursor.close()
    conn.close()
    
    for row in rs:
        return "%d"%row

def add(id,value):
    conn=pymysql.connect(host="127.0.0.1",
                     port=3306,
                     user="root",
                     passwd='',
                     db="lifegame",
                     charset='utf8'
                     )
    cursor=conn.cursor()
    sql='insert into map values("%d","%s");'% (id,value)
    
    cursor.execute(sql)
    conn.commit()
    if cursor.rowcount != 1:
        raise Exception('插入失败')
    cursor.close()
    conn.close()

class Button(object):
    """这个类是一个按钮，具有自我渲染和判断是否被按上的功能"""
    def __init__(self,position):
 
        self.position = position
 
    def add(self, surface,path):
        # 家常便饭的代码了
        x, y, = self.position
        b = pygame.image.load(path)
        surface.blit(b,[x,y])
 
    def is_over(self, point):
        # 如果point在自身范围内，返回True
        point_x, point_y = point
        x, y, z, h = self.position
 
        in_x = point_x >= x and point_x < x + z
        in_y = point_y >= y and point_y < y + h
        return in_x and in_y

#矩阵宽与矩阵高
WIDTH = 90
HEIGHT = 40
STATE = 0#状态位，0表示自动，1表示手动
R = 3
INDEX = 0

#记录鼠标按键情况的全局变量
pygame.button_down = False

#记录游戏世界的矩阵
pygame.world=np.zeros((HEIGHT,WIDTH-10))#世界地图是一个二维数组，初始均为零
#创建 Cell 类方便细胞绘制
class Cell(pygame.sprite.Sprite):

    size = 10

    def __init__(self, position):#position为该cell在画布中的位置

        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([self.size, self.size])

        #填上白色
        self.image.fill((20,255,255))

        # 创建一个以左上角为锚点的矩形
        self.rect = self.image.get_rect()
        self.rect.topleft = position

#保存新地图
#把world写入文件中
def savemap():
    try:
        num = count()
        path = "text%s%s"%(str(num),".txt")
        fsock = open(path, "w")
    except IOError:
            print ("The file don't exist, Please double check!")
            exit()
    print ('The file mode is ',fsock.mode)
    print ('The file name is ',fsock.name)
    for i in range(0, HEIGHT):
        for j in range(0,WIDTH-10):
            fsock.write((str)((int)(pygame.world[i][j])))
        fsock.write('\r\n')
    fsock.close()
    add((int)(count()),path)


#读取本地已有地图示例
def readmap():
    global INDEX
    try:
        t = INDEX
        if (int)(count()) != 0:
            INDEX = INDEX % (int)(count())   
        path = selectmap(INDEX)
        INDEX +=1
        print (path)
        fsock = open(path, "r")
    except IOError:
            print ("The file %d don't exist, Please double check!"%t)
            exit()
    print ('The file mode is ',fsock.mode)
    print ('The file name is ',fsock.name)
    i=0
    AllLines = fsock.readlines()
    for EachLine in AllLines:
        print(EachLine)
        if EachLine == '\r\n':
            pass
        else:
            for j in range(0,WIDTH-10):
                if(EachLine[j]=='1'):
                    pygame.world[i][j]=1
                elif(EachLine[j]=='0'):
                    pygame.world[i][j]=0
            i=i+1
    fsock.close()


#绘图函数，注意到我们是把画布重置了再遍历整个世界地图，因此有很大的性能提升空间
def draw():
    screen.fill((0,0,0))#第一步用黑色填充窗口,且分割出一部分做菜单栏，增加按钮。
    pygame.draw.rect(screen,[255,255,255],[800, 0, 100, 400],0)
    b1 = Button((800,0))
    b1.add(screen,'start.jpg')
    b2 = Button((800,30))
    b2.add(screen,'stop.jpg')
    b3 = Button((800,60))
    b3.add(screen,'change.jpg')
    b4 = Button((800,90))
    b4.add(screen,'reset.jpg')
    b5 = Button((800,120))
    b5.add(screen,'map.jpg')
    b6 = Button((800,150))
    b6.add(screen,'save.jpg')
    b6 = Button((825,180))
    b6.add(screen,'next.jpg')
    
    #第二步，访问存储数据的数组，将存在的cell画到画布中
    for sp_col in range(pygame.world.shape[1]):
        for sp_row in range(pygame.world.shape[0]):
            if pygame.world[sp_row][sp_col]:
                new_cell = Cell((sp_col * Cell.size,sp_row * Cell.size))
                screen.blit(new_cell.image,new_cell.rect)#第一个参数是源surface对象，第二个是位置

#根据细胞更新规则更新地图
#规则：如果一个细胞周围有3个细胞为生（一个细胞周围共有8个细胞），则该细胞为生，
  #即该细胞若原先为死，则转为生，若原先为生，则保持不变；
  #2． 如果一个细胞周围有2个细胞为生，则该细胞的生死状态保持不变；
  #3． 在其它情况下，该细胞为死。                
def next_generation():
    nbrs_count = sum(np.roll(np.roll(pygame.world, i, 0), j, 1)
                 for i in (-1, 0, 1) for j in (-1, 0, 1)
                 if (i != 0 or j != 0))
#astypy()返回一个数组
    pygame.world = (nbrs_count == 3) | ((pygame.world == 1) & (nbrs_count == 2)).astype('int')

#地图初始化
def init():
    pygame.world.fill(0)
    draw()
    return 'Stop'

#停止时的操作
def stop():
    global STATE
    for event in pygame.event.get():
        if event.type == QUIT:#退出
            pygame.quit()
            sys.exit()

        if event.type == KEYDOWN and event.key == K_RETURN:
            return 'Move'

        if event.type == KEYDOWN and event.key == K_r:
            return 'Reset'
        if event.type == KEYDOWN and event.key == K_o:
            return 'One_step'
        if event.type == KEYDOWN and event.key == K_m:
            return 'Move'

        if event.type == MOUSEBUTTONDOWN:#鼠标摁下
            pygame.button_down = True
            pygame.button_type = event.button

        if event.type == MOUSEBUTTONUP:#鼠标释放
            pygame.button_down = False

        if pygame.button_down:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            sp_col = mouse_x / Cell.size;
            sp_row = mouse_y / Cell.size;
            #若为左键则为安放一个cell，右键则为消灭一个cell
            if pygame.button_type == 1 and sp_col<WIDTH-10: #鼠标左键
                pygame.world[sp_row][sp_col] = 1
            elif pygame.button_type == 3 and sp_col<WIDTH-10: #鼠标右键
                pygame.world[sp_row][sp_col] = 0
            elif pygame.button_type == 1 and sp_col>WIDTH-10:#鼠标左键
                if sp_row<3:
                    return 'Move'
                elif sp_row>=6 and sp_row<9:
                    if STATE==0:
                        STATE = 1
                        return 'One_step'
                    if STATE==1:
                        STATE = 0
                        return 'Move'
                elif sp_row>=9 and sp_row<12:
                    return 'Reset'
                elif sp_row>=12 and sp_row<15:
                    readmap()
                    draw()
                elif sp_row>=15 and sp_row<18:
                    savemap()
                elif sp_row>=18 and sp_row<23:
                        next_generation()
                        draw()
                        pygame.clock_start = time.clock()
                        return 'One_step'
                    
            draw()

    return 'Stop'

#计时器，控制帧率
pygame.clock_start = 0


#进行演化时的操作
def one_step():
    global STATE
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN and event.key == K_SPACE:
            return 'Stop'
        if event.type == KEYDOWN and event.key == K_r:
            return 'Reset'
        if event.type == KEYDOWN and event.key == K_o:
            return 'Move'
        if event.type == KEYDOWN and event.key == K_n:
            next_generation()
            draw()
            pygame.clock_start = time.clock()
        
        if event.type==MOUSEBUTTONDOWN:
            pygame.button_down = True
            pygame.button_type = event.button

        if event.type == MOUSEBUTTONUP:
            pygame.button_down = False

        if pygame.button_down:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            sp_col = mouse_x / Cell.size;
            sp_row = mouse_y / Cell.size;

            if pygame.button_type == 1 and sp_col<WIDTH-10: #鼠标左键
                pygame.world[sp_row][sp_col] = 1
            elif pygame.button_type == 3 and sp_col<WIDTH-10:#鼠标右键
                pygame.world[sp_row][sp_col] = 0
            elif pygame.button_type == 1 and sp_col>WIDTH-10:#鼠标左键
                if sp_row<3:
                    return 'Move'
                elif sp_row>=6 and sp_row<9:
                    if STATE==0:
                        STATE=1
                        return 'One_step'
                    elif STATE==1:
                        STATE=0
                        return 'Move'
                elif sp_row>=9 and sp_row<12:
                    return 'Reset'
                elif sp_row>=12 and sp_row<15:
                    readmap()
                    draw()
                elif sp_row>=15 and sp_row<18:
                    savemap()
                elif sp_row>=18 and sp_row<23:
                        next_generation()
                        draw()
                        pygame.clock_start = time.clock()
                        return 'One_step'
            draw()

    return 'One_step'

def move():
    global STATE
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN and event.key == K_SPACE:
            return 'Stop'
        if event.type == KEYDOWN and event.key == K_r:
            return 'Reset'
        if event.type == KEYDOWN and event.key == K_o:
            return 'One_step'
        if event.type==MOUSEBUTTONDOWN:
            pygame.button_down = True
            pygame.button_type = event.button

        if event.type == MOUSEBUTTONUP:
            pygame.button_down = False

        if pygame.button_down:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            sp_col = mouse_x / Cell.size;
            sp_row = mouse_y / Cell.size;

            if pygame.button_type == 1 and sp_col<WIDTH-10: #鼠标左键
                pygame.world[sp_row][sp_col] = 1
            elif pygame.button_type == 3 and sp_col<WIDTH-10:#鼠标右键
                pygame.world[sp_row][sp_col] = 0
            elif pygame.button_type == 1 and sp_col>WIDTH-10:#鼠标左键
                if sp_row<3:
                    return 'Move'
                elif sp_row>=3 and sp_row<6:
                    return 'Stop'
                elif sp_row>=6 and sp_row<9:
                    if STATE==0:
                        STATE=1
                        return 'One_step'
                    elif STATE==1:
                        STATE=0
                        return 'Move'
                elif sp_row>=9 and sp_row<12:
                    return 'Reset'
                elif sp_row>=12 and sp_row<15:
                    readmap()
                    draw()
                elif sp_row>=15 and sp_row<18:
                    savemap()
                elif sp_row>=18 and sp_row<23:
                        next_generation()
                        draw()
                        pygame.clock_start = time.clock()
                        return 'One_step'
            draw()
    if time.clock() - pygame.clock_start >0.02:
            next_generation()
            draw()
            pygame.clock_start = time.clock()

    return 'Move'


if __name__ == '__main__':

    #状态机对应三种状态，初始化，停止，进行
    state_actions = {
            'Reset': init,
            'Stop': stop,
            'Move': move,
            'One_step':one_step
            
        }
    state = 'Reset'

    pygame.init()
    pygame.display.set_caption('Conway\'s Game of Life')

    screen = pygame.display.set_mode((WIDTH * Cell.size, HEIGHT * Cell.size))

    while True: # 游戏主循环

        state = state_actions[state]()
        pygame.display.update()
