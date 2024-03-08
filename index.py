from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUiType
from os import path
import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QCheckBox,
    QLabel
)
import matplotlib.pyplot as plt
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from os import path
import os
import sys
from scipy.signal import spectrogram, find_peaks
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from scipy.io import wavfile
from PyQt5.QtCore import Qt
from pydub import AudioSegment
import tempfile
import wave
import datetime

FORM_CLASS, _ = loadUiType(
    path.join(path.dirname(__file__), "Equalizer.ui"))


class SignalViewer (pg.PlotWidget):
    def __init__(self, signal_data=[]):
        super().__init__()
        # audio variables
        self.duration = 0 
        self.audio_data = 0
        self.audio_sample_rate = 0
        self.media_content = 0
        self.playback_rate = 1
        self.audio_sample_width = 0
        self.audio_num_of_channels = 0
        self.media_player = QMediaPlayer()
        self.needle = pg.InfiniteLine(
            pos=0, angle=90, movable=False, pen='cyan')  # nnedle of mediaplayer
        # general variables
        self.timer = QTimer(self)
        self.timer_interval = 100
        self.speed_multiplier = 1
        self.playing = True
        self.current_zoom = 1.0
        self.updater = 1
        self.max_zoom_factor = 2.0
        self.min_zoom_factor = 1.0
        self.signal_data = []
        self.plot_item = 0
        self.audio_mode = False
        # non_audio mood variables
        self.data_index = 0
        self.draw_flag=True
    def reset_everything(self):
        # audio variables
        self.duration = 0  # duration of media player
        self.audio_data = 0
        self.audio_sample_rate = 0
        self.media_content = 0
        self.playback_rate = 1
        self.audio_sample_width = 0
        self.audio_num_of_channels = 0
        # Create a QMediaPlayer instance
        self.media_player.stop()
        self.media_player = QMediaPlayer()
        self.needle = pg.InfiniteLine(
            pos=0, angle=90, movable=False, pen='cyan')  # nnedle of mediaplayer
        # general variables
        self.timer.stop()
        self.timer = QTimer(self)
        self.timer_interval = 100
        self.speed_multiplier = 1
        self.playing = True
        self.current_zoom = 1.0
        self.max_zoom_factor = 2.0
        self.min_zoom_factor = 1.0
        self.signal_data.clear()
        self.plot_item = 0
        self.audio_mode = False

        self.getViewBox().setLimits(yMin=None, yMax=None)
        self.getViewBox().setLimits(xMin=None, xMax=None)
        # non_audio mood variables
        self.data_index = 0
        self.draw_flag=True
  

    def playAudio(self, file_path):
        self.audio_mode = True
        self.media_content = QMediaContent(QUrl.fromLocalFile(file_path))
        self.media_player.setMedia(self.media_content)
        self.media_player.setPlaybackRate(self.playback_rate)
        self.media_player.play()

        def on_media_state_changed(state):
            if state == QMediaPlayer.StoppedState:
                self.media_player.setPlaybackRate(self.playback_rate)
                self.media_player.play()
        self.media_player.stateChanged.connect(on_media_state_changed)
        self.timer_interval = 35
        self.timer.start(self.timer_interval)

    def update_needle(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            position = self.media_player.position()
            self.needle.setPos(position/1000)

    def initWaveform(self, file_path):
        audio = AudioSegment.from_mp3(file_path)
        self.audio_num_of_channels = audio.channels
        self.audio_sample_rate = audio.frame_rate
        self.audio_data = audio.get_array_of_samples()
        self.audio_sample_width = audio.sample_width

        num_samples = len(self.audio_data)
        self.duration = (num_samples / self.audio_sample_rate)
        x = np.linspace(0, self.duration, num_samples)
        combined_list = list(zip(x, self.audio_data))
        signal_data = np.array(combined_list)
        self.signal_data = [signal_data]
        self.plot_item = self.plot(pen=pg.mkPen(color='gray'))

        self.setXRange(x[0]-0.1, x[-1]+0.1)
        self.addItem(self.needle)
        self.plot_item.setData(x, self.audio_data)
        self.timer.timeout.connect(self.update_needle)
        self.enableAutoRange("xy")


    def update_signal(self):
        if self.playing:
            if self.signal_data:
                if self.data_index >= len(self.signal_data[0]):
                    self.data_index = 0
                data_chunk = self.signal_data[0][: self.data_index]
                self.plot_item.setData(data_chunk)
                x_values = [sublist[0] for sublist in self.signal_data[0]]
                one_sec_indecation = 0
                for index, value in enumerate(x_values):
                    if value >= 1:
                        one_sec_indecation = index
                        break
                if self.data_index <= one_sec_indecation:
                    self.setXRange(0, 1)
                else:
                    self.setXRange(
                        (x_values[self.data_index] - 1)/self.current_zoom,
                        (x_values[self.data_index])/self.current_zoom)
                    self.getViewBox().setLimits(
                        xMin=0, xMax=x_values[self.data_index]/self.current_zoom+0.1)
                self.data_index += 1

    def draw_csv_signal(self, signal_data):
        self.audio_mode = False

        self.clear()
        self.signal_data = [signal_data]
        self.plot_item = self.plot(pen=pg.mkPen(color='red'))
        self.plot_item.setData(signal_data[:, 0] ,signal_data[:, 1])
        # if self.draw_flag==True:
        #     self.timer.timeout.connect(self.update_signal)
        #     self.timer.start(self.timer_interval)
        #     self.draw_flag=False
        
        # self.data_index = 0
        # # Clear existing plot data
        # # Create a plot item in the viewer and add it to the viewer's plotItem
        # self.plot_item = self.plot(pen="red")
        y_min = np.min(signal_data[:, 1]) * 2
        y_max = np.max(signal_data[:, 1]) * 2
        # Set the Y-axis limits for the viewbox
        self.getViewBox().setLimits(yMin=y_min, yMax=y_max)
        self.setYRange(y_min*0.5, y_max*0.5)

        


    def play(self):
        if self.audio_mode == True:
            self.media_player.play()
        self.playing = True
        self.timer.start(self.timer_interval)

    def pause(self):
        if self.audio_mode == True:
            self.media_player.pause()
        self.playing = False
        self.timer.stop()

    def speedUp(self):
        self.speed_multiplier += 1.5
        self.timer_interval = int(100 / self.speed_multiplier)
        self.timer.start(self.timer_interval)
        if self.audio_mode == True:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.playback_rate = self.playback_rate+0.5
                if self.playback_rate > 2:
                    self.playback_rate = 2
                self.media_player.setPlaybackRate(self.playback_rate)
                self.media_player.play()

    def speedDown(self):
        if self.speed_multiplier > 0.1:
            self.speed_multiplier -= 1.5
            if self.speed_multiplier > 0:
                self.timer_interval = int(100 / self.speed_multiplier)
                self.timer.start(self.timer_interval)
        if self.audio_mode == True:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.playback_rate = self.playback_rate - 0.5
                if self.playback_rate < 0.5:
                    self.playback_rate = 0.5
                self.media_player.setPlaybackRate(self.playback_rate)
                self.media_player.play()

    def zoomIn(self):
        zoom_factor = 1.0 / 1.2
        if self.current_zoom < self.max_zoom_factor:
            self.getViewBox().scaleBy((zoom_factor, zoom_factor))
            self.current_zoom += 0.25

    def zoomOut(self):
        zoom_factor = 1.2
        if self.current_zoom > self.min_zoom_factor:
            self.getViewBox().scaleBy((zoom_factor, zoom_factor))
            self.current_zoom -= 0.25

    def rewind(self):
        if self.audio_mode == False:
            self.update_signal()
            self.data_index = 0
        if self.audio_mode == True:
            # Set the position to the beginning (0 milliseconds)
            self.media_player.setPosition(0)
            self.media_player.play()
        self.speed_multiplier = 1.0
    

class SpectrogramViewer(FigureCanvas):
    def __init__(self, parent=None, spectrogram_data=[]):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.spectrogram_data = spectrogram_data
        self.fs = 0
        self.canvas_visible = True
        super().__init__(self.fig)

    def show_spectrogram(self, fs):
        self.fs = fs

        flat_data = [
            point for sublist in self.spectrogram_data for point in sublist]

        # Calculate the spectrogram
        Sxx, f, t, cax = plt.specgram(flat_data, Fs=fs)

        # Plot the spectrogram
        self.ax.clear()
        self.ax.pcolormesh(t, f, 10 * np.log10(Sxx))
        self.ax.set_xlabel('Time [s]')
        self.ax.set_ylabel('Frequency [Hz]')
        # self.ax.set_ylim(0, 55)

        # Refresh the canvas
        self.draw()

    def hide_spectrogram(self):
        self.canvas_visible = False
        self.setVisible(False)

    def display_spectrogram(self):
        if not self.canvas_visible:
            self.setVisible(True)
            self.canvas_visible = True

class Equalizer():
    def __init__(self):
        self.freq_bins = []
        self.i=0
        
    def apply_equalization(self, time_domain_data, slider_values, freq_ranges, selected_window, selected_width,fft_result,window_list):
       
        selected_width=(selected_width-1)/10
        fft_result = fft_result[:-1]

        N = len(time_domain_data)

        sampling_rate = 1.0 / (time_domain_data[1][0] - time_domain_data[0][0])
        freq_bins = np.fft.rfftfreq(N, 1/sampling_rate)

        # Apply adjustments based on the frequency ranges freq_range
        for i, freq_range in enumerate(freq_ranges):
            range_indices = np.where((freq_bins >= freq_range[0]) & (freq_bins <= freq_range[1]))[0]
            if len(range_indices) > 0:
                valid_indices = range_indices[(range_indices >= 0) & (range_indices < len(fft_result))]
                smoothing_window_array = self.create_window_array(selected_window, freq_range[1] - freq_range[0], len(valid_indices), slider_values[i], freq_range[0],window_list,selected_width)
            
                fft_result[valid_indices] *= smoothing_window_array
        
        fft_result = np.append(fft_result, 0)
        _ = self.create_window_array(selected_window, 1, len(valid_indices), 1,0,window_list,selected_width)
        # Reconstruct the signal using the inverse FFT (iFFT)
        reconstructed_signal = np.fft.irfft(fft_result)

        
        while  len (time_domain_data) !=len (reconstructed_signal) :
            if len (time_domain_data) > len (reconstructed_signal):
                reconstructed_signal = np.append(reconstructed_signal, 0)
            else :
                time_domain_data = np.append(time_domain_data, 0)
                
        # Prepare the time-domain data for the output viewer
        modified_time_domain_data = [
            [point[0], reconstructed_signal[i]] for i, point in enumerate(time_domain_data)]
        return np.array(modified_time_domain_data)
    
    def create_window_array(self, window_type, width, length, slider_value, start,window_list,selected_width):
        stop = start + width
        selected_width = selected_width* width
        mid_point=(start+stop)/2
        mu=mid_point
        sigma=selected_width/4
  
        x = np.linspace(mid_point-(selected_width/2), mid_point+(selected_width/2), length)
        if window_type == "Hamming":
            window = np.hamming(length) *slider_value / 10
        elif window_type == "Hanning":
            window = np.hanning(length) * slider_value / 10
        elif window_type == "Gaussian":
            mid_point=(start +stop)/2
            window= 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
            # window = np.exp(-0.5 * ((x - mid_point) / (0.1 * width)) ** 2) * slider_value / 10
        elif window_type == "Rectangle":
            window = np.where((x > mid_point-(selected_width/2)) & (x < mid_point+(selected_width/2)), 1, 0) * slider_value / 10
            
        else:
            # Default to a rectangular window if the type is unrecognized
            window = np.ones(x)
        
        window_list.append([x,window])       
        return window 

    def fft(self, time_domain_data, frequency_viewer):
        # Extract the y-values from your data
        y_values = [point[1] for point in time_domain_data]
        fft_result = np.fft.rfft(y_values)
        # Assuming evenly spaced data
        sampling_rate = 1.0 / \
            (time_domain_data[1][0] - time_domain_data[0][0])
        n = len(time_domain_data)
        frequency_magnitudes = np.abs(fft_result)
        max_freq=max(frequency_magnitudes)
        frequency_phase = np.angle(fft_result)
        self.freq_bins = np.fft.rfftfreq(n, 1/sampling_rate)
        self.draw_freq_domain(
            self.freq_bins, frequency_magnitudes, frequency_viewer)
        return max_freq, fft_result,self.freq_bins,frequency_magnitudes

    def draw_freq_domain(self, freq_bins, frequency_magnitudes, frequency_viewer):

        frequency_viewer.plot(freq_bins, frequency_magnitudes, pen='r')



class MainApp(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowTitle("Equalizer")
        self.setupUi(self)
    
        self.mode_configurations = {
            "Uniform Range Mode ": {
                "freq_ranges": [
                    [0, 5], [5, 10], [10, 15], [30, 40], [40, 50],
                    [50, 60], [60, 70], [70, 80], [80, 90], [90, 100]
                ],
                " freq_labels ":[ "0:10", "10: 20", "20: 30", "30: 40", "40: 50",
                    "50: 60", "60: 70", "70: 80", "80: 90", "90: 100"],
                
                "play_radiobtn_widget": False,
                "sliders_count": 10
            },
            #ranges lazem teb2a laz2a f ba3d fa khaletha 
            "Animal Sounds Mode ": {
                "freq_ranges": [
                    [0, 1100], [1100, 3000], [3000, 6500], [6500, 22000]
                    #frog       bird          cricket       bat 
                ],
                
                "play_radiobtn_widget": True,
                "sliders_count": 4 ,
                " freq_labels ":["frog","bird","cricket","bat"]
            },
           
            "Musical Instrument Mode ": {
                "freq_ranges": [
                    [0, 1000], [1000, 2000], [2000, 4000], [4000, 14000]
                ],
                
                "play_radiobtn_widget": True,
                "sliders_count": 4 ,
                " freq_labels ":["flute","guitar","drums","violin"]
            },
            "ECG Abnormal Mode ": {
                "freq_ranges": [
                    [0, 40], [0,1] ,[83, 125],[125, 166]
                ],
                " freq_labels ":[ "0 : 40", "Ventrical Fibrillation",  "83 : 125" , "125 : 166" ],
                
                "play_radiobtn_widget": False,
                "sliders_count": 4
            }
            
            
        }
        self.freq_labels=[]
        # Get the selected mode from the combo box
        self.selected_mode = self.mode_combobox.currentText()

        # Access configurations based on the selected mode

        self.freq_ranges=[[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0]] 
        self.i=0
        self.signal_data = []
        self.sliders = []
        self.original_data=[]
        self.max_freq=0
        self.slider_values=[]
        self.frequency_magnitudes=[]
        self.freq_bins=[]
        self.fft_result=[]
        self.smoothing_window=[]
        self.input_viewer = SignalViewer("input time ")
        self.frequency_viewer = SignalViewer()
        self.output_viewer = SignalViewer("output time ")
        self.input_spectrogram = SpectrogramViewer("input frequency ")
        self.output_spectrogram = SpectrogramViewer("output frequency")
        self.selected_mode = 'Uniform Range Mode '
        self.selected_window = 'rectangle'
        self.viewer_layout = QHBoxLayout(self.viewer_widget)
        self.viewer_layout.addWidget(self.input_viewer)
        self.viewer_layout.addWidget(self.output_viewer)
        self.spectogram_layout = QHBoxLayout(self.spectrogram_widget)
        self.spectogram_layout.addWidget(self.input_spectrogram)
        self.spectogram_layout.addWidget(self.output_spectrogram)
        self.slider_layout = QHBoxLayout(self.sliders_widget)
        self.freq_widget.setMinimumSize(0, 350)
        self.frequency_layout = QVBoxLayout(self.freq_widget)
        self.frequency_layout.addWidget(self.frequency_viewer)
        self.frequency_layout.addWidget(self.sliders_widget)
        self.hamming_viewer = SignalViewer("selected mode")
        self.label = QLabel("selcted window")
        self.hamming_layout = QVBoxLayout(self.hamming_widget)
        self.hamming_layout.addWidget(self.label)
        self.hamming_layout.addWidget(self.haaming_combobox)
        self.hamming_layout.addWidget(self.hamming_viewer)
        self.hamming_widget.setMaximumSize(300, 500)
        self.hamming_viewer.setMinimumSize(300, 200)
        self.hamming_viewer.setXRange(-1,11)
        self.hamming_slider = QSlider()
        self.hamming_slider.setOrientation(1)
        self.hamming_slider.setMinimum(1)
        self.hamming_slider.setMaximum(11)
        self.hamming_slider.setValue(1)
        self.hamming_layout.addWidget(self.hamming_slider)
        self.spectrogram_show_layout = QHBoxLayout(
            self.spectrogram_show_widget)
        self.show_spectrogram_checkbox = QCheckBox("Show Spectrogram : ")
        self.show_spectrogram_checkbox.setStyleSheet(
            "QCheckBox { color: white; }")
        self.show_spectrogram_checkbox.setChecked(True)
        self.spectrogram_show_layout.addWidget(self.show_spectrogram_checkbox)
        self.label1 = QLabel("play :")
        self.label1.setStyleSheet("font-size: 25px;")
        self.play_radiobtn_layout = QVBoxLayout(self.play_radiobtn_widget)
        self.play_input_radio_btn = QRadioButton("play orignal ")
        self.play_output_radio_btn = QRadioButton("play modified ")
        
        self.play_input_radio_btn.setChecked(True)
        self.play_radiobtn_layout.addWidget(self.label1)
        self.play_radiobtn_layout.addWidget(self.play_input_radio_btn)
        self.play_radiobtn_layout.addWidget(self.play_output_radio_btn)
        
        self.show_spectrogram_checkbox.stateChanged.connect(
            self.on_show_spectrogram_checkbox_change)
        self.play_input_radio_btn.toggled.connect(
            self.play_input_radio_btn_toggeled)
        self.play_output_radio_btn.toggled.connect(
            self.play_output_radio_btn_toggled)
        self.actionUpload.triggered.connect(self.load_signal)
        self.actionUpload.triggered.connect(self.modify_sliders_ui)
        # self.hamming_viewer.draw_hamming(10, 1, 5, number_of_point=1000)
        self.playBtn.hide()
        self.playBtn.clicked.connect(self.play_viewers)
        self.pauseBtn.clicked.connect(self.pause_viewers)
        self.zoomInBtn.clicked.connect(self.zoomIn_viewers)
        self.zoomOutBtn.clicked.connect(self.zoomOut_viewers)
        self.speedUpBtn.clicked.connect(self.speedUp_viewers)
        self.slowDownBtn.clicked.connect(self.slowDown_viewers)
        self.rewindBtn.clicked.connect(self.rewind_viewers)
        
        self.applyEqualizerBtn.clicked.connect(self.equalize)
        self.applyEqualizerBtn.clicked.connect(self.rewind_viewers)
        self.applyEqualizerBtn.clicked.connect(
            self.update_drawing)
        self.mode_combobox.currentIndexChanged.connect(self.mode_changed)
        
        # self.haaming_combobox.currentIndexChanged.connect(
        #     self.equalize)
       
        self.haaming_combobox.currentIndexChanged.connect(
            self.update_drawing)

        if len(self.signal_data) == 0:
                self.hamming_slider.valueChanged.connect(self.update_drawing)
        
        self.mode_changed()
        
        self.equalizer = Equalizer()

    def play_output_radio_btn_toggled(self):
        self.output_viewer.play()
        self.input_viewer.pause()

    def play_input_radio_btn_toggeled(self):
        self.output_viewer.pause()
        self.input_viewer.play()



    def equalize(self):
        if  len(self.fft_result) != 0:
            self.slider_values = [slider.value() for slider in self.sliders]
            # Get the selected window type and width from the UI
            selected_window = self.haaming_combobox.currentText()
            width = self.hamming_slider.value()
            self.max_freq,self.fft_result,self.freq_bins,self.frequency_magnitudes=self.equalizer.fft(
                        self.original_data, self.frequency_viewer)
            self.smoothing_window=[] #clear the list 
            new_signal= self.equalizer.apply_equalization(self.original_data, self.slider_values, self.freq_ranges, selected_window, width,self.fft_result,self.smoothing_window)
            self.selected_mode = self.mode_combobox.currentText()
            if self.selected_mode == "Uniform Range Mode " or self.selected_mode == "ECG Abnormal Mode ":
                self.output_viewer.draw_csv_signal(new_signal)
                self.output_spectrogram.spectrogram_data = new_signal
                self.output_spectrogram.show_spectrogram(fs=1000)
                # self.output_viewer.setYRange(*self.input_viewer.getViewBox().viewRange()[1])
                # self.input_viewer.rewind()
            else:
                self.input_viewer.pause()
                # Sample audio data (replace this with your actual audio data)
                sample_rate = self.input_viewer.audio_sample_rate
                audio_data = new_signal
                # Specify the WAV file parameters
                self.i +=1
                file_path = f"output_{self.i}.wav"
                n_channels = self.input_viewer.audio_num_of_channels
                sample_width = self.input_viewer.audio_sample_width
                n_frames = len(audio_data)
                comptype = 'NONE'
                compname = 'not compressed'
                # Open the WAV file for writing
                with wave.open(file_path, 'w') as wave_file:
                    wave_file.setnchannels(n_channels)
                    wave_file.setsampwidth(sample_width)
                    wave_file.setframerate(2*sample_rate)
                    wave_file.setnframes(n_frames)
                    wave_file.setcomptype(comptype, compname)
                    # Convert audio data to bytes and write to the WAV file
                    audio_bytes = (audio_data).astype(np.int16).tobytes()
                    wave_file.writeframes(audio_bytes)
                # Create QMediaContent from the temporary file URL
                audio = AudioSegment.from_mp3(file_path)
                audio_data = audio.get_array_of_samples()
                self.output_viewer.clear()
                self.output_viewer.initWaveform(file_path)
                self.output_viewer.playAudio(file_path)
                self.play_output_radio_btn.setChecked(True)
                self.play_output_radio_btn_toggled()
                self.output_spectrogram.spectrogram_data = new_signal
                self.output_spectrogram.show_spectrogram(
                    fs=audio.frame_rate*0.5)  # Assuming fs=1000, modify as needed

    def on_show_spectrogram_checkbox_change(self, state):
        if state == Qt.Checked:  # Check for the checked state
            self.input_spectrogram.display_spectrogram()
            self.output_spectrogram.display_spectrogram()

        else:
            self.input_spectrogram.hide_spectrogram()
            self.output_spectrogram.hide_spectrogram()

         
    def modify_sliders_ui(self):
        self.selected_mode = self.mode_combobox.currentText()

        if self.selected_mode in self.mode_configurations:
            
            config = self.mode_configurations[self.selected_mode]
            
            if len(self.original_data) != 0:
                self.freq_ranges = config["freq_ranges"]
            self.create_sliders(config["sliders_count"])
            
            if "play_radiobtn_widget" in config:
                if config["play_radiobtn_widget"]:
                    self.play_radiobtn_widget.show()
                else:
                    self.play_radiobtn_widget.hide()
        
    def mode_changed(self):
        self.input_viewer.reset_everything()
        self.output_viewer.reset_everything()
        self.clear_all()
        self.modify_sliders_ui()
        # if self.selected_window =="Gaussian":
        #     self.hamming_slider.setMaximum(21)
        #     self.hamming_slider.setValue(11)

    def clear_all(self):
        self.input_viewer.clear()
        self.output_viewer.clear()
        self.frequency_viewer.clear()
        self.input_spectrogram.ax.clear()
        self.output_spectrogram.ax.clear()
        self.input_spectrogram.draw()
        self.output_spectrogram.draw()
        self.original_data=[]
        self.signal_data=[]
        self.freq_ranges=[[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0],[0, 0]] 
        self.smoothing_window=[]
        self.i=0
        self.max_freq=0
        self.frequency_magnitudes=[]
        self.freq_bins=[]
        self.fft_result=[]
        

    def create_sliders(self, num_sliders):
        self.sliders = []
        
        for i in range(self.slider_layout.count()):
            widget = self.slider_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        

        for i in range(num_sliders):
            slider_widget=QWidget()
            slider_layout=QVBoxLayout(slider_widget)
            vertical_slider = QSlider()
            vertical_slider.setOrientation(2)
            vertical_slider.setMinimum(0)  # Set the minimum value to 0
            # Set the maximum value to 20 (since 2 * 10 = 20)
            vertical_slider.setMaximum(20)
            vertical_slider.setSingleStep(1)
            vertical_slider.setValue(10)
            vertical_slider.setMinimumHeight(100)
            slider_layout.addWidget(vertical_slider)
            self.slider_layout.addWidget(slider_widget)
            if len(self.original_data) != 0:
                label_corresponding_freq = QLabel(self.mode_configurations[f'{self.selected_mode}'][' freq_labels '][i])
                slider_layout.addWidget(label_corresponding_freq)
            self.sliders.append(vertical_slider)
            
            label = QLabel(f"Value: {vertical_slider.value()/10.0}", self)
            self.slider_layout.addWidget(label)
            vertical_slider.valueChanged.connect(
                lambda value, label=label: label.setText(f"Value: {value/10.0}"))
            vertical_slider.valueChanged.connect(self.update_drawing)

    def load_signal(self):
        self.clear_all()
        self.slider_values=[]
        self.slider_values = [slider.value() for slider in self.sliders]
        # Get the selected window type and width from the UI
        selected_window = self.haaming_combobox.currentText()
        width = self.hamming_slider.value()
        self.hamming_slider.valueChanged.connect(
                self.update_drawing)
        self.selected_mode = self.mode_combobox.currentText()
        if self.selected_mode == "Uniform Range Mode " or self.selected_mode == "ECG Abnormal Mode ":
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Signal",
                "",
                "CSV Files (*.csv);;All Files (*)",
                options=options,
            )
            if file_path:
                signal_data = np.loadtxt(file_path, delimiter=",", skiprows=1)
                self.original_data = signal_data.copy()
                self.input_viewer.draw_csv_signal(signal_data)
                self.input_spectrogram.spectrogram_data = signal_data
                self.input_spectrogram.show_spectrogram(fs=1000)
                self.max_freq,self.fft_result,self.freq_bins,self.frequency_magnitudes=self.equalizer.fft(
                    signal_data, self.frequency_viewer)
                self.modify_sliders_ui()
                _= self.equalizer.apply_equalization(self.original_data, self.slider_values, self.freq_ranges, selected_window, width,self.fft_result,self.smoothing_window)
                self.update_drawing()



        else:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Audio File",
                "",
                "Audio Files (*.wav *.mp3 *.ogg);;All Files (*)",
                options=options,
            )
            if file_path:

                audio = AudioSegment.from_mp3(file_path)
                sample_width = audio.sample_width
                # Get the sample rate of the audio
                sample_rate = audio.frame_rate

                # Get the audio data as a NumPy array
                audio_data = audio.get_array_of_samples()
                num_samples = len(audio_data)

                duration = (num_samples / sample_rate)
                x = np.linspace(0, duration, num_samples)
                self.input_viewer.initWaveform(file_path)
                combined_list = list(zip(x, audio_data))
                audio_signal = np.array(combined_list)
                self.original_data = audio_signal.copy()
                self.input_spectrogram.spectrogram_data = audio_signal
                self.input_viewer.playAudio(file_path)
                self.input_spectrogram.show_spectrogram(fs=sample_rate)
                self.max_freq,self.fft_result,self.freq_bins,self.frequency_magnitudes=self.equalizer.fft(
                    self.original_data, self.frequency_viewer)
                self.modify_sliders_ui()
                _= self.equalizer.apply_equalization(self.original_data, self.slider_values, self.freq_ranges, selected_window, width,self.fft_result,self.smoothing_window)
                self.update_drawing()
                self.input_viewer.enableAutoRange("xy")

    def play_viewers(self):
        self.playBtn.hide()
        self.pauseBtn.show()
        if self.play_input_radio_btn.isChecked()==True:
            self.input_viewer.play()
        elif self.play_output_radio_btn.isChecked()==True:
            self.output_viewer.play()

            

    def pause_viewers(self):
        self.playBtn.show()
        self.pauseBtn.hide()
        self.input_viewer.pause()
        self.output_viewer.pause()

    def zoomIn_viewers(self):
        self.input_viewer.zoomIn()
        self.output_viewer.zoomIn()

    def zoomOut_viewers(self):
        self.input_viewer.zoomOut()
        self.output_viewer.zoomOut()

    def speedUp_viewers(self):
        self.input_viewer.speed_multiplier = self.output_viewer.speed_multiplier
        self.input_viewer.speedUp()
        self.output_viewer.speedUp()

    def slowDown_viewers(self):
        self.input_viewer.speedDown()
        self.output_viewer.speedDown()

    def rewind_viewers(self):
        self.playBtn.hide()
        self.pauseBtn.show()

        if self.selected_mode =='Musical Instrument Mode ' or self.selected_mode =="Animal Sounds Mode ":
            self.input_viewer.rewind()
            self.output_viewer.rewind()
            if self.play_input_radio_btn.isChecked():
                self.input_viewer.play()
                self.output_viewer.pause()
            else:
                self.input_viewer.pause()
                self.output_viewer.play() 
     

    def update_drawing(self):
        self.slider_values=[]
        self.smoothing_window=[]
        width = self.hamming_slider.value()
        selected_window = self.haaming_combobox.currentText()

        self.frequency_viewer.clear()
        self.hamming_viewer.clear()
       
        self.slider_values = [slider.value() for slider in self.sliders]
        
        if  len(self.fft_result) != 0:
            _= self.equalizer.apply_equalization(self.original_data, self.slider_values, self.freq_ranges, selected_window, width,self.fft_result,self.smoothing_window)
            self.equalizer.draw_freq_domain(self.freq_bins,self.frequency_magnitudes,self.frequency_viewer)
            self.hamming_viewer.plot(self.smoothing_window[-1][0],self.smoothing_window[-1][1],pen='g')
            self.hamming_viewer.setXRange(0,1)
            self.smoothing_window = self.smoothing_window[:-1]

            for i , smoothing_window in enumerate(self.smoothing_window):
                self.frequency_viewer.plot(smoothing_window[0],smoothing_window[1]*(self.slider_values[i]*self.max_freq/10),pen='g')

    def exit_program(self):
        sys.exit()

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()