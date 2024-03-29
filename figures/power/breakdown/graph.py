#!/usr/bin/env python

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from power.lib import * #@UnusedWildImport
from statistics.lib import * #@UnusedWildImport

colors = {'Display': 'coral',
          'Sleep': 'black',
          'Idle CPU': 'lightgrey',
          'Active CPU': 'darkgrey',
          'Idle Data': 'lightgreen',
          'Active Data': 'green',
          'Phone': 'yellow',
          'Idle Wifi': 'orange',
          'GPS': 'red',
          'Bluetooth': 'purple'}

p = Power.load(verbose=True)
s = Statistic.load(verbose=True)

breakdown = p.component_breakdown()
total = sum(breakdown.values())
for component in breakdown.keys():
  breakdown[component] = (breakdown[component] * 100.0) / total
  
sorted_keys = sorted(breakdown.keys(), key=lambda k: breakdown[k], reverse=True)

fig = plt.figure()
ax = fig.add_subplot(111)

overall_bottom = 0.0
for key in sorted_keys:
  key_total = breakdown[key]
  if colors[key] == 'white':
    linewidth = 0.1
  else:
    linewidth = 0.0
  ax.bar(0.0, key_total, width=8.0, bottom=overall_bottom, linewidth=linewidth, color=colors[key], label="%s (%.1f%%)" % (key, key_total))
  overall_bottom += key_total

device_breakdowns = {}
device_totals = {}
device_times = {}

devices = set(s.experiment_devices)
removing_devices = set([])

for device in devices:
  device_breakdowns[device] = p.component_breakdown(device)
  device_times[device] = p.total_time(device)
  if device_times[device] == 0.0:
    removing_devices.add(device)
    continue
  device_totals[device] = sum(device_breakdowns[device].values())
devices -= removing_devices

sorted_devices = sorted(devices, key=lambda k: device_totals[k], reverse=True)
total_total = sum(device_breakdowns[sorted_devices[0]].values())

for device in sorted_devices:
  for component in device_breakdowns[device].keys():
    device_breakdowns[device][component] = (device_breakdowns[device][component] * 100.0) / device_totals[device]
    
left = 10.0
for device in sorted_devices:
  overall_bottom = 0.0
  breakdown = device_breakdowns[device]
  for key in sorted_keys:
    key_total = breakdown[key]
    if colors[key] == 'white':
      linewidth = 0.1
    else:
      linewidth = 0.0
    ax.bar(left, key_total, width=1.0, bottom=overall_bottom, linewidth=linewidth, color=colors[key], label="__none__")
    overall_bottom += key_total
  left += 1.0

ax.axis(ymin=0.0, ymax=100.0, xmin=0.0, xmax=len(devices) + 50.0)

ax.set_xticks([4,])
ax.set_xticklabels(["Testbed"])
ax.set_yticks(ax.get_yticks()[1:])
ax.set_ylabel('%% of Total')
ax.legend(loc=7, prop={'size': 9})
fig.subplots_adjust(left=0.04, right=0.99, top=0.99, bottom=0.08)
fig.set_size_inches(7.0, 3.5)
fig.savefig('graph.pdf', dpi=300)
