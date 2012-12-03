#!/usr/bin/env python

from common import lib

class Telephony(lib.LogFilter):
  TAGS = ['PhoneLabSystemAnalysis-Telephony', 'SmsReceiverService']
  
  def __init__(self):  
    self.calls = None
    self.texts = None
    super(Telephony, self).__init__()
    
  def process(self):
    c = CallState()
    t = set([])
    
    for logline in self.generate_loglines():
      if logline.log_tag == 'PhoneLabSystemAnalysis-Telephony' and logline.json.has_key('State'):
        c.add(logline)
      elif logline.log_tag == 'SmsReceiverService' and logline.log_message == "onStart: #1 mResultCode: -1 = Activity.RESULT_OK":
        t.add(Text(logline.device, logline.datetime))
    
    self.calls = c.calls
    self.texts = list(t)
  
  def get_call_counts(self, start_time=None, end_time=None):
    call_counts = {}
    for device in self.devices:
      call_counts[device] = 0
    for call in [c for c in self.calls if ( start_time == None or c.start >= start_time ) and ( end_time == None or c.start < end_time )]:
      call_counts[call.device] += (call.end - call.start).seconds
    return call_counts
  
  def get_text_counts(self, start_time=None, end_time=None):
    text_counts = {}
    for device in self.devices:
      text_counts[device] = 0
    for text in [t for t in self.texts if ( start_time == None or t.datetime >= start_time ) and ( end_time == None or t.datetime < end_time )]:
      text_counts[text.device] += 1
    return text_counts
    
class Call:
  def __init__(self, device, placed, start, end):
    self.device = device
    self.placed = placed
    self.start = start
    self.end = end
  
class Text:
  def __init__(self, device, datetime):
    self.device = device
    self.datetime = datetime
  
  def __attrs(self):
    return (self.device, self.datetime)
  
  def __eq__(self, other):
    return isinstance(other, Text) and self.__attrs() == other.__attrs()
  
  def __hash__(self):
    return hash((self.device, self.datetime)) 
    
class CallState:
  
  def __init__(self):
    self.call_state = {}
    self.calls = []
    
  def add(self, logline):
    if logline.json['State'] == 'CALL_STATE_RINGING':
      self.start_ringing(logline.device, logline.datetime)
    elif logline.json['State'] == 'CALL_STATE_OFFHOOK':
      self.off_hook(logline.device, logline.datetime)
    elif logline.json['State'] == 'CALL_STATE_IDLE':
      self.idle(logline.device, logline.datetime)
  
  def start_ringing(self, device, datetime):
    self.call_state[device] = ('r', datetime)
  
  def is_ringing(self, device):
    if self.has(device) and self.call_state[device][0] == 'r':
      return True
    else:
      return False
    
  def off_hook(self, device, datetime):
    if self.is_ringing(device):
      self.call_state[device] = ('r', datetime)
    else:
      self.call_state[device] = ('p', datetime)
      
  def is_off_hook(self, device):
    if self.has(device) and ( self.call_state[device][0] == 'r' or self.call_state[device][0] == 'p' ):
      return True
    else:
      return False
  
  def is_received(self, device):
    if not self.is_off_hook(device):
      return False
    return self.call_state[device][0] == 'r'
  
  def is_placed(self, device):
    if not self.is_off_hook(device):
      return False
    return self.call_state[device][0] == 'p'
  
  def idle(self, device, datetime):
    if self.is_off_hook(device):
      self.calls.append(Call(device, self.is_placed(device), self.get_time(device), datetime))
    self.call_state[device] = ('i', datetime)
  
  def is_idle(self, device):
    if self.has(device) and self.call_state[device][0] == 'i':
      return True
    else:
      return False
  
  def has(self, device):
    return self.call_state.has_key(device)
  
  def get_time(self, device):
    if self.call_state.has_key(device):
      return self.call_state[device][1]
    else:
      return None