import json
from copy import copy
from channels import *

from autosportlabs.racecapture.geo.geopoint import GeoPoint

MAX_ANALOG_RAW_VALUE = 1023
MIN_ANALOG_RAW_VALUE = 0

class ScalingMap(object):
    def __init__(self, **kwargs):
        points = 5
        raw = []
        scaled = []
        for i in range(points):
            raw.append(0)
            scaled.append(0)
        self.points = points
        self.raw = raw
        self.scaled = scaled
 
    def fromJson(self, mapJson):
        rawJson = mapJson.get('raw', None)
        if rawJson:
            i = 0
            for rawValue in rawJson:
                self.raw[i] = rawValue
                i+=1

        scaledJson = mapJson.get('scal', None)
        if scaledJson:
            i = 0
            for scaledValue in scaledJson:
                self.scaled[i] = scaledValue
                i+=1
                
    def toJson(self):
        mapJson = {}
        rawBins = []
        scaledBins = []
        for rawValue in self.raw:
            rawBins.append(rawValue)
        
        for scaledValue in self.scaled:
            scaledBins.append(scaledValue)
            
        mapJson['raw'] = rawBins
        mapJson['scal'] = scaledBins
        
        return mapJson 
        
    def getVolts(self, mapBin):
        try:
            return (5.0 * self.raw[mapBin]) / 1024.0
        except IndexError:
            print('Index error getting volts')
            return 0
     
    def setVolts(self, mapBin, value):
        try:
            value = float(value)
            raw = value * 204.6
            raw = int(raw)
            raw = MAX_ANALOG_RAW_VALUE if raw >= MAX_ANALOG_RAW_VALUE else raw
            raw = MIN_ANALOG_RAW_VALUE if raw <= MIN_ANALOG_RAW_VALUE else raw
            self.raw[mapBin] = raw
        except IndexError:
            print('Index error setting bin')
            
    def getScaled(self, mapBin):
        try:
            return self.scaled[mapBin]
        except IndexError:
            print('Index error getting scaled value')
            return 0
    
    def setScaled(self, mapBin, value):
        try:
            self.scaled[mapBin] = float(value)
        except IndexError:
            print('Index error setting bin')
            
ANALOG_SCALING_MODE_RAW     = 0
ANALOG_SCALING_MODE_LINEAR  = 1
ANALOG_SCALING_MODE_MAP     = 2

class AnalogChannel(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.channelId = 0
        self.sampleRate = 0
        self.scalingMode = 0
        self.linearScaling = 0
        self.linearOffset = 0
        self.alpha = 0
        self.scalingMap = ScalingMap()
    
    def fromJson(self, json):
        self.channelId = json.get('id', self.channelId)
        self.sampleRate = json.get('sr', self.sampleRate)
        self.scalingMode = json.get('scalMod', self.scalingMode)
        self.linearScaling = json.get('scaling', self.linearScaling)
        self.linearOffset = json.get('offset', self.linearOffset)
        self.alpha = json.get('alpha', self.alpha)
        mapJson = json.get('map', None)
        if mapJson:
            self.scalingMap.fromJson(mapJson)
        self.stale = False
        
    def toJson(self):
        channelJson = {}
        channelJson['id'] = self.channelId
        channelJson['sr'] = self.sampleRate
        channelJson['scalMod'] = self.scalingMode
        channelJson['scaling'] = self.linearScaling
        channelJson['offset'] = self.linearOffset
        channelJson['alpha'] = self.alpha
        channelJson['map'] = self.scalingMap.toJson()
        return channelJson
    
ANALOG_CHANNEL_COUNT = 8

class AnalogConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = ANALOG_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(AnalogChannel())   

    def fromJson(self, analogCfgJson):
        for i in range (self.channelCount):
            analogChannelJson = analogCfgJson.get(str(i), None)
            if analogChannelJson:
                self.channels[i].fromJson(analogChannelJson)

    def toJson(self):
        analogCfgJson = {}
        for i in range(ANALOG_CHANNEL_COUNT):
            analogChannel = self.channels[i]
            analogCfgJson[str(i)] = analogChannel.toJson()
        return {'analogCfg':analogCfgJson}
            
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value    
    
class ImuChannel(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.sampleRate = 0
        self.mode = 0
        self.chan = 0
        self.zeroValue = 0
        self.alpha = 0

    def fromJson(self, imuChannelJson):
        self.sampleRate =  imuChannelJson.get('sr', self.sampleRate)
        self.mode = imuChannelJson.get('mode', self.mode)
        self.chan = imuChannelJson.get('chan', self.chan)
        self.zeroValue = imuChannelJson.get('zeroVal', self.zeroValue)
        self.alpha = imuChannelJson.get('alpha', self.alpha)
        self.stale = False
        
    def toJson(self):
        jsonCfg = {}
        jsonCfg['sr'] = self.sampleRate
        jsonCfg['mode'] = self.mode
        jsonCfg['chan'] = self.chan
        jsonCfg['zeroVal'] = self.zeroValue
        jsonCfg['alpha'] = self.alpha
        return jsonCfg
    
IMU_CHANNEL_COUNT = 4
IMU_ACCEL_CHANNEL_IDS   = [0,1,2]
IMU_GYRO_CHANNEL_IDS    = [3]
IMU_MODE_DISABLED       = 0
IMU_MODE_NORMAL         = 1
IMU_MODE_INVERTED       = 2

class ImuConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = IMU_CHANNEL_COUNT
        self.channels = []
        
        for i in range(self.channelCount):
            self.channels.append(ImuChannel())

    def fromJson(self, imuConfigJson):
        for i in range (self.channelCount):
            imuChannelJson = imuConfigJson.get(str(i), None)
            if imuChannelJson:
                self.channels[i].fromJson(imuChannelJson)
                
    def toJson(self):
        imuCfgJson = {}
        for i in range (self.channelCount):
            imuChannel = self.channels[i]
            imuCfgJson[str(i)]=imuChannel.toJson()
            
        return {'imuCfg':imuCfgJson}
        
            
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
          
class LapConfigChannel(object):
    def __init__(self, **kwargs):
        self.sampleRate = 0
        self.id = 0
        
    def fromJson(self, jsonCfg):
        if jsonCfg:
            self.sampleRate = int(jsonCfg.get('sr', self.sampleRate))
            self.id = int(jsonCfg.get('id', self.id))
        
    def toJson(self):
        return {'id': self.id, 'sr':self.sampleRate}
        
        
class LapConfig(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.lapCount = LapConfigChannel()
        self.lapTime = LapConfigChannel()
        self.predTime = LapConfigChannel()
        self.sector = LapConfigChannel()
        self.sectorTime = LapConfigChannel()

    def fromJson(self, jsonCfg):
        if jsonCfg:
            lapCount = jsonCfg.get('lapCount')
            if lapCount:
                self.lapCount.fromJson(lapCount) 
                
            lapTime = jsonCfg.get('lapTime')
            if lapTime: 
                self.lapTime.fromJson(lapTime)
                
            predTime = jsonCfg.get('predTime')
            if predTime: 
                self.predTime.fromJson(predTime)
                
            sector = jsonCfg.get('sector')
            if sector: 
                self.sector.fromJson(sector)
                
            sectorTime = jsonCfg.get('sectorTime')
            if sectorTime: 
                self.sectorTime.fromJson(sectorTime)
            
            self.stale = False
            
    def toJson(self):
        lapCfgJson = {'lapCfg':{
                                  'lapCount': self.lapCount.toJson(),
                                  'lapTime': self.lapTime.toJson(),
                                  'predTime': self.predTime.toJson(),
                                  'sector': self.sector.toJson(),
                                  'sectorTime': self.sectorTime.toJson()
                                  }
                        }
        return lapCfgJson
          
class GpsConfig(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.sampleRate = 0
        self.positionEnabled = False
        self.speedEnabled = False
        self.distanceEnabled = False
        self.timeEnabled = False
        self.satellitesEnabled = False

    def fromJson(self, json):
        if json:
            self.sampleRate = int(json.get('sr', self.sampleRate))
            self.positionEnabled = int(json.get('pos', self.positionEnabled))
            self.speedEnabled = int(json.get('speed', self.speedEnabled))
            self.timeEnabled = int(json.get('time', self.timeEnabled))
            self.distanceEnabled = int(json.get('dist', self.timeEnabled))
            self.satellitesEnabled = int(json.get('sats', self.satellitesEnabled))
            self.stale = False
            
    def toJson(self):
        gpsJson = {'gpsCfg':{
                              'sr' : self.sampleRate,
                              'pos' : self.positionEnabled,
                              'speed' : self.speedEnabled,
                              'time' : self.timeEnabled,
                              'dist' : self.distanceEnabled,
                              'sats' : self.satellitesEnabled
                              }
                    }
                   
        return gpsJson
        
    
TIMER_CHANNEL_COUNT = 3

class TimerChannel(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.channelId = 0
        self.sampleRate = 0
        self.mode = 0
        self.divider = 0
        self.pulsePerRev = 0
        self.slowTimer = 0
        
    def fromJson(self, timerJson):
        if (timerJson):
            self.channelId = timerJson.get('id', self.channelId)
            self.sampleRate = timerJson.get('sr', self.sampleRate)
            self.mode = timerJson.get('mode', self.mode)
            self.divider = timerJson.get('div', self.divider)
            self.pulsePerRev = timerJson.get('ppr', self.pulsePerRev)
            self.slowTimer = timerJson.get('st', self.slowTimer)
            self.stale = False
            
    def toJson(self):
        timerJson = {}
        timerJson['id'] = self.channelId
        timerJson['sr'] = self.sampleRate
        timerJson['mode'] = self.mode
        timerJson['ppr'] = self.pulsePerRev
        timerJson['div'] = self.divider
        timerJson['st'] = self.slowTimer
        return timerJson

class TimerConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = TIMER_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(TimerChannel())   

    def fromJson(self, json):
        for i in range (self.channelCount):
            timerChannelJson = json.get(str(i), None)
            if timerChannelJson:
                self.channels[i].fromJson(timerChannelJson)
    
    def toJson(self):
        timerCfgJson = {}
        for i in range(TIMER_CHANNEL_COUNT):
            timerChannel = self.channels[i]
            timerCfgJson[str(i)] = timerChannel.toJson()
        return {'timerCfg':timerCfgJson}
        
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
        
class GpioChannel(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.channelId = 0
        self.sampleRate = 0
        self.mode = 0
        
    def fromJson(self, json):
        if (json):
            self.channelId = json.get('id', self.channelId)
            self.sampleRate = json.get('sr', self.sampleRate)
            self.mode = json.get('mode', self.mode)
            self.stale = False
            
    def toJson(self):
        gpioJson = {}
        gpioJson['sr'] = self.sampleRate
        gpioJson['id'] = self.channelId
        gpioJson['mode'] = self.mode
        return gpioJson
         
GPIO_CHANNEL_COUNT = 3

class GpioConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = GPIO_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(GpioChannel())   

    def fromJson(self, json):
        for i in range (self.channelCount):
            channelJson = json.get(str(i), None)
            if channelJson:
                self.channels[i].fromJson(channelJson)
                
    def toJson(self):
        gpioCfgJson = {}
        for i in range(GPIO_CHANNEL_COUNT):
            gpioChannel = self.channels[i]
            gpioCfgJson[str(i)] = gpioChannel.toJson()
        return {'gpioCfg':gpioCfgJson}
        
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
    
class PwmChannel(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.channelId = 0
        self.sampleRate = 0
        self.outputMode = 0
        self.loggingMode = 0
        self.startupPeriod = 0
        self.startupDutyCycle = 0
        
    def fromJson(self, pwmChannelJson):
        if (pwmChannelJson):
            self.channelId = pwmChannelJson.get('id', self.channelId)
            self.sampleRate = pwmChannelJson.get('sr', self.sampleRate)
            self.outputMode = pwmChannelJson.get('outMode', self.outputMode)
            self.loggingMode = pwmChannelJson.get('logMode', self.loggingMode)
            self.startupDutyCycle = pwmChannelJson.get('stDutyCyc', self.startupDutyCycle)
            self.startupPeriod = pwmChannelJson.get('stPeriod', self.startupPeriod)
            self.stale = False
            
    def toJson(self):
        pwmChannelJson = {}
        pwmChannelJson['id'] = self.channelId
        pwmChannelJson['sr'] = self.sampleRate
        pwmChannelJson['outMode'] = self.outputMode
        pwmChannelJson['logMode'] = self.loggingMode
        pwmChannelJson['stDutyCyc'] = self.startupDutyCycle
        pwmChannelJson['stPeriod'] = self.startupPeriod
        return pwmChannelJson

PWM_CHANNEL_COUNT = 4   

class PwmConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = PWM_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(PwmChannel())   

    def fromJson(self, json):
        for i in range (self.channelCount):
            channelJson = json.get(str(i), None)
            if channelJson:
                self.channels[i].fromJson(channelJson)

    def toJson(self):
        pwmCfgJson = {}
        for i in range(PWM_CHANNEL_COUNT):
            pwmChannel = self.channels[i]
            pwmCfgJson[str(i)] = pwmChannel.toJson()
        return {'pwmCfg':pwmCfgJson}
        
    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False
    
    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value
        
CONFIG_SECTOR_COUNT = 20
        
TRACK_TYPE_CIRCUIT  = 0
TRACK_TYPE_STAGE    = 1

CONFIG_SECTOR_COUNT_CIRCUIT = 19
CONFIG_SECTOR_COUNT_STAGE = 18

class Track(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.trackType = TRACK_TYPE_CIRCUIT
        self.sectorCount = CONFIG_SECTOR_COUNT
        self.startLine = GeoPoint()
        self.finishLine = GeoPoint()
        self.sectors = []
    
    def fromJson(self, trackJson):
        if trackJson:
            self.trackType = trackJson.get('type', self.trackType)
            sectorsJson = trackJson.get('sec', None)
            del self.sectors[:]
            
            if self.trackType == TRACK_TYPE_CIRCUIT:
                self.startLine.fromJson(trackJson.get('sf', None))
                sectorCount = CONFIG_SECTOR_COUNT_CIRCUIT
            else:
                self.startLine.fromJson(trackJson.get('st', self.startLine))
                self.finishLine.fromJson(trackJson.get('fin', self.finishLine))
                sectorCount = CONFIG_SECTOR_COUNT_STAGE
    
            returnedSectorCount = len(sectorsJson)
            if sectorsJson:
                for i in range(sectorCount):
                    sector = GeoPoint()
                    if i < returnedSectorCount:
                        sectorJson = sectorsJson[i]
                        sector.fromJson(sectorJson)
                    self.sectors.append(sector)
            self.sectorCount = sectorCount
            self.stale = False
        
    @classmethod
    def fromTrackMap(cls, trackMap):
        t = Track()
        t.trackType = TRACK_TYPE_STAGE if trackMap.finishPoint else TRACK_TYPE_CIRCUIT
        t.startLine = copy(trackMap.startFinishPoint)
        t.finishLine = copy(trackMap.finishPoint)

        maxSectorCount = CONFIG_SECTOR_COUNT_CIRCUIT if t.trackType == TRACK_TYPE_CIRCUIT else CONFIG_SECTOR_COUNT_STAGE
        sectorCount = 0
        for point in trackMap.sectorPoints:
            sectorCount += 1
            if sectorCount > maxSectorCount: break
            t.sectors.append(copy(point))
        return t
        
    def toJson(self):
        sectors = []
        for sector in self.sectors:
            sectors.append(sector.toJson())
        trackJson = {}
        trackJson['sec']  = sectors
        trackJson['type'] = self.trackType
        
        if self.trackType == TRACK_TYPE_STAGE:
            trackJson['st'] = self.startLine.toJson()
            trackJson['fin'] = self.finishLine.toJson()
        else:
            trackJson['sf'] = self.startLine.toJson()
        return trackJson
        
class TrackConfig(object):
    def __init__(self, **kwargs):
        self.stale=False
        self.track = None
        self.radius = 0
        self.autoDetect = 0
        
    def fromJson(self, trackConfigJson):
        if trackConfigJson:
            self.radius = trackConfigJson.get('rad', self.radius)
            self.autoDetect = trackConfigJson.get('autoDetect', self.autoDetect)
            
            trackJson = trackConfigJson.get('track', None)
            if trackJson:
                self.track = Track()
                self.track.fromJson(trackJson)
            self.stale = False
                    
    def toJson(self):
        trackCfgJson = {}
        trackCfgJson['rad'] = self.radius
        trackCfgJson['autoDetect'] = 1 if self.autoDetect else 0 
        trackCfgJson['track'] = self.track.toJson()

        return {'trackCfg':trackCfgJson}

class TracksDb(object):
    tracks = None
    def __init__(self, **kwargs):
        self.stale = False
        self.tracks = []
        
    def fromJson(self, tracksDbJson):
        if tracksDbJson:
            del self.tracks[:]
            tracksNode = tracksDbJson.get('tracks')
            if tracksNode:
                for trackNode in tracksNode:
                    track = Track()
                    track.fromJson(trackNode)
                    self.tracks.append(track)
            self.stale = False

    def toJson(self):
        tracksJson = []
        tracks = self.tracks
        for track in tracks:
            tracksJson.append(track.toJson())
        return {"trackDb":{'size':len(tracks),'tracks': tracksJson}}
  
class CanConfig(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.enabled = False
        self.baudRate = 0
    
    def fromJson(self, canCfgJson):
        self.enabled = True if canCfgJson.get('en', self.enabled) == 1 else False 
        self.baudRate = canCfgJson.get('baud', self.baudRate)
        self.stale = False
        
    def toJson(self):
        canCfgJson = {}
        canCfgJson['en'] = 1 if self.enabled else 0
        canCfgJson['baud'] = self.baudRate
        return {'canCfg':canCfgJson}        
    
        
class PidConfig(object):
    def __init__(self, **kwargs):
        self.channelId = 0
        self.sampleRate = 0
        self.pidId = 0
        
    def fromJson(self, json):
        self.channelId = json.get("id", self.channelId)
        self.sampleRate = json.get("sr", self.sampleRate)
        self.pid = json.get("pid", self.pidId)
        
    def toJson(self):
        pidJson = {}
        pidJson['id'] = self.channelId
        pidJson['sr'] = self.sampleRate
        pidJson['pid'] = self.pidId
        return pidJson

OBD2_CONFIG_MAX_PIDS = 20

class Obd2Config(object):
    pids = []
    enabled = False
    def __init__(self, **kwargs):
        self.stale = False
        self.enabled = False
    
    def fromJson(self, obd2CfgJson):
        self.enabled = obd2CfgJson.get('en', self.enabled) 
        pidsJson = obd2CfgJson.get("pids", None)
        if pidsJson:
            del self.pids[:]
            for pidJson in pidsJson:
                pid = PidConfig()
                pid.fromJson(pidJson)
                self.pids.append(pid)
                
    def toJson(self):
        pidsJson = []
        pidCount = len(self.pids)
        pidCount = pidCount if pidCount <= OBD2_CONFIG_MAX_PIDS else OBD2_CONFIG_MAX_PIDS
        
        for i in range(pidCount):
            pidsJson.append(self.pids[i].toJson())
            
        obd2Json =  {'obd2Cfg':{'en': 1 if self.enabled else 0, 'pids':pidsJson }}
        return obd2Json
        
class LuaScript(object):
    script = ""
    def __init__(self, **kwargs):
        self.stale = False
        pass
            
    def fromJson(self, jsonScript):
        self.script = jsonScript['data']
        self.stale = False
        
    def toJson(self):
        scriptJson = {"scriptCfg":{'data':self.script,'page':None}}
        return scriptJson
        
class BluetoothConfig(object):
    name = ""
    passKey = ""
    btEnabled = False
    def __init__(self, **kwargs):
        pass

    def fromJson(self, btCfgJson):
        self.btEnabled = btCfgJson['btEn'] == 1
        self.name = btCfgJson.get('name', self.name)
        self.passKey = btCfgJson.get('pass', self.passKey)
        
    def toJson(self):
        btCfgJson = {}
        btCfgJson['btEn'] = 1 if self.btEnabled else 0
        btCfgJson['name'] = self.name
        btCfgJson['passKey'] = self.passKey
        return btCfgJson 

class CellConfig(object):
    cellEnabled = False
    apnHost = ""
    apnUser = ""
    apnPass = ""
    def __init__(self, **kwargs):
        pass
    
    def fromJson(self, cellCfgJson):
        self.cellEnabled = cellCfgJson['cellEn'] == 1
        self.apnHost = cellCfgJson.get('apnHost', self.apnHost)
        self.apnUser = cellCfgJson.get('apnUser', self.apnUser)
        self.apnPass = cellCfgJson.get('apnPass', self.apnUser)

    def toJson(self):
        cellConfigJson = {}
        cellConfigJson['cellEn'] = 1 if self.cellEnabled else 0
        cellConfigJson['apnHost'] = self.apnHost
        cellConfigJson['apnUser'] = self.apnUser
        cellConfigJson['apnPass'] = self.apnPass
        return cellConfigJson        
    
class TelemetryConfig(object):
    deviceId = ""
    backgroundStreaming = 0
    
    def fromJson(self, telCfgJson):
        self.deviceId = telCfgJson.get('deviceId', self.deviceId)
        self.backgroundStreaming = True if telCfgJson.get('bgStream', 0) == 1 else False 
        
    def toJson(self):
        telCfgJson = {}
        telCfgJson['deviceId'] = self.deviceId
        telCfgJson['bgStream'] = 1 if self.backgroundStreaming else 0
        return telCfgJson
    
class ConnectivityConfig(object):
    stale = False
    bluetoothConfig = BluetoothConfig()
    cellConfig = CellConfig()
    telemetryConfig = TelemetryConfig()
    
    def fromJson(self, connCfgJson):
        btCfgJson = connCfgJson.get('btCfg')
        if btCfgJson:
            self.bluetoothConfig.fromJson(btCfgJson)
            
        cellCfgJson = connCfgJson.get('cellCfg')
        if cellCfgJson:
            self.cellConfig.fromJson(cellCfgJson)
            
        telCfgJson = connCfgJson.get('telCfg')
        if telCfgJson:
            self.telemetryConfig.fromJson(telCfgJson)
        self.stale = False
        
    def toJson(self):
        connCfgJson = {'btCfg' : self.bluetoothConfig.toJson(),
                       'cellCfg' : self.cellConfig.toJson(),
                       'telCfg' : self.telemetryConfig.toJson()}
        
        return {'connCfg':connCfgJson}


class VersionConfig(object):
    major = 0
    minor = 0
    bugfix = 0
    def __init__(self, **kwargs):
        pass
    
    def toString(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.bugfix)
    
    def fromJson(self, versionJson):
        self.major = versionJson.get('major', self.major)
        self.minor = versionJson.get('minor', self.minor)
        self.bugfix = versionJson.get('bugfix', self.bugfix)
        
    def toJson(self):
        versionJson = {'major': self.major, 'minor': self.minor, 'bugfix': self.bugfix}
        return {'ver': versionJson}
        
class RcpConfig(object):
    loaded = False
    def __init__(self, **kwargs):
        
        self.versionConfig = VersionConfig()
        self.analogConfig = AnalogConfig()
        self.imuConfig = ImuConfig()
        self.gpsConfig = GpsConfig()
        self.lapConfig = LapConfig()
        self.timerConfig = TimerConfig()
        self.gpioConfig = GpioConfig()
        self.pwmConfig = PwmConfig()
        self.trackConfig = TrackConfig()
        self.connectivityConfig = ConnectivityConfig()
        self.canConfig = CanConfig()
        self.obd2Config = Obd2Config()
        self.scriptConfig = LuaScript()
        self.trackDb = TracksDb()
        self.channels = Channels()

    @property
    def stale(self):
        return  (self.analogConfig.stale or
                self.imuConfig.stale or
                self.gpsConfig.stale or
                self.lapConfig.stale or
                self.timerConfig.stale or
                self.gpioConfig.stale or
                self.pwmConfig.stale or
                self.trackConfig.stale or
                self.connectivityConfig.stale or
                self.canConfig.stale or
                self.obd2Config.stale or
                self.scriptConfig.stale or
                self.trackDb.stale or
                self.channels.stale)
    
    @stale.setter
    def stale(self, value):
        self.analogConfig.stale = value
        self.imuConfig.stale = value
        self.gpsConfig.stale = value
        self.lapConfig.stale = value
        self.timerConfig.stale = value
        self.gpioConfig.stale = value
        self.pwmConfig.stale = value
        self.trackConfig.stale = value
        self.connectivityConfig.stale = value
        self.canConfig.stale = value
        self.obd2Config.stale = value
        self.scriptConfig.stale = value
        self.trackDb.stale = value
        self.channels.stale = value
        
    def fromJson(self, rcpJson):
        if rcpJson:
            rcpJson = rcpJson.get('rcpCfg', None)
            if rcpJson:
                versionJson = rcpJson.get('ver', None)
                if versionJson:
                    self.versionConfig.fromJson(versionJson)
        
                analogCfgJson = rcpJson.get('analogCfg', None)
                if analogCfgJson:
                    self.analogConfig.fromJson(analogCfgJson)
        
                timerCfgJson = rcpJson.get('timerCfg', None)
                if timerCfgJson:
                    self.timerConfig.fromJson(timerCfgJson)
                    
                imuCfgJson = rcpJson.get('imuCfg', None)
                if imuCfgJson:
                    self.imuConfig.fromJson(imuCfgJson)
                    
                lapCfgJson = rcpJson.get('lapCfg', None)
                if lapCfgJson:
                    self.lapConfig.fromJson(lapCfgJson)
                    
                gpsCfgJson = rcpJson.get('gpsCfg', None)
                if gpsCfgJson:
                    self.gpsConfig.fromJson(gpsCfgJson)
                    
                gpioCfgJson = rcpJson.get('gpioCfg', None)
                if gpioCfgJson:
                    self.gpioConfig.fromJson(gpioCfgJson)

                pwmCfgJson = rcpJson.get('pwmCfg', None)
                if pwmCfgJson:
                    self.pwmConfig.fromJson(pwmCfgJson)
                    
                trackCfgJson = rcpJson.get('trackCfg', None)
                if trackCfgJson:
                    self.trackConfig.fromJson(trackCfgJson)
                    
                connectivtyCfgJson = rcpJson.get('connCfg', None)
                if connectivtyCfgJson:
                    self.connectivityConfig.fromJson(connectivtyCfgJson)
                    
                canCfgJson = rcpJson.get('canCfg', None)
                if canCfgJson:
                    self.canConfig.fromJson(canCfgJson)
                    
                obd2CfgJson = rcpJson.get('obd2Cfg', None)
                if obd2CfgJson:
                    self.obd2Config.fromJson(obd2CfgJson)
                
                scriptJson = rcpJson.get('scriptCfg', None)
                if scriptJson:
                    self.scriptConfig.fromJson(scriptJson)
                    
                trackDbJson = rcpJson.get('trackDb', None)
                if trackDbJson:
                    self.trackDb.fromJson(trackDbJson)
                    
                channelsJson = rcpJson.get('channels', None)
                if channelsJson:
                    self.channels.fromJson({'channels':channelsJson})
                    
                print('RCP config version ' + str(self.versionConfig.major) + '.' + str(self.versionConfig.minor) + '.' + str(self.versionConfig.bugfix) + ' Loaded')
                self.loaded = True
    
    def fromJsonString(self, rcpJsonString):
        rcpJson = json.loads(rcpJsonString)
        self.fromJson(rcpJson)
        
    def toJsonString(self, pretty = True):
        return json.dumps(self.toJson(), sort_keys=True, indent=2, separators=(',', ': '))

    def toJson(self):
        rcpJson = {'rcpCfg':{
                             'ver': self.versionConfig.toJson().get('ver'),
                             'gpsCfg':self.gpsConfig.toJson().get('gpsCfg'),
                             'lapCfg':self.lapConfig.toJson().get('lapCfg'),
                             'imuCfg':self.imuConfig.toJson().get('imuCfg'),
                             'analogCfg':self.analogConfig.toJson().get('analogCfg'),
                             'timerCfg':self.timerConfig.toJson().get('timerCfg'),
                             'gpioCfg':self.gpioConfig.toJson().get('gpioCfg'),
                             'pwmCfg':self.pwmConfig.toJson().get('pwmCfg'),
                             'canCfg':self.canConfig.toJson().get('canCfg'),
                             'obd2Cfg':self.obd2Config.toJson().get('obd2Cfg'),
                             'connCfg':self.connectivityConfig.toJson().get('connCfg'),
                             'trackCfg':self.trackConfig.toJson().get('trackCfg'),
                             'scriptCfg':self.scriptConfig.toJson().get('scriptCfg'),
                             'trackDb': self.trackDb.toJson().get('trackDb'),
                             'channels': self.channels.toJson().get('channels')
                             }
                   }
        return rcpJson
