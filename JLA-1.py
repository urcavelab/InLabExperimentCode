#!/Library/Frameworks/Python.framework/Versions/2.5/bin/python
# -*- coding: latin-1 -*-
"""JLA-1: Collaborators are Jessi Lesky and David Landy."""



################################################################
#                  Load Libraries--Ignore this                 #
################################################################

import pyaudio, pygame, wave, sys, threading, code, random, sys, ctypes.util, math, socket


OS = "OS X"
if OS == "OS X":
    import numpy, os
    new_nice = -10
    os.system("sudo renice -n %s %s" % (new_nice, os.getpid()))

from wx import *

import VisionEgg; VisionEgg.config.VISIONEGG_GUI_INIT = 0
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()

from VisionEgg.Core import *
from VisionEgg.MoreStimuli import *
from VisionEgg.FlowControl import Presentation
from MyDots import *
import VisionEgg.Daq

from VisionEgg.Text import *
from ExperimentLibrary03 import *
from VisionEgg.Textures import *

application = wx.PySimpleApp()
COMPUTER_NAME = socket.gethostname()



################################################################
#                  Experimenter parameters--ADJUST THESE       #
################################################################

subjectID = ask_user_for_sID()
test_mode = False
VisionEgg.config.VISIONEGG_FULLSCREEN = False
EXPERIMENT_CODE = "JLA-1"

output = ""
dirname = os.path.expanduser("~/Desktop/" + EXPERIMENT_CODE)
if not os.path.isdir(dirname + "/"):
    os.mkdir( dirname + "/")


outputdir = os.path.expanduser("~/Desktop/" + EXPERIMENT_CODE ) + "/"


random_sID = True
click_through_stimuli = True
skip_no_motion = False


# Audio Parameters
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
#RATE = 2000

SOUND_THRESHOLD = -20.0

BREAKS_EVERY_N = True
BREAK_N = 20

IMAGE_SCALING = 0.75

#######################################################
#            Stimulus Parameters--ADJUST THESE        #
#######################################################



foreground_color = (0.0, 0.0, 0.2, 1.0) #RGBA
background_color = (1.0, 1.0, 0.5, 1.0) #RGBA

font_size = 30

ball_velocity = 250
ball_size = 10.0
n_dots = 325
signal_fraction = 1.6


# Note to David--change to a hash
isi_time = 0.75
ippi_time = .5
prime_time = 10
probe_time = 2.0

response_key_1 = pygame.locals.K_q
response_key_2 = pygame.locals.K_p

stimulus_font_size = 40




if OS == "Windows":
    courier_font = "C:\WINDOWS\Fonts\COUR.TTF"
else :
    courier_font = "/Library/Fonts/Courier New Bold.ttf"


################################################################
#                  Some basic routines--Ignore these           #
################################################################

class Stimulus2(Stimulus):
    def __init__(self, stimulusString, attrString):
        if hasattr(Stimulus, '__init__'):
            Stimulus.__init__(self, stimulusString, attrString)
        self.correct = 0
##        print self.correct
##        if self.rAnd > self.lAnd:
##            swap = self.rAnd
##            self.rAnd = self.lAnd
##            self.lAnd = swap
##        self.lAnd = lAnd
##        self.lOp = lOp
##        self.mAnd = mAnd
##        self.rOp = rOp
##        self.rAnd = rAnd
        stimVals = (stimulusString[0:len(stimulusString)]).split("\t")
        self.itemNumber = stimVals[0]
        self.block = int(float(stimVals[1]))
        self.type = stimVals[2]
        self.index = stimVals[3]
        self.lAnd = int(float(stimVals[4]))
        self.lOp = unicode(stimVals[5], 'latin-1').replace("*", u"\u00D7")
        self.mAnd = int(float(stimVals[6]))
        self.rOp = unicode(stimVals[7], 'latin-1').replace("*", u"\u00D7")
        self.rAnd = int(float(stimVals[8]))
        self.correct = stimVals[9]
        self.direction = stimVals[10]
        self.isi_time = isi_time
        self.ippi_time = ippi_time
        self.prime_time = prime_time
        self.probe_time = probe_time
        self.responseCode = int(math.floor(RandomArray.random(1)*2))
    def pretty_name(self, timings=True, mode="prime"):
        if mode == "prime":
            crct = self.correct
        else:
            crct = 0

        if timings:
            return "%s\t%f\t%f\t%f\t%f" % \
                   (self.attr_text(),  \
                    self.isi_time, self.ippi_time, self.prime_time, self.probe_time \
                    )
        else:
            return self.attr_text()
            
    def prime_text(self): # Governs presentation in program
        return  "%s %s %s %s %s" % \
               (self.lAnd, self.lOp, self.mAnd, self.rOp, self.rAnd
               )

    def probe_text(self): # Governs presentation in program
        return  "Transform    Count    Remember    Other"




##################################
#    Read stimulus file          #
##################################

# This is the *OLD* way
#stimuli = []
#stimulusStrings = open('Algebra_Stimuli.txt','r').readlines()
#for stimulusString in stimulusStrings[1:]:
#    stimuli.append(Stimulus2(stimulusString, stimulusStrings[0]))

# The new way directly uses Excel files:
stimuli = read_stimuli_into_list(EXPERIMENT_CODE + '-Stimuli.xls', 0, Stimulus2)


#Check to make sure that each stimulus item has a unique "itemNumber" value

items = [s.item for s in stimuli]

#Instead of Item_number 
if not verify_item_uniqueness([s.item for s in stimuli]):
    report_error("Not all entries had unique item numbers!")


##################################
#    Set up Screen and Dots      #
##################################
screen = get_default_screen()
screen.parameters.bgcolor = background_color
image_size = screen.size
image_size = [screen.size[0] * IMAGE_SCALING, screen.size[1] * IMAGE_SCALING]





ball_color = foreground_color
dots_stimulus_left_fast = DotArea2DA(
    position                = (screen.size[0]/2.0, screen.size[1]/2.0),
    anchor                  = 'center',
    size                    = (512.0 , 384.0),
    signal_fraction         = signal_fraction,
    signal_direction_deg    = 180.0,
    velocity_min = ball_velocity/1.5,
    velocity_max = ball_velocity/1.0,
    dot_lifespan_sec        = 25.0,
    dot_size                = ball_size,
    num_dots                = n_dots,
    color                   = ball_color,
    mode                    = 'wind'
)

dots_stimulus_right_fast = DotArea2DA(
    position                = (screen.size[0]/2.0, screen.size[1]/2.0),
    anchor                  = 'center',
    size                    = (512.0 , 384.0),
    signal_fraction         = signal_fraction,
    signal_direction_deg    = 0.0,
    velocity_min = ball_velocity/1.5,
    velocity_max = ball_velocity/1.0,
    dot_lifespan_sec        = 25.0,
    dot_size                = ball_size,
    num_dots                = n_dots,
    color                   = ball_color,
    mode                    = 'wind'

)

dots_stimulus_left_slow = DotArea2DA(
    position                = (screen.size[0]/2.0, screen.size[1]/2.0),
    anchor                  = 'center',
    size                    = (512.0 , 384.0),
    signal_fraction         = signal_fraction,
    signal_direction_deg    = 180.0,
    velocity_min = ball_velocity/3.25,
    velocity_max = ball_velocity/2.25,
    dot_lifespan_sec        = 25.0,
    dot_size                = ball_size,
    num_dots                = n_dots,
    color                   = ball_color,
    mode                    = 'wind'

)

dots_stimulus_right_slow = DotArea2DA(
    position                = (screen.size[0]/2.0, screen.size[1]/2.0),
    anchor                  = 'center',
    size                    = (512.0 , 384.0),
    signal_fraction         = signal_fraction,
    signal_direction_deg    = 0.0,
    velocity_min = ball_velocity/3.25,
    velocity_max = ball_velocity/2.25,
    dot_lifespan_sec        = 25.0,
    dot_size                = ball_size,
    num_dots                = n_dots,
    color                   = ball_color,
    mode                    = 'wind'

)

dots_stimulus_none = DotArea2DA(
    position                = (image_size[0]/2.0, image_size[1]/2.0),
    anchor                  = 'center',
    size                    = (512.0 , 384.0),
    signal_fraction         = 1,
    signal_direction_deg    = 90.0,
    velocity_min = ball_velocity/2.0,
    velocity_max = ball_velocity/1.0,
    dot_lifespan_sec        = 25.0,
    dot_size                = ball_size,
    num_dots                = 000,
    color                   = ball_color,
    mode                    = 'wind'

)

dots_stimulus_neutral = DotArea2DA(
    position                = (screen.size[0]/2.0, screen.size[1]/2.0),
    anchor                  = 'center',
    size                    = (1024.0 , 768.0),
    signal_fraction         = 0,
    signal_direction_deg    = 90.0,
    velocity_min = ball_velocity/2.0,
    velocity_max = ball_velocity/1.0,
    dot_lifespan_sec        = 25.0,
    dot_size                = ball_size,
    num_dots                = n_dots,
    color                   = ball_color,
    mode                    = 'wind'

)

image_offset = 0.00

texture_mask1 = TextureStimulus(texture = Texture(os.path.join("","mask1.jpg")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)

texture_mask2 = TextureStimulus(texture = Texture(os.path.join("","mask2.jpg")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)

texture_mask3 = TextureStimulus(texture = Texture(os.path.join("","mask3.jpg")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)

texture_mask4 = TextureStimulus(texture = Texture(os.path.join("","mask4.jpg")),
                               position = [screen.size[0]*(0.5+image_offset), screen.size[1]/2.0],
                               anchor = 'center',
                               size = [image_size[0], image_size[1]],
                               shrink_texture_ok=1)


#######################
# Set up Text Windows #
#######################

# Note: this code doesn't use the text structure in ExperimentLibrary :-(

max_alpha = 1.0
text = Text(text="",
            color = foreground_color, # alpha is ignored (set with max_alpha_param)
            position=(screen.size[0]/2.0,screen.size[1]/2.0+90),
            font_size=font_size,
            font_name=courier_font,
            anchor='center',
            max_alpha = max_alpha)
textline2 = Text(text="",
            color = foreground_color, # alpha is ignored (set with max_alpha_param)
            position=(screen.size[0]/2.0,screen.size[1]/2.0+30),
            font_size=font_size,
            font_name=courier_font,
            anchor='center',
            max_alpha = max_alpha)
textline3 = Text(text="",
            color = foreground_color, # alpha is ignored (set with max_alpha_param)
            position=(screen.size[0]/2.0,screen.size[1]/2.0-30),
            font_size=font_size,
            font_name=courier_font,
            anchor='center',
            max_alpha = max_alpha)
textline4 = Text(text="",
            color = foreground_color, # alpha is ignored (set with max_alpha_param)
            position=(screen.size[0]/2.0,screen.size[1]/2.0-90),
            font_size=font_size,
            font_name=courier_font,
            anchor='center',
            max_alpha = max_alpha)

textStimulus = Text(text="Correct",
            color = foreground_color, # alpha is ignored (set with max_alpha_param)
            position=(screen.size[0]/2.0,screen.size[1]/2.0),
            font_size= stimulus_font_size,
            font_name=courier_font,
            anchor='center',
            max_alpha = max_alpha)


###############################################################
#  Create viewport - intermediary between stimuli and screen  #
###############################################################



viewport = Viewport(screen=screen, stimuli=[dots_stimulus_none, text])


##################################
#  Set up Subject File           #
##################################


    
# Make audio directory.
dirname = "audio"+ str(subjectID)
if not os.path.isdir(dirname + "/"):
    os.mkdir(outputdir+dirname+"/")

f = open(outputdir + dirname + "/" +  EXPERIMENT_CODE + '-'+ str(subjectID) + '.txt', 'w')

    

########################################
#  Create presentation object and go!  #
########################################
escape_code = False
x = 0 
q = Queue.Queue()


def go(mode, time=2):
    global x
    global escape_code
    global position
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
        ac = Audio_collection(FORMAT, CHANNELS, RATE, SOUND_THRESHOLD, stimulus.itemNumber, True, chunk, \
                         outputdir + "audio"+ str(subjectID) +"/" + EXPERIMENT_CODE +"-" + str(subjectID)+stimulus.itemNumber+".wav", prime_time, chunk, q)
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
        if(time_since_start - start_time > time):
            quit_now = True
        if (mode == "prime") and not (ac.is_alive()):
            quit_now = True


    if(mode=="prime"):
        if mode == "prime":
            tab = "0"
        else:
            tab = "1"       
        ac.join()
        audio_start_time = q.get()
        audio_end_time = q.get()
        if not (audio_end_time == 10000000):
            f.write("%s\t%f\t%f\t%f\t%d\t%s\t%s\t%f\t%f\t%s\t%f\t%d\t%s\n" % (stimulus.itemNumber + tab, audio_end_time-audio_start_time, audio_start_time, \
                                                                audio_end_time, \
                                                      subjectID, mode, stimulus.pretty_name(timings=False, mode=mode), start_time, time_since_start-start_time, \
                                                         response, rt,position," . ".join(other_responses)))
        else:
            f.write("%s\t%f\t%f\t%f\t%d\t%s\t%s\t%f\t%f\t%s\t%f\t%d\t%s\n" % (stimulus.itemNumber + tab, audio_end_time, audio_start_time, \
                                                                audio_end_time, \
                                                      subjectID, mode, stimulus.pretty_name(timings=False, mode=mode), start_time, time_since_start-start_time, \
                                                         response, rt,position," . ".join(other_responses)))

        f.flush()


    




########
#  Go  #
########



f.write("item\tduration\tsample_start\tsample_end\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tOther_keys\n"
% ("sID", "mode", stimuli[0].attr_names(), "start_time", "response",
"response_time", "position"))


last_block = 0
random.shuffle(stimuli)
item = 0
for stimulus in sorted(stimuli, cmp = lambda x,y: cmp(int(x.block), int(y.block))):
    if escape_code:
        break
    if(skip_no_motion and (int(stimulus.block)<2)):
        pass
    else :
        # Are we between runs?
        if stimulus.block != last_block or (BREAKS_EVERY_N and ((item+1) % BREAK_N) == 0) :
            item = 0
            text.parameters.font_size = 20
            if str(last_block)=="0":
                text.parameters.text = "Welcome to the experiment!"
                textline2.parameters.text = "We will begin with some"
                textline3.parameters.text = "practice trials."
                textline4.parameters.text = "Please press the space bar"
            elif str(last_block)=="1":
                text.parameters.text = "End of practice trials"
                textline2.parameters.text = "When you are ready to proceed"
                textline3.parameters.text = "Please press the space bar"
                textline4.parameters.text = " "
            else:
                text.parameters.text = "Feel free to take a short break"
                textline2.parameters.text = "When you are ready to proceed"
                textline3.parameters.text = "Please press the space bar"
                textline4.parameters.text = " "
            viewport = Viewport(screen=screen, stimuli=[text, textline2, textline3, textline4])
            wait_for_key(screen, viewport, pygame.locals.K_SPACE)
            last_block = stimulus.block

        # Figure out motion direction
        if stimulus.direction == "right_fast":
            current_dots = dots_stimulus_right_fast
        elif stimulus.direction == "left_fast":
            current_dots = dots_stimulus_left_fast
        elif stimulus.direction == "No motion":
            current_dots = dots_stimulus_none
        elif stimulus.direction == "right_slow":
            current_dots = dots_stimulus_right_slow
        elif stimulus.direction == "left_slow":
            current_dots = dots_stimulus_left_slow
        elif stimulus.direction == "none":
            current_dots = dots_stimulus_none
        elif stimulus.direction == "neutral":
            current_dots = dots_stimulus_neutral
        else :
            report_error("I didn't understand the motion direction: '"+stimulus.direction + "'") 

            sys.exit(-1)


        # Do isi 
        viewport = Viewport(screen=screen, stimuli=[current_dots, textStimulus])
        textStimulus.parameters.text = "|"
        textStimulus.parameters.position = (screen.size[0]/2.0,screen.size[1]/2.0)
        go("isi")

        
        # present prime
        viewport = Viewport(screen=screen, stimuli=[current_dots, textStimulus])
        textStimulus.parameters.text = stimulus.prime_text()
        position = random.randrange(1, 4)
        if position == 1: textStimulus.parameters.position = (screen.size[0]/2.0,screen.size[1]/2.0)
        elif position == 2: textStimulus.parameters.position = (screen.size[0]/2.0, screen.size[1]/2.0 - image_size[1]*0.25)
        elif position == 3: textStimulus.parameters.position = (screen.size[0]/2.0, screen.size[1]/2.0 + image_size[1]*0.25)
        go("prime")
        item = item + 1


        # Do ippi (inter-prime-probe-interval)
        textStimulus.parameters.text = "|"
        viewport = Viewport(screen=screen, stimuli=[current_dots, textStimulus])
        go("ippi")


        # Do probe presentation
        current_mask = random.randrange(1, 5)
        if current_mask == 1: viewport = Viewport(screen=screen, stimuli=[texture_mask1])
        elif current_mask == 2: viewport = Viewport(screen=screen, stimuli=[texture_mask2])
        elif current_mask == 3: viewport = Viewport(screen=screen, stimuli=[texture_mask3])
        elif current_mask == 4: viewport = Viewport(screen=screen, stimuli=[texture_mask4])
        go("probe")
        
f.close()
screen.close()

#   sleep(1) # Sleep for 1 second
