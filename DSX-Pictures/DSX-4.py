#!/Library/Frameworks/Python.framework/Versions/2.5/bin/python
# -*- coding: latin-1 -*-
"""DSX-3 code; For exploring the relationship between depth and arithmetic computation.  David Landy and Sally Linkenauger"""



################################################################
#                  Load Libraries--Ignore this                 #
################################################################

import pyaudio, wave, sys, Queue
import threading

from ExperimentLibrary02 import *

OS = "OS X"
import ctypes.util
#import time
if OS == "Windows" :
    sys.path.append("C:\Python25\Lib\site-packages\numpy")
    sys.path.append("C:\Python25\Lib\site-packages\VisionEgg")
    sys.path.append("C:\Python25\Lib\site-packages\pygame")
    import numpy
else:
    #import Numeric, RandomArray
    import numpy
    import os
    new_nice = -10
    os.system("sudo renice -n %s %s" % (new_nice, os.getpid()))
import VisionEgg; VisionEgg.config.VISIONEGG_GUI_INIT = 0
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
from VisionEgg.Core import *
from VisionEgg.MoreStimuli import *
from VisionEgg.FlowControl import Presentation
import VisionEgg.Daq
from VisionEgg.Text import *
from VisionEgg.Textures import *

import math, socket



COMPUTER_NAME = socket.gethostname()


dirname = os.path.expanduser("~/Desktop/DSX-4")
if not os.path.isdir(dirname + "/"):
    os.mkdir( dirname + "/")


################################################################
#                  Set up experiment directories               #
################################################################

outputdir = os.path.expanduser("~/Desktop/DSX-4") + "/"
#output = "/Volumes/Users/d/dlandy/inbox/Tapping/"
#output = ""

subjectID = ask_user_for_sID()
# Make audio directory.
dirname = "audio"+ str(subjectID)
if not os.path.isdir(outputdir+dirname + "/"):
    os.mkdir(outputdir+dirname+"/")
else:
    tkMessageBox.showwarning("Illegal Subject ID", "Subject ID " + str(subjectID) + " is taken or unusable")
    sys.exit()

################################################################
#                  Experimenter parameters                     #
################################################################

test_mode = False
VisionEgg.config.VISIONEGG_FULLSCREEN = False
VisionEgg.config.VISIONEGG_HIDE_MOUSE = True



random_sID = True
fMRI_Version = False
click_through_stimuli = True
skip_no_motion = False

chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
#RATE = 2000

SOUND_THRESHOLD = -20.0
BREAKS_EVERY_N = True
BREAK_N = 32
IMAGE_SCALING = 0.5

#########################################
#            Stimulus Constants         #
#########################################


EXPERIMENT_CODE = "DSX-4"
foreground_color = (0.0, 0.0, 0.0, 1.0)
background_color = (1.0, 1.0, 1.0, 1.0)

font_size = int(80 * IMAGE_SCALING)
font_size_stimulus = int(80 * IMAGE_SCALING)
max_alpha = 1.0
isi_time = 2
ippi_time = 2
prime_time = 8
probe_time = 1

if fMRI_Version:
    response_key_1 = pygame.locals.K_4
    response_key_2 = pygame.locals.K_7
else:
    response_key_1 = pygame.locals.K_q
    response_key_2 = pygame.locals.K_p


if OS == "Windows":
    courier_font = "C:\WINDOWS\Fonts\COUR.TTF"
else :
    courier_font = "/Library/Fonts/Courier New Bold.ttf"

################################################################
#                  Some basic routines--Ignore these           #
################################################################




class Stimulus2(Stimulus):
    def __init__(self, stimulusString):
        #Stimulus.__init__(self, stimulusString)
        stimVals = (stimulusString[0:len(stimulusString)-1]).split("\t")
        self.itemNumber = stimVals[0]
        self.block = stimVals[1]
        self.type = stimVals[2]
        self.index = stimVals[3]
        self.lAnd = stimVals[4]
        self.lOp = unicode(stimVals[5], 'latin-1').replace("*", u"\u00D7")
        self.mAnd = stimVals[6]
        self.rOp = unicode(stimVals[7], 'latin-1').replace("*", u"\u00D7")
        self.rAnd = stimVals[8]
        self.correct = stimVals[9]
        self.fronted = stimVals[10]
        self.isi_time = isi_time
        self.ippi_time = ippi_time
        self.prime_time = prime_time
        self.probe_time = probe_time
    def pretty_name(self, timings=True):
        if timings:
            return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%f\t%f\t%f\t%f" % \
                   (self.itemNumber, self.block,  self.type, self.index, self.lAnd, self.lOp.replace(u"\u00D7", "*"), self.mAnd, self.rOp.replace(u"\u00D7", "*"), \
                    self.rAnd, self.Correct, \
                    self.isi_time, self.ippi_time, self.prime_time, self.probe_time \
                    )
        else:
            return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s " % \
                   (self.itemNumber, self.block,  self.type, self.index, self.lAnd, self.lOp.replace(u"\u00D7", "*"), self.mAnd, self.rOp.replace(u"\u00D7", "*"), \
                    self.rAnd, self.correct \
                    )
            
    def prime_text(self): # Governs presentation in program
        return  "%s\n%s\n%s\n%s\n%s" % \
               (self.lAnd, self.lOp, self.mAnd, self.rOp, self.rAnd
               )

    def probe_text(self): # Governs presentation in program
        return  ""

        
screen = VisionEgg.Core.Screen( size = (1280,960), frameless = True )
screen.parameters.bgcolor = background_color # make black (RGBA)
        
image_size = screen.size
image_size = [screen.size[0] * IMAGE_SCALING, screen.size[1] * IMAGE_SCALING]


##################################
#    Read stimulus file          #
##################################

stimuli = []
for stimulusString in open('Arithmetic_Stims.txt','r').readlines():
    stimuli.append(Stimulus2(stimulusString))




######################################
#    Load and Construct Background   #
######################################

image_offset = 0.00
text_offset = 0.03
# For Jessi: This code creates the images.  "Texture" means "picture".

texture_left = TextureStimulus(texture = Texture(os.path.join("","Cylinders_Left_Front.png")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)

texture_right = TextureStimulus(texture = Texture(os.path.join("","Cylinders_Right_Front.png")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)
texture_ippi = TextureStimulus(texture = Texture(os.path.join("","IPPI_Image.png")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)

texture_fixation = TextureStimulus(texture = Texture(os.path.join("","Fixation.png")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)



def offcenter(x, y):
    return (screen.size[0]*0.5 + image_size[0]*x,
            screen.size[1]*0.5 + image_size[1]*y)


instructions = Textlines(screen, foreground_color, font_size, courier_font, max_alpha)   
textStimulus = Textlines(screen, foreground_color, font_size_stimulus, courier_font, max_alpha,
                         pos0 = offcenter(-0.16 - text_offset, 0.1),
                         pos1 = offcenter(-0.08 - text_offset, 0.1), 
                         pos2 = offcenter(0 - text_offset, 0.1),
                         pos3 = offcenter(0.08 - text_offset, 0.1),
                         pos4 = offcenter(0.16 - text_offset, 0.1))
 


###############################################################
#  Create viewport - intermediary between stimuli and screen  #
###############################################################



viewport = Viewport(screen=screen, stimuli=[], position=(screen.size[0]/2.0, screen.size[0]/2.0), size=image_size)


##################################
#  Set up Subject File           #
##################################

# subjectID = get_sID(random_sID)





    

f = open(outputdir + dirname + "/" +  EXPERIMENT_CODE + str(subjectID) + '.txt', 'w')

      
########################################
#  Create presentation object and go!  #
########################################
escape_code = False
x = 0 
q = Queue.Queue()

def go(mode, time=2):
    global x
    global escape_code 
    quit_now = False
    response = None
    other_responses = []
    rt = -1000
    frame_timer = FrameTimer()
    if mode == "isi":
        time = stimulus.isi_time
    elif mode == "ippi":
        time = stimulus.ippi_time
    elif mode == "prime":
        time = stimulus.prime_time
    elif mode == "probe":
        time = stimulus.probe_time


    if(mode == "prime"):

        x = x + 1
        print "collecting " + str(x)
        ac = Audio_collection(FORMAT, CHANNELS, RATE, SOUND_THRESHOLD, stimulus.itemNumber, True, \
                         chunk, outputdir + "audio"+ str(subjectID) +"/" + EXPERIMENT_CODE + str(subjectID)+stimulus.itemNumber+".wav", prime_time, chunk, q)
        ac.start()

    start_time = VisionEgg.time_func()
    while not quit_now:





        # Process keyboard inputs
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                quit_now = True
            elif event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_BACKQUOTE :
                    quit_now = True
                    escape_code = True
                    f.close()
                    screen.close()
                    #screen2.close()
                    sys.exit()
                    
                elif event.key == response_key_1 :
                    if response==None:
                        rt = VisionEgg.time_func() - start_time
                        response = "LeftResponse"
                        if click_through_stimuli:
                            quit_now = True
                    else :
                        other_responses.append(str(event.key) + " " + str(VisionEgg.time_func() - start_time))
                elif event.key == response_key_2 :
                    if response==None:
                        rt = VisionEgg.time_func() - start_time
                        response = "RightResponse"
                        if click_through_stimuli:
                            quit_now = True
                    else :
                        other_responses.append(str(event.key) + " " + str(VisionEgg.time_func() - start_time))


                elif event.key == pygame.locals.K_BACKQUOTE:
                    quit_now =  True
                else :
                        other_responses.append(str(event.key) + " " + str(VisionEgg.time_func() - start_time))
                    #text.parameters.text+=event.unicode
        screen.clear()
        viewport.draw()
        swap_buffers()
        frame_timer.tick()
        time_since_start = VisionEgg.time_func()
        if((time_since_start - start_time > time) ):
            quit_now = True
        if (mode == "prime") and not (ac.is_alive()):
            quit_now = True


    

    if(mode=="prime"):
        ac.join()
        #while threading.activeCount() > 2: # This is sheer magic.  I'm not sure why there are two threads active at this point, so it could break at any moment.
        #    print threading.activeCount()
    
        audio_start_time = q.get()
        audio_end_time = q.get()

        if not (audio_end_time == 10000000):
            f.write("%s\t%f\t%f\t%f\t%s\t%d\t%s\t%f\t%f\t%s\n" % (stimulus.itemNumber, audio_end_time-audio_start_time, audio_start_time, \
                                                                audio_end_time, \
                                                                stimulus.pretty_name(timings=False), \
                                                                subjectID, mode, start_time, time_since_start-start_time, \
                                                                " . ".join(other_responses)))
        else:
            f.write("%s\t%f\t%f\t%f\t%s\t%d\t%s\t%f\t%f\t%s\n" % (stimulus.itemNumber, audio_end_time, audio_start_time, \
                                                                audio_end_time, \
                                                                stimulus.pretty_name(timings=False), \
                                                                subjectID, mode, start_time, time_since_start-start_time, \
                                                                " . ".join(other_responses)))

        f.flush()


    




########
#  Go  #
########



f.write("item\tduration\tsample_start\tsample_end\t%s\t%s\t%s\t%s\t%s\tOther_keys\n" % (stimuli[0].pretty_name(timings=False), \
                                                                              "sID", "mode", "onset_time",  "record_time"))
last_block = -1
stimuli = stimuli[1:]
random.shuffle(stimuli)

print(str(len(stimuli)))

item = 0
for stimulus in sorted(stimuli, cmp = lambda x,y: cmp(int(x.block), int(y.block))):
    if escape_code:
        break
    if(skip_no_motion and (int(stimulus.block)<2)):
        pass
    else :
        # Are we between runs?
        if stimulus.block != last_block or (BREAKS_EVERY_N and ((item+1) % BREAK_N) == 0) :
            last_block = stimulus.block
            item = 0
            if fMRI_Version:
                instructions.set_text("The next run will begin in a moment\n" +
                                      "If you need to move your head\n" +
                                      "or cough, please do it now.")
                viewport = Viewport(screen=screen, stimuli=[instructions.get_views()])
                wait_for_key(screen, viewport, pygame.locals.K_SPACE)
                #text.parameters.text = "|"
                viewport = Viewport(screen=screen, stimuli=[text])
                wait_for_key(screen, viewport, pygame.locals.K_s)
            else:
                if str(stimulus.block)=="1":
                    instructions.set_text("Welcome to the experiment!\n"+
                                          "When you are ready to begin\n" +
                                          "Please press the space bar")
                else:
                    instructions.set_text("Feel free to take a short break\n" +
                                          "When you are ready to proceed\n" +
                                          "Please press the space bar")
                
                viewport = Viewport(screen=screen, stimuli=instructions.get_views())
                wait_for_key(screen, viewport, pygame.locals.K_SPACE)
        # Do isi
        textStimulus.set_text("\n\n|\n\n")
        if stimulus.fronted == "none":
            viewport = Viewport(screen=screen, stimuli=textStimulus.get_views())
        else:
            viewport = Viewport(screen=screen, stimuli=[texture_fixation] + textStimulus.get_views())
        go("isi")
        if(fMRI_Version): wait_for_key(screen, viewport, target_key=pygame.locals.K_s)

        
        # present prime
        textStimulus.set_text(stimulus.prime_text())
        if stimulus.fronted == "left":
            texture = texture_left
        else:
            texture = texture_right
        if stimulus.fronted == "none":
            viewport = Viewport(screen=screen, stimuli= textStimulus.get_views())
        else:
            viewport = Viewport(screen=screen, stimuli=[texture] + textStimulus.get_views())
        go("prime")
        item = item + 1

        # For Jessi: this code presents the texture
        
        viewport = Viewport(screen=screen, stimuli=[texture_ippi])
        go("ippi")

f.close()
screen.close()

#screen2.close()
#   sleep(1) # Sleep for 1 second
