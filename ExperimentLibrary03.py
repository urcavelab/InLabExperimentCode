#!/Library/Frameworks/Python.framework/Versions/2.5/bin/python
# -*- coding: latin-1 -*-
"""Code base for experiments.  This should be imported into any and every experiment, and will (eventually) be progressively versioned"""

CAVE_Experiment_CODE_Version = 0.1

################################################################
#                  Load Libraries--Ignore this                 #
################################################################

import random, pygame, pyaudio, wave, sys, Queue, xlrd

import threading
from wx import *

#from Tkinter import *
#import tkSimpleDialog
#import tkMessageBox


OS = "OS X"
import ctypes.util
#import warnings
import pygame, math, datetime, random, sys
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
from VisionEgg.Core import *
from VisionEgg.MoreStimuli import *
from VisionEgg.FlowControl import Presentation
from MyDots import *
import VisionEgg.Daq
from VisionEgg.Text import *

####################################
#   Some General Utility Functions #
####################################

def verify_item_uniqueness(itemlist):
    uniques = uniqify(itemlist)
    if(len(uniques)==len(itemlist)):
        return True
    else:
        return False
    return False



def uniqify(seq, idfun=None): 
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def build_texture(image, position, size):
    global texture_list
    filename = os.path.join("",image)

    if texture_list.has_key(filename):
        texture = texture_list[filename]
    else:
        texture = Texture(filename)
        texture_list[filename] = texture

    return TextureStimulus(texture = texture,
                               position = position,
                               anchor = 'center',
                               size = size,
                               shrink_texture_ok=1)

def ask_user_for_sID(application=None):
    if None == application:
        application = wx.PySimpleApp()
    random_sID = wx.TextEntryDialog ( None, 'Enter Subject Number (cancel for random):', 'Enter Subject #', '1000' )

    if random_sID.ShowModal() == wx.ID_OK:
        subjectID = int(random_sID.GetValue())
    else:
        subjectID = int(math.floor(RandomArray.random(1)*1000000000))
    random_sID.Destroy()
    return subjectID

def report_error(errorText, application=None):
    if None == application:
        application = wx.PySimpleApp()
    wx.MessageDialog(None, "An error arose!", errorText, wx.OK).ShowModal()
    sys.exit(0)
    
class Textlines():
    """Instructions is just a holder for a set of Text windows, usueful for providing
        brief instructions to a subject, during breaks and pauses."""
    def __init__(self, screen, color, font_size, font_name, max_alpha, \
                 pos0 = None, pos1 = None, pos2 = None, pos3 = None, pos4= None, pos5=None):
        if pos0==None: pos0 = (screen.size[0]/2.0,screen.size[1]/2.0+90)
        if pos1==None: pos1 = (screen.size[0]/2.0,screen.size[1]/2.0+30)
        if pos2==None: pos2 = (screen.size[0]/2.0,screen.size[1]/2.0-30)
        if pos3==None: pos3 = (screen.size[0]/2.0,screen.size[1]/2.0-90)
        if pos4==None: pos4 = (screen.size[0]/2.0,screen.size[1]/2.0-120)
        if pos5==None: pos5 = (screen.size[0]/2.0,screen.size[1]/2.0-120)
        self.line = [0, 0, 0, 0, 0, 0]
        self.color = color
        self.font_size = font_size
        self.font_name = font_name
        self.max_alpha = max_alpha
        self.line[0] = Text(text="",
            color = self.color, # alpha is ignored (set with max_alpha_param)
            position=pos0, font_size=self.font_size, #font_name=self.font_name,
            anchor='center', max_alpha = self.max_alpha)
        self.line[1] = Text(text="",
            color = self.color, # alpha is ignored (set with max_alpha_param)
            position=pos1, font_size=self.font_size, #font_name=self.font_name,
            anchor='center', max_alpha = self.max_alpha)
        self.line[2] = Text(text="",
            color = self.color, # alpha is ignored (set with max_alpha_param)
            position=pos2, font_size=self.font_size, #font_name=self.font_name,
            anchor='center', max_alpha = self.max_alpha)
        self.line[3] = Text(text="",
            color = self.color, # alpha is ignored (set with max_alpha_param)
            position=pos3, font_size=self.font_size, #font_name=self.font_name,
            anchor='center', max_alpha = self.max_alpha)
        self.line[4] = Text(text="",
            color = self.color, # alpha is ignored (set with max_alpha_param)
            position=pos4, font_size=self.font_size, #font_name=self.font_name,
            anchor='center', max_alpha = self.max_alpha)        
        self.line[5] = Text(text="",
            color = self.color, # alpha is ignored (set with max_alpha_param)
            position=pos5, font_size=self.font_size, #font_name=self.font_name,
            anchor='center', max_alpha = self.max_alpha)
    def set_text_line(self, n, string):
        
        self.line[n].parameters.text = string
        return string
    
    def set_text(self, string): # starts at the top, and goes to the bottom
        text = string.split("\n")
        for i in range(0, min(len(text), len(self.line))):
            self.set_text_line(i, text[i])
        #if len(text) < 6:
        #    for i in range(len(text)+1, 5):
        #        self.set_text_line(i, "")
                               
    def get_views(self):
        return filter(lambda(x): not x.parameters.text=="" , self.line)
        

    
def get_sID(bRandom):
    if bRandom:
        subjectID = int(math.floor(RandomArray.random(1)*1000000000))
    else:
        application = wxPySimpleApp()
        random_sID = wxTextEntryDialog ( None, 'Enter Subject Number (cancel for random):', 'Enter Subject #', '1000' )

        if random_sID.ShowModal() == wxID_OK:
           subjectID = int(random_sID.GetValue())
        else:
           subjectID = int(math.floor(RandomArray.random(1)*1000000000))
        random_sID.Destroy()

    return subjectID


                
def wait_for_key( screen, viewport, target_key=pygame.locals.K_s):
    frame_timer = FrameTimer()
    while 1:
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                return False
            elif event.type == pygame.locals.KEYDOWN:
                if event.key == pygame.locals.K_ESCAPE :
                    sys.exit()
                elif event.key == target_key:
                    return True
        screen.clear()
        viewport.draw()
        swap_buffers()
        frame_timer.tick()

def loudness(chunk):
    '''Calculate and return volume of input samples

    Input chunk should be a numpy array of samples for analysis, as
    returned by sound card.  Sound card should be in 16-bit mono mode.
    Return value is measured in dB, will be from 0dB (maximum
    loudness) down to -80dB (no sound).  Typical very loud sound will
    be -1dB, typical silence is -36dB.

    '''
    data = numpy.array(chunk, dtype=float) / 32768.0
    ms = math.sqrt(numpy.sum(data ** 2.0) / len(data))
    if ms < 10e-8: ms = 10e-8
    return 10.0 * math.log(ms, 10.0)




class Stimulus:
    def __init__(self, stimulusString, attrString):
        stimVals = (stimulusString[0:len(stimulusString)-1]).split("\t")
        attrVals = (    attrString[0:len(    attrString)-1]).split("\t")
        if not len(stimVals) == len(attrVals):
            report_error("Error in Stimulus: the number of column headers does not equal the number of entries in some row:" \
                         + str(len(stimVals)) + " != " + str(len(stimVals)))
        else:
            for i in range(0, len(stimVals)-1):
                setattr(self, attrVals[i], stimVals[i])
##                print ":"+attrVals[i]+":   :"+stimVals[i]+":"

    def attr_text(self):
        ls = "\t".join([unicode(x).replace(u"\u00D7", "*") for x in self.__dict__.values()])
        return ls
    def attr_names(self):
        ls = "\t".join([str(x) for x in self.__dict__.keys()])
        return ls
                        
    def prime_text(self): # Governs presentation in program
        return  "%s %s %s" % \
               (self.operand1, self.operation, self.operand2
               )

    def probe_text(self): # Governs presentation in program
        return  "Transform    Count    Remember    Other"
    def ans_text(self):
        return "%s %s" % (self.itemNumber, self.correct)

def read_stimuli_into_list(workbook, sheet=0, Stimulus=Stimulus):
    stimuli = []
    stimuliXL = xlrd.open_workbook(workbook).sheet_by_index(sheet)
    for i in range(1, stimuliXL.nrows):
        stimuli.append(Stimulus("\t".join([str(x.value) for x in stimuliXL.row(i)]),
                                "\t".join([str(x.value) for x in stimuliXL.row(0)])))
    return stimuli


################################################################
# Create thread for audio collection
################################################################

class Audio_collection (threading.Thread):
    def __init__(self, format, channels, rate, sound_threshold, item, input, \
                 frames_per_buffer, file_name, time, chunk, q):

        self.format = format
        self.channels = channels
        self.rate = rate
        self.input = input
        self.frames_per_buffer = frames_per_buffer
        self.file_name = file_name
        self.time = time
        self.q = q
        self.rate = rate
        self.chunk = chunk
        self.sound_threshold = sound_threshold
        self.item = item
        threading.Thread.__init__ ( self )
        
    def run(self):
        p = pyaudio.PyAudio()
        time_stamped = False
        stream = p.open(format = self.format,
                        channels = self.channels,
                        rate = self.rate,
                        input = self.input,
                        frames_per_buffer = self.frames_per_buffer)

        print "* recording"
        all = []
        start_time = VisionEgg.time_func()
        i=0
        while (i <= self.rate / self.chunk * self.time) and ((not time_stamped) or (VisionEgg.time_func() < end_time + 2)):
            #for i in range(0, self.rate / self.chunk * self.time):
            data = stream.read(self.chunk)
            samps = numpy.fromstring(data, dtype=numpy.int16)
            all.append(data)
            loud = loudness(samps)
            #print str(i) + "   " + str(loud)
            if (not time_stamped) and loud > self.sound_threshold:
                end_time = VisionEgg.time_func()
                self.q.put(start_time)
                self.q.put(end_time)
                #self.f.write("%s\t%f\t%f\t%f\t" % (self.item, end_time-start_time, start_time, end_time))
                #self.f.flush()
                print "Crossed Threshold!"
                time_stamped = True
            i = i + 1
            
        if not time_stamped:
            self.q.put(start_time)
            self.q.put(10000000)
            #self.f.write("%s\t%f\t%f\t%f\t" % (self.item, 10000000, start_time, 10000000.0))

        print "* done recording"
        stream.close()
        p.terminate()

        # write data to WAVE file
        data = ''.join(all)
        wf = wave.open(self.file_name, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(data)
        wf.close()

################################################################
# Create header for an azk file
################################################################


def print_azk_main_header(f, computer_name, number_of_subjects):
    f.write("\n")
    f.write("Subjects incorporated to date: " + str(number_of_subjects) +"\n")
    f.write("Data file started on machine " + computer_name + "\n")

def print_azk_subject_header(f, computer_name, subjectID):
    now = datetime.datetime.now()
    f.write("\n")
    f.write("**********************************************************************\n")

    f.write("Subject " + str(subjectID) + ", " + now.strftime("%m/%d/%Y %H:%M:%S") + " on " + computer_name+ ", refresh 1000ms, ID " +str(subjectID) + "\n")


def getRandomInt(lower=0, upper=10, distribution="uniform"):
    if distribution == "uniform":
        return random.randrange(lower, upper)
    elif distribution == "uniform in digits":
        # Here lower and upper should be positive integers denoting the minimum and maximum number of digits.
        # in a 'log uniform' distribution, there is a uniform likelihood of a number of k digits. In addition, each
        # particular number of k digits is equally likely.
        k = random.randrange(lower, upper+1) #rand range is exclusive, but we want to be inclusive
        return int(("".join([str(x) for x in [random.randrange(1, 10) for i in range(0, k)]])))
    elif distribution == "log uniform":
        # here the probability of the log of the number is uniform, within some specified range, lower to upper
        return int(round(math.exp(random.uniform(math.log(lower), math.log(upper)))))
    else:
        report_error("I didn't understand the distribution you used: "+distribution)



