import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.app import Builder
from mappedspinner import MappedSpinner
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseMultiChannelConfigView, BaseChannelView
from autosportlabs.racecapture.config.rcpconfig import *

Builder.load_file('autosportlabs/racecapture/views/configuration/rcp/timerchannelsview.kv')

class PulseChannelsView(BaseMultiChannelConfigView):
    def __init__(self, **kwargs):
        super(PulseChannelsView, self).__init__(**kwargs)
        self.channel_title = 'Timer '
        self.accordion_item_height = 110

    def channel_builder(self, index):
        editor = PulseChannel(id='timer' + str(index), channels=self.channels)
        editor.bind(on_modified=self.on_modified)
        if self.config:
            editor.on_config_updated(self.config.channels[index])
        return editor
    
    def get_specific_config(self, rcp_cfg):
        return rcp_cfg.timerConfig


class TimerModeSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(TimerModeSpinner, self).__init__(**kwargs)
        self.setValueMap({0:'RPM', 1:'Frequency', 2:'Period (ms)', 3:'Period (us)'}, 'RPM')
            
class TimerSpeedSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(TimerSpeedSpinner, self).__init__(**kwargs)
        self.setValueMap({0:'Slow', 1:'Medium', 2:'Fast'}, 'Medium')
    
class PulsePerRevSpinner(MappedSpinner):
    def __init__(self, **kwargs):
        super(PulsePerRevSpinner, self).__init__(**kwargs)
        valueMap = {}
        for i in range (1, 64):
            valueMap[i] = str(i)
        self.setValueMap(valueMap, '1');
    
class PulseChannel(BaseChannelView):
    def __init__(self, **kwargs):
        super(PulseChannel, self).__init__(**kwargs)
                
    def on_pulse_per_rev(self, instance, value):
        if self.channelConfig:
            self.channelConfig.pulsePerRev = int(value)
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                        
    def on_mode(self, instance, value):
        if self.channelConfig:
            self.channelConfig.mode = int(instance.getValueFromKey(value))
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                        
    def on_speed(self, instance, value):
        if self.channelConfig:
            self.channelConfig.speed = int(instance.getValueFromKey(value))
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
                            
    def on_config_updated(self, channel_config):
        
        sample_rate_spinner = kvFind(self, 'rcid', 'sr')
        sample_rate_spinner.setValue(channel_config.sampleRate)
    
        channel_spinner = kvFind(self, 'rcid', 'chanId')
        channel_spinner.setValue(channel_config.name)
        
        mode_spinner = kvFind(self, 'rcid', 'mode')
        mode_spinner.setFromValue(channel_config.mode)
        
        speed_spinner = kvFind(self, 'rcid', 'speed')
        speed_spinner.setFromValue(channel_config.speed)
        
        pulse_per_rev_spinner = kvFind(self, 'rcid', 'ppr')
        pulse_per_rev_spinner.setFromValue(channel_config.pulsePerRev)
        
        self.channelConfig = channel_config

