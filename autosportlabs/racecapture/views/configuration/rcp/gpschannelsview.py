import kivy
kivy.require('1.8.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from samplerateview import *
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *

Builder.load_file('autosportlabs/racecapture/views/configuration/rcp/gpschannelsview.kv')            
            
class GPSChannelsView(BaseConfigView):
    gpsConfig = None
    
    def __init__(self, **kwargs):
        super(GPSChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        kvFind(self, 'rcid', 'sr').bind(on_sample_rate = self.on_sample_rate)

    def setCheckBox(self, gpsCfg, key, active):
        checkbox = kvFind(self, 'rcid', key)
        checkbox.active = active
                
    def onPosActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.positionEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
                    
    def onSpeedActive(self, instance, value):
        if self.gpsConfig:        
            self.gpsConfig.speedEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
                        
    def onDistActive(self, instance, value):
        if self.gpsConfig:        
            self.gpsConfig.distanceEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
                                                
    def onSatsActive(self, instance, value):
        if self.gpsConfig:        
            self.gpsConfig.satellitesEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
                
    def on_sample_rate(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.sampleRate = value
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
                    
    def on_config_updated(self, rcpCfg):
        gpsConfig = rcpCfg.gpsConfig
        
        sampleRate = kvFind(self, 'rcid', 'sr')
        sampleRate.setValue(gpsConfig.sampleRate)
        
        self.setCheckBox(gpsConfig, 'pos', gpsConfig.positionEnabled)
        self.setCheckBox(gpsConfig, 'speed', gpsConfig.speedEnabled)
        self.setCheckBox(gpsConfig, 'dist', gpsConfig.distanceEnabled)
        self.setCheckBox(gpsConfig, 'sats', gpsConfig.satellitesEnabled)
        
        self.gpsConfig = gpsConfig
        