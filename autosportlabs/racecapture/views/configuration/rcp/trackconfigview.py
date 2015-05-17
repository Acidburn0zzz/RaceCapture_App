import kivy
kivy.require('1.8.0')

from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.app import Builder
from helplabel import HelpLabel
from fieldlabel import FieldLabel
from settingsview import *
from utils import *
from valuefield import FloatValueField
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.tracks.tracksview import TrackInfoView, TracksView
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *

TRACK_CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/trackconfigview.kv'

class SectorPointView(BoxLayout):
    geoPoint = None
    def __init__(self, **kwargs):
        super(SectorPointView, self).__init__(**kwargs)
        self.register_event_type('on_config_changed')
        title = kwargs.get('title', None)
        if title:
            self.setTitle(title)

    def on_config_changed(self):
        pass
        
    def setTitle(self, title):
        kvFind(self, 'rcid', 'title').text = title
        
    def setPoint(self, geoPoint):
        self.ids.lat.text = str(geoPoint.latitude)
        self.ids.lon.text = str(geoPoint.longitude)
        self.geoPoint = geoPoint
        
    def on_lat(self, instance, value):
        if self.geoPoint:
            self.geoPoint.latitude = float(value)
            self.dispatch('on_config_changed')
    
    def on_lon(self, instance, value):
        if self.geoPoint:
            self.geoPoint.longitude = float(value)
            self.dispatch('on_config_changed')
            
class EmptyTrackDbView(BoxLayout):
    def __init__(self, **kwargs):
        super(EmptyTrackDbView, self).__init__(**kwargs)
        
class TrackDbItemView(BoxLayout):
    track = None
    trackInfoView = None
    index = 0
    def __init__(self, **kwargs):
        super(TrackDbItemView, self).__init__(**kwargs)
        track = kwargs.get('track', None)
        self.index = kwargs.get('index', 0)
        trackInfoView = kvFind(self, 'rcid', 'trackinfo')
        trackInfoView.setTrack(track)
        self.track = track
        self.trackInfoView = trackInfoView
        self.register_event_type('on_remove_track')

    def on_remove_track(self, index):
        pass
    
    def removeTrack(self):
        self.dispatch('on_remove_track', self.index)
        
class TrackSelectionPopup(BoxLayout):
    track_browser = None
    def __init__(self, **kwargs):
        super(TrackSelectionPopup, self).__init__(**kwargs)
        self.register_event_type('on_tracks_selected')
        track_manager = kwargs.get('track_manager', None)
        track_browser = kvFind(self, 'rcid', 'browser')
        track_browser.set_trackmanager(track_manager)
        track_browser.init_view()
        self.track_browser = track_browser
        
    def on_tracks_selected(self, selectedTrackIds):
        pass
    
    def confirmAddTracks(self):
        self.dispatch('on_tracks_selected', self.track_browser.selectedTrackIds)        
        
            
class AutomaticTrackConfigScreen(Screen):
    trackDb = None
    tracksGrid = None
    trackManager = None
    TRACK_ITEM_MIN_HEIGHT = 200
    searchRadiusMeters = 2000
    searchBearing = 360
    trackSelectionPopup = None
    def __init__(self, **kwargs):
        super(AutomaticTrackConfigScreen, self).__init__(**kwargs)
        self.tracksGrid = kvFind(self, 'rcid', 'tracksgrid')
        self.register_event_type('on_tracks_selected')
        self.register_event_type('on_modified')
                        
    def on_modified(self, *args):
        pass
                
    def on_config_updated(self, rcpCfg):
        self.trackDb = rcpCfg.trackDb
        self.init_tracks_list()
        
    def on_tracks_updated(self, track_manager):
        self.trackManager = track_manager
        self.init_tracks_list()
    
    def on_tracks_selected(self, instance, selectedTrackIds):
        if self.trackDb:
            failures = False
            for trackId in selectedTrackIds:
                trackMap = self.trackManager.getTrackById(trackId)
                if trackMap:
                    startFinish = trackMap.startFinishPoint
                    if startFinish and startFinish.latitude and startFinish.longitude:
                        track = Track.fromTrackMap(trackMap)
                        self.trackDb.tracks.append(track)
                    else:
                        failures = True
            if failures:
                alertPopup('Cannot Add Tracks', 'One or more tracks could not be added due to missing start/finish points.\n\nPlease check for track map updates and try again.')            
            self.init_tracks_list()
            self.trackSelectionPopup.dismiss()
            self.trackDb.stale = True
            self.dispatch('on_modified')
                    
    def on_add_track_db(self):
        trackSelectionPopup = TrackSelectionPopup(track_manager=self.trackManager)
        popup = Popup(title = 'Add Race Tracks', content = trackSelectionPopup, size_hint=(0.9, 0.9))
        trackSelectionPopup.bind(on_tracks_selected=self.on_tracks_selected)
        popup.open()
        self.trackSelectionPopup = popup
    
    def init_tracks_list(self):
        if self.trackManager and self.trackDb:
            matchedTracks = []
            for track in self.trackDb.tracks:
                matchedTrack = self.trackManager.findTrackByShortId(track.trackId)
                if matchedTrack:
                    matchedTracks.append(matchedTrack)
                    
            grid = kvFind(self, 'rcid', 'tracksgrid')
            grid.clear_widgets()
            if len(matchedTracks) == 0:
                grid.add_widget(EmptyTrackDbView())
                self.tracksGrid.height = dp(self.TRACK_ITEM_MIN_HEIGHT)
            else:
                self.tracksGrid.height = dp(self.TRACK_ITEM_MIN_HEIGHT) * (len(matchedTracks) + 1)
                index = 0
                for track in matchedTracks:
                    trackDbView = TrackDbItemView(track=track, index=index)
                    trackDbView.bind(on_remove_track=self.on_remove_track)
                    trackDbView.size_hint_y = None
                    trackDbView.height = dp(self.TRACK_ITEM_MIN_HEIGHT)
                    grid.add_widget(trackDbView)
                    index += 1
                
            self.disableView(False)
            
    def on_remove_track(self, instance, index):
            try:
                del self.trackDb.tracks[index]
                self.init_tracks_list()
                self.trackDb.stale = True
                self.dispatch('on_modified')
                            
            except Exception as detail:
                print('Error removing track from list ' + str(detail))
                    
    def disableView(self, disabled):
        kvFind(self, 'rcid', 'addtrack').disabled = disabled
        
class ManualTrackConfigScreen(Screen):
    trackCfg = None
    sectorViews = []
    startLineView = None
    finishLineView = None
    separateStartFinish = False

    def __init__(self, **kwargs):
        super(ManualTrackConfigScreen, self).__init__(**kwargs)
        
        sepStartFinish = kvFind(self, 'rcid', 'sepStartFinish') 
        sepStartFinish.bind(on_setting=self.on_separate_start_finish)
        sepStartFinish.setControl(SettingsSwitch())
        
        self.separateStartFinish = False
        sectorsContainer = self.ids.sectors_grid        
        self.sectorsContainer = sectorsContainer
        self.initSectorViews()
            
        sectorsContainer.height = dp(35) * CONFIG_SECTOR_COUNT
        sectorsContainer.size_hint = (1.0, None)
        
        self.register_event_type('on_modified')
                        
    def on_modified(self, *args):
        pass
    
    def on_separate_start_finish(self, instance, value):        
        if self.trackCfg:
            self.trackCfg.track.trackType = 1 if value else 0
            self.trackCfg.stale = True
            self.dispatch('on_modified')            
            self.separateStartFinish = value
            self.updateTrackViewState()
              
    def initSectorViews(self):
        
        sectorsContainer = self.sectorsContainer
        sectorsContainer.clear_widgets()
        
        self.startLineView = kvFind(self, 'rcid', 'startLine')
        self.startLineView.bind(on_config_changed=self.on_config_changed)
        self.finishLineView = kvFind(self, 'rcid', 'finishLine')
        self.finishLineView.bind(on_config_changed=self.on_config_changed)
                                
        self.updateTrackViewState()
            
    def on_config_changed(self, *args):
        self.trackCfg.stale = True
        self.dispatch('on_modified')
                    
    def updateTrackViewState(self):
        if not self.separateStartFinish:
            self.startLineView.setTitle('Start / Finish')
            self.finishLineView.setTitle('- - -')            
            self.finishLineView.disabled = True
        else:
            self.startLineView.setTitle('Start Line')
            self.finishLineView.setTitle('Finish Line')
            self.finishLineView.disabled = False
            
    def on_config_updated(self, rcpCfg):
        trackCfg = rcpCfg.trackConfig
        
        separateStartFinishSwitch = kvFind(self, 'rcid', 'sepStartFinish')
        self.separateStartFinish = trackCfg.track.trackType == TRACK_TYPE_STAGE
        separateStartFinishSwitch.setValue(self.separateStartFinish) 
        
        sectorsContainer = self.sectorsContainer

        sectorsContainer.clear_widgets()
        for i in range(0, trackCfg.track.sectorCount):
            sectorView = SectorPointView(title = 'Sector ' + str(i))
            sectorView.bind(on_config_changed=self.on_config_changed)
            sectorsContainer.add_widget(sectorView)
            sectorView.setPoint(trackCfg.track.sectors[i])
            self.sectorViews.append(sectorView)

        self.startLineView.setPoint(trackCfg.track.startLine)
        self.finishLineView.setPoint(trackCfg.track.finishLine)
        
        self.trackCfg = trackCfg
        self.updateTrackViewState()
            
class TrackConfigView(BaseConfigView):
    trackCfg = None
    trackDb = None
    
    screenManager = None
    manualTrackConfigView = None
    autoConfigView = None
    
    def __init__(self, **kwargs):
        Builder.load_file(TRACK_CONFIG_VIEW_KV)
        super(TrackConfigView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        
        self.manualTrackConfigView = ManualTrackConfigScreen(name='manual')
        self.manualTrackConfigView.bind(on_modified=self.on_modified)
        
        self.autoConfigView = AutomaticTrackConfigScreen(name='auto')
        self.autoConfigView.bind(on_modified=self.on_modified)
        
        screenMgr = kvFind(self, 'rcid', 'screenmgr')
        screenMgr.add_widget(self.manualTrackConfigView)
        self.screenManager = screenMgr
        
        autoDetect = kvFind(self, 'rcid', 'autoDetect') 
        autoDetect.bind(on_setting=self.on_auto_detect)
        autoDetect.setControl(SettingsSwitch())

    def on_tracks_updated(self, track_manager):
        self.autoConfigView.on_tracks_updated(track_manager)
        
    def on_config_updated(self, rcpCfg):
        trackCfg = rcpCfg.trackConfig
        trackDb = rcpCfg.trackDb
        
        autoDetectSwitch = kvFind(self, 'rcid', 'autoDetect')
        autoDetectSwitch.setValue(trackCfg.autoDetect)
        
        self.manualTrackConfigView.on_config_updated(rcpCfg)
        self.autoConfigView.on_config_updated(rcpCfg)
        self.trackCfg = trackCfg
        self.trackDb = trackDb
        
    def on_auto_detect(self, instance, value):
        if value:
            self.screenManager.switch_to(self.autoConfigView)
        else:
            self.screenManager.switch_to(self.manualTrackConfigView)

        if self.trackCfg:
            self.trackCfg.autoDetect = value
            self.trackCfg.stale = True
            self.dispatch('on_modified')
            
            
class GeoPointEditor(BoxLayout):
    channel = None
    rc_api = None
    def __init__(self, **kwargs):
        super(GeoPointEditor, self).__init__(**kwargs)
        self.point = kwargs.get('point', None)
        self.rc_api = kwargs.get('rc_api', None)
        self.register_event_type('on_point_edited')        
        self.init_view()
        
    def init_view(self):
        pass
            
    def on_latitude(self, instance, value):
        self.channel.name = value
        
    def on_longitude(self, instance, value):
        self.channel.units = value
    
    def on_close(self):
        self.dispatch('on_point_edited')        
            