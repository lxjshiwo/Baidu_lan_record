# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""

from PyQt4.QtGui import QMainWindow
from PyQt4.QtCore import pyqtSignature
from PyQt4 import QtCore, QtGui

from Ui_baidu_lan_main import Ui_MainWindow

import os
import sys
import json
import time
import pycurl

#to filter the record voice
import numpy as np

#for the wav recording
import wave
from pyaudio import PyAudio,paInt16
import urllib2
from tornado.test.curl_httpclient_test import pycurl

#to define a thread class
import threading
import Queue
from gevent.hub import sleep

class MyThread(threading.Thread):
    '''
    the class for the thread running control
    '''
    def __init__(self,func,args,name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        
    def getResult(self):
         return self.args   

    def run(self):
        print 'starting',self.name,'at:',time.ctime()
        self.res = apply(self.func,self.args)
        print self.name,'finished at:',time.ctime()



class MainWindow(QMainWindow, Ui_MainWindow,threading.Thread):
    """
    the MainWindow GUI Class
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QMainWindow.__init__(self, parent)
        threading.Thread.__init__(self)
        self.setupUi(self)
 
        #init self wav record param
        self.framerate = 8000
        self.NUM_SAMPLES  = 2000
        #to filter the voice 
        self.LEVEL = 600
        #to compare with the accumulate voice point vover Threshold
        self.mute_count_limit = 50
        self.mute_begin = 0
        self.mute_end = 1
        self.not_mute = 0
        
        #record time
        self.TIME = 1
        self.channels = 1
        self.sampwidth = 2
        
        #the index of the file
        self.voice_queue = Queue.Queue(1024)
        self.wav_queue = Queue.Queue(1024)
        self.file_name_index = 1
        self.thread_flag = 0
        self.start_flag = 0
        
        
#         try:
#             self.serial = serial.Serial('COM8',9600)
#         except Exception as e:
#             print e
#             self.serial = None
        
    
    def save_wave_file(self,filename,data):
        '''
            save the data to the wav file
        '''
        wf = wave.open(filename,'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.sampwidth)
        wf.setframerate(self.framerate)
        wf.writeframes("".join(data))
        wf.close()
    
    
    def run(self):
        '''
        the thread function recording the voice
        '''
        print 'starting',self.name,'at:',time.ctime()
        self.res = apply(self.my_record)
        print self.name,'finished at:',time.ctime()
    
    
        
    def my_record(self,temp):
        while self.start_flag == 1:
            pa = PyAudio()
            
            stream = pa.open(
                                format=paInt16,
                                channels = 1,
                                rate = self.framerate,
                                input = True,
                                frames_per_buffer = self.NUM_SAMPLES)
            my_buf = []
            count = 0
            while count < self.TIME*20:
                string_audio_data = stream.read(self.NUM_SAMPLES)
                #without filtering the audio data
#                 my_buf.append(string_audio_data)
#                 count += 1
#                 print '.'
                #to filter the voice with a define LEVEL
                audio_data = np.fromstring(string_audio_data,dtype=np.short)
                large_sample_count = np.sum(audio_data > self.LEVEL)
                print large_sample_count
                if large_sample_count < self.mute_count_limit:
                    self.mute_beigin = 1
                else:
                    my_buf.append(string_audio_data)
                    self.mute_begin = 0
                    self.mute_end = 1
                count += 1
                #the spare part of the voice recording 
                if(self.mute_end - self.mute_begin) > 9:
                    self.mute_begin = 0
                    self.mute_end = 1
                    break
                if self.mute_begin:
                    self.mute_end +=1
                print '.'
                

            
            
            if my_buf:
                if self.file_name_index < 11:
                    pass
                else:
                    self.file_name_index = 1
                filename = str(self.file_name_index)+'.wav'
                self.save_wave_file(filename=filename,data=my_buf)
                self.writeQ(queue=self.wav_queue,data=filename)
                self.file_name_index += 1
                print filename,'saved'
            else:
                print'file not saved!'
            
            my_buf = [] 
            
    #         self.save_wave_file('01.wav', my_buf)
            stream.close()
        
    def dump_res(self,buf):
        print buf
        my_temp = json.loads(buf)
        if my_temp['err_no']:
            if my_temp['err_no'] == 3300:
                print u'参数输入不正确'
            elif my_temp['err_no'] == 3301:
                print u'识别错误'
            elif my_temp['err_no'] == 3302:
                print u'验证失败'
            elif my_temp['err_no'] == 3303:
                print u'语音识别后端问题'
            elif my_temp['err_no'] == 3304:
                print u'请求GPS过大，超过限额'
            elif my_temp['err_no'] == 3305:
                print u'产品线当前日请求数目超过限额'
        else:
            my_list = my_temp['result']
            print type(my_list)
            print my_list[0]
            self.textBrowser.append(my_list[0])
            
            #to combine with the serial module user can make a switch case selection after result translated
#             if u'我要上厕所' in my_list[0]:
#                 print 'close switch'
#                 if self.serial:
#                     self.serial.write('B')
#             elif u'我要睡觉' in my_list[0]:
#                 print 'open switch'
#                 if self.serial:
#                     self.serial.write('A')
#             else:
#                 pass
    def get_token(self):
        apiKey = 'bGxcA8SRIrwKtp1GhE4aZ2rs'
        secretKey = 'a72b7d8535ef7a29914850a88b0fdbe7'
        auth_url = 'https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id='+apiKey+'&client_secret='+secretKey
        print auth_url
        res = urllib2.urlopen(auth_url)
        json_data = res.read()
        
        return json.loads(json_data)['access_token']
    
    def use_cloud(self,token):
        while True:
            if self.wav_queue.qsize():
                filename = self.readQ(queue=self.wav_queue)
            else:
                continue
            fp = wave.open(filename, 'rb')
            nf = fp.getnframes()
#             print 'sampwidth:',fp.getsampwidth()
#             print 'framerate:',fp.getframerate()
#             print 'channels:',fp.getnchannels()
            f_len = nf*2
            audio_data = fp.readframes(nf)
            
            cuid = 'xxxxxxxxxx'
            srv_url = 'http://vop.baidu.com/server_api'+'?cuid='+cuid+'&token='+token
            http_header = [
                'Content-Type:audio/pcm;rate=8000',
                'Content-length:%d' % f_len
            ]
            
            
            c = pycurl.Curl()
            c.setopt(pycurl.URL,str(srv_url)) #curl doesn't support unicode
            #c.setopt(c.RETURNTRANSE,1)
            c.setopt(c.HTTPHEADER,http_header) 
            c.setopt(c.POST,1)
            c.setopt(c.CONNECTTIMEOUT,80)
            c.setopt(c.TIMEOUT,80)
            c.setopt(c.WRITEFUNCTION,self.dump_res)
            c.setopt(c.POSTFIELDS,audio_data)
            c.setopt(c.POSTFIELDSIZE,f_len)
            try:
                c.perform() #pycurl.perform() has no return val
            except Exception as e:
                print e
            sleep(0.3)
            
    def writeQ(self,queue,data):
        queue.put(data,1)
#         print "size now",queue.qsize()
    
    def readQ(self,queue):
        val = queue.get(1)
        return val

    def voice_tts(self):
        self.use_cloud(token=self.get_token())  
    
    
    @pyqtSignature("")
    def on_pushButton_clicked(self):
        """
        Slot documentation goes here.
        """
        if self.thread_flag == 0:
            self.start_flag = 1
            record_t = MyThread(self.my_record,(self,),self.my_record.__name__)
            record_t.setDaemon(True)
            record_t.start()
            self.thread_flag = 1
            
    
    @pyqtSignature("")
    def on_pushButton_2_clicked(self):
        """
        Slot documentation goes here.
        """
        if self.thread_flag == 1:
            self.start_flag = 0
            self.thread_flag = 0
            
    @pyqtSignature("")
    def on_radioButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSignature("")
    def on_radioButton_2_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = MainWindow()
    ui.setDaemon(True)
    ui.start()
#     record_t = MyThread(ui.use_cloud,(ui.get_token(),),ui.use_cloud.__name__)
#     record_t.setDaemon(True)
#     record_t.start()
    ui.show()
    sys.exit(app.exec_())


