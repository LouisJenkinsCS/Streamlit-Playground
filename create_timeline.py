# Import libraries to read in a file line-by-line (txt file)
import io
import os
import sys
import time
import datetime
import re


timelineData = {}
datadir = os.getcwd() + '/Arkouda-Benchmark-Data'

# Iterate over all files in the current directory
for filename in os.listdir(datadir):
    if not filename.endswith('32.out'):
        continue
    # print(f"==========================={filename}================================")
    timelineData[filename] = {}
    # Read line-by-line and grab timestamp at beginnning of line...
    with io.open(f'{datadir}/{filename}', 'r', encoding='utf-8') as f:
        t = 0
        for line in f:
            if line.startswith("2021"):
                # Extract timestamp from example: "2021-12-09:11:30:59"
                timestamp = ':'.join(line.split(':')[:2] + [line.split(':')[2][:2]]) + '.' + line.split(".")[1][:6]
                # Convert timestamp to datetime object
                dt = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                # Convert datetime object to UNIX timestamp
                unix_timestamp = time.mktime(dt.timetuple())
                # Extract for example: ">>> getconfig took 0.00025399999999997647 sec"
                # and obtain both the name (i.e. getconfig) and the time (i.e. 0.00025399999999997647)
                # from "2021-12-09:11:31:23 [arkouda_server] main Line 410 INFO [Chapel] <<< getconfig took 0.00025399999999997647 sec"
                ret = re.match("(.*) <<< (.*) took (.*) sec", line)
                if ret is not None:
                    ret = ret.groups()
                    key = ret[1]
                    if ret[1].startswith('shutdown'):
                        key = 'shutdown'

                    if key not in  timelineData[filename]:
                        timelineData[filename][key] = []
                    timelineData[filename][key].append((t, t+int(ret[2])))

                    # Print the name and the time
                    # timeTakenStr = str(int(ret[2]) / 1000000) + "s" if int(ret[2]) >= 1000000 else str(int(ret[2])/1000) + "ms" if int(ret[2]) >= 1000 else ret[2] + "μs"
                    # currentStartTimeStr = str(t / 1000000) + "s" if t >= 1000000 else str(t/1000) + "ms" if t >= 1000 else str(t) + "μs"
                    # endStartTimeStr = str((t+int(ret[2])) / 1000000) + "s" if (t+int(ret[2])) >= 1000000 else str((t+int(ret[2]))/1000) + "ms" if (t+int(ret[2])) >= 1000 else str(t+int(ret[2])) + "μs"
                    # print(f'{ret[1]} took {timeTakenStr} @ ({currentStartTimeStr},{endStartTimeStr})')
                    t += int(ret[2])

# print(timelineData)

import streamlit as st
import plotly.express as px
import pandas as pd

for plotName in timelineData.keys():
    df = pd.DataFrame(
        [dict(Task=t, Start=s, Finish=f) for t, xs in timelineData[plotName].items() for (s,f) in xs]
    )
    df['delta'] = df['Finish'] - df['Start']
    df.sort_values(by=['Start'], inplace=True)
    fig = px.timeline(df, x_start='Start', x_end='Finish', y='Task')
    fig.update_yaxes(autorange="reversed")
    fig.layout.xaxis.type = 'linear'
    fig.data[0].x = df.delta.tolist()
    f = fig.full_figure_for_development(warn=False)
    # Set name of plot to `plotName` as subheading
    st.subheader(plotName)
    st.write(fig)
    st.write(df)
    