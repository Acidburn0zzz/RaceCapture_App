from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent
from autosportlabs.uix.color.colorsequence import ColorSequence
from autosportlabs.racecapture.datastore import Filter
from autosportlabs.racecapture.views.analysis.analysisdata import ChannelData

from installfix_garden_graph import Graph, LinePlot, SmoothLinePlot
from kivy.app import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty

Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

class ChannelPlot(object):
    plot = None
    channel = None
    min_value = 0
    max_value = 0
    lap = None
    sourceref = None
    distance_index = {}
    samples = 0

    def __init__(self, plot, channel, min_value, max_value, sourceref):
        self.plot = plot
        self.channel = channel
        self.min_value = min_value
        self.max_value = max_value
        self.sourceref = sourceref

    def __str__(self):
        return "{}_{}".format(str(self.sourceref), self.channel) 

class LineChart(ChannelAnalysisWidget):
    color_sequence = ObjectProperty(None)
    _channel_plots = {}
    ZOOM_SCALING = 0.02
    TOUCH_ZOOM_SCALING = 0.000001
    
    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)
        self.register_event_type('on_marker')
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_motion=self.on_motion)
        
        self._touches = []
        self._initial_touch_distance = 0
        self._touch_offset = 0
        self._touch_distance = 0

        self.zoom_level = 1
        self.max_distance = 0
        self.current_distance = 0
        self.current_offset = 0
        self.marker_pct = 0

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y
        if self.collide_point(x, y):
            touch.grab(self)
            if len(self._touches) == 1:
                self._initial_touch_distance = self._touches[0].distance(touch)
                self._touch_offset = self.current_offset
                self._touch_distance = self.current_distance
                
            self._touches.append(touch)
                    
            super(LineChart, self).on_touch_down(touch)
            return True
        else:
            super(LineChart, self).on_touch_down(touch)
            return False

    def on_touch_up(self, touch):   
        x, y = touch.x, touch.y

        # remove it from our saved touches
        if touch in self._touches: # and touch.grab_state:
            touch.ungrab(self)
            self._touches.remove(touch)

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            return True
        
    def on_motion(self, instance, event, motion_event):
        if motion_event.x > 0 and motion_event.y > 0 and self.collide_point(motion_event.x, motion_event.y):
            chart = self.ids.chart
            try:
                
                button = motion_event.button
                zoom = self.marker_pct
                zoom_right = 1 / zoom
                zoom_left = 1 / (1 - zoom)
                zoom_left = zoom_left * self.ZOOM_SCALING
                zoom_right = zoom_right * self.ZOOM_SCALING

                if button == 'scrollup':
                    self.current_distance += zoom_right
                    self.current_offset -= zoom_left
                else:
                    if button == 'scrolldown' and self.current_offset < self.current_distance:
                        self.current_distance -= zoom_right
                        self.current_offset += zoom_left

                self.current_distance = self.max_distance if self.current_distance > self.max_distance else self.current_distance
                self.current_offset = 0 if self.current_offset < 0 else self.current_offset
                
                chart.xmax = self.current_distance
                chart.xmin = self.current_offset
            except:
                pass #no scrollwheel support
    
    def on_marker(self, marker_event):
        pass

    def dispatch_marker(self, x, y):
        mouse_x = x - self.pos[0]
        width = self.size[0]
        pct = mouse_x / width
        self.marker_pct = pct
        data_index = self.current_offset + (pct * (self.current_distance - self.current_offset))
        self.ids.chart.marker_x = data_index
        for channel_plot in self._channel_plots.itervalues():
            index = (data_index / self.max_distance) * channel_plot.samples
            marker = MarkerEvent(int(index), channel_plot.sourceref)
            self.dispatch('on_marker', marker)
        
        
    def on_touch_move(self, touch):
        x, y = touch.x, touch.y
        
        if self.collide_point(x, y):
            touches = len(self._touches)
            if touches == 1:
                #regular dragging / updating marker
                self.dispatch_marker(x, y)
            elif touches == 2:
                #handle pinch zoom
                touch1 = self._touches[0]
                touch2 = self._touches[1]
                distance = touch1.distance(touch2)
                delta = distance - self._initial_touch_distance
                delta = delta * (float(self.size[0]) * self.TOUCH_ZOOM_SCALING ) 
                
                #zoom around a dynamic center between two touch points
                touch_center_x = touch1.x + ((touch2.x - touch1.x) / 2)
                width = self.size[0]
                pct = touch_center_x / width
                zoom_right = 1 / pct
                zoom_left = 1 / (1 - pct)
                zoom_left = zoom_left * delta
                zoom_right = zoom_right * delta

                self.current_distance = self._touch_distance - zoom_right
                self.current_offset = self._touch_offset + zoom_left
                
                #Rail the zooming
                self.current_distance = self.max_distance if self.current_distance > self.max_distance else self.current_distance
                self.current_distance = self.current_offset + self.TOUCH_ZOOM_SCALING if self.current_distance < self.current_offset else self.current_distance
                self.current_offset = 0 if self.current_offset < 0 else self.current_offset
                self.current_offset = self.current_distance + self.TOUCH_ZOOM_SCALING if self.current_offset > self.current_distance else self.current_offset

                chart = self.ids.chart
                chart.xmax = self.current_distance
                chart.xmin = self.current_offset
            return True
                        
    def on_mouse_pos(self, x, pos):
        if len(self._touches) > 1:
            return False
        if not self.collide_point(pos[0], pos[1]):
            return False
        
        self.dispatch_marker(pos[0], pos[1])

    def remove_channel(self, channel, ref):
        remove = []
        for channel_plot in self._channel_plots.itervalues():
            if channel_plot.channel == channel and str(ref) == str(channel_plot.sourceref):
                remove.append(channel_plot)
        
        for channel_plot in remove:
            self.ids.chart.remove_plot(channel_plot.plot)
            del(self._channel_plots[str(channel_plot)])

    
    def add_channel(self, channel_name, query_data):
        chart = self.ids.chart
        channel_data_values = query_data[channel_name]
        distance_data_values = query_data['Distance']
        
        key = channel_data_values.channel + str(channel_data_values.source)
        plot = SmoothLinePlot(color=self.color_sequence.get_color(key))
        channel_plot = ChannelPlot(plot, 
                                   channel_data_values.channel, 
                                   channel_data_values.min, 
                                   channel_data_values.max, 
                                   channel_data_values.source)
        chart.add_plot(plot)
        points = []
        distance_index = {}
        max_distance = chart.xmax
        sample_index = 0
        distance_data = distance_data_values.data.values
        channel_data = channel_data_values.data.values 
        for sample in channel_data:
            distance = distance_data[sample_index]
            if distance > max_distance:
                max_distance = distance 
            points.append((distance, sample))
            distance_index[distance] = sample_index
            sample_index += 1
        
        channel_plot.distance_index = distance_index
        channel_plot.samples = sample_index            
        chart.ymin = channel_data_values.min
        chart.ymax = channel_data_values.max
        chart.xmin = 0
        chart.xmax = max_distance
        plot.points = points
        self._channel_plots[str(channel_plot)] = channel_plot
        self.max_distance = max_distance
        self.current_distance = max_distance
    
    def query_new_channel(self, channel, source_ref):
        channel_data = self.datastore.get_channel_data(source_ref, ['Distance', channel])
        self.add_channel(channel, channel_data)        

