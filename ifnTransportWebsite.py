# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 13:32:03 2022

@author: User
"""

from flask import Flask, request, redirect, url_for
from geopy.geocoders import Nominatim
import osm2ifn as osm
import pandas as pd
import ifnTransport as ifn
from os.path import exists as ex
import json
import requests
app = Flask(__name__)

def get_bbox(city):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(city)
    boundingbox = location.raw
    boundingbox = boundingbox.get("boundingbox")
    south = boundingbox[0]
    north = boundingbox[1]
    west = boundingbox[2]
    east = boundingbox[3]
    bbox = west,east,north,south
    return bbox

def download_OSM(city, roadTypes, isSCC):
    bbox = get_bbox(city)
    nodeFName = "Node "+str(city)+".txt"
    linkFName = "Link "+str(city)+".txt"
    osm.downloadOSMdata(bbox,roadTypes,nodeFName,linkFName,isSCC)
    
def data_osm(city, h, w):
    nodeFName = "Node "+str(city)+".txt"
    linkFName = "Link "+str(city)+".txt"
    dfNode = pd.read_csv(nodeFName, sep=",")
    dfLink = pd.read_csv(linkFName, sep =",")
    
    node1 = dfLink[["Node1"]]
    node1 = node1.set_index("Node1")
    dfNode = dfNode.rename({"NodeID":"Node1"},axis = 1)
    dfNode = dfNode.set_index("Node1")
    node1["X1"] = node1.index.map(dfNode["X"])
    node1["Y1"] = node1.index.map(dfNode["Y"])
    node1 = node1.reset_index()
    dfNode = dfNode.reset_index()
    
    node2 = dfLink[["Node2"]]
    node2 = node2.set_index("Node2")
    dfNode = dfNode.rename({"Node1":"Node2"},axis=1)
    dfNode = dfNode.set_index("Node2")
    node2["X2"] = node2.index.map(dfNode["X"])
    node2["Y2"] = node2.index.map(dfNode["Y"])
    node2 = node2.reset_index()
    
    dfFinal = pd.concat([node1,node2], axis = 1)
    country = get_city_country(city)
    pop = get_city_population(city)
    
    x_max, x_min = dfNode["X"].max(), dfNode["X"].min()
    y_max, y_min = dfNode["Y"].max(), dfNode["Y"].min()
    scale = min(h/(y_max-y_min), w/(x_max-x_min))
    if x_max-x_min < y_max-y_min:
        tx = (w-((x_max-x_min)*scale))/2
        ty = 0
    else:
        tx = 0
        ty = (h-((y_max-y_min)*scale))/2
    
    
    script = ""
    script_capacity = ""
    script_link_speed = ""

    base_script = 'var w = window.innerWidth;\n'+\
                    'var h = window.innerHeight;\n'+\
                    'var city = "City : '+str(city)+'"\n'+\
                    'var country = "Country : '+str(country)+'"\n'+\
                    'var pop = "Population : '+str(pop)+'"\n'+\
                    'var canvas = document.getElementById("myCanvas");\n'+\
                    'canvas.width = 0.98*w;\n'+\
                    'canvas.height = 0.98*h;\n'+\
                    'var margintop = 0.02/2*h;\n'+\
                    'var marginleft = 0.02/2*w;\n'+\
                    'canvas.style.marginTop = margintop.toString()+"px";\n'+\
                    'canvas.style.marginLeft = marginleft.toString()+"px";\n'+\
                    'var ctx = canvas.getContext("2d");\n'+\
                    'ctx.lineWidth = 1;\n'+\
                    'ctx.strokeStyle = col;'
    for x in range(len(dfLink)):
        x1 = (dfFinal["X1"].iloc[x]-x_min)*scale+tx
        x2 = (dfFinal["X2"].iloc[x]-x_min)*scale+tx
        y1 = (dfFinal["Y1"].iloc[x]-y_min)*scale+ty
        y2 = (dfFinal["Y2"].iloc[x]-y_min)*scale+ty
        txt_osm = "ctx.beginPath();\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script += txt_osm
        
        capacity_value = dfLink["Capacity"].iloc[x]
        capacity_max = dfLink["Capacity"].max()
        if capacity_value <= capacity_max/3:
            stroke_capacity = "low"
        elif capacity_value > capacity_max/3 and capacity_value <= capacity_max *2 /3:
            stroke_capacity = "mid"
        else:
            stroke_capacity = "high"
        txt_capacity = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_capacity)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_capacity += txt_capacity
        
        link_speed_value = dfLink["MaxSpeed"].iloc[x]
        link_speed_max = dfLink["MaxSpeed"].max()
        if link_speed_value <= link_speed_max/3:
            stroke_link_speed = "low"
        elif link_speed_value > link_speed_max/3 and link_speed_value <= link_speed_max*2/3:
            stroke_link_speed = "mid"
        else:
            stroke_link_speed = "high"
        txt_speed = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_link_speed)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_link_speed += txt_speed
        
    with open(city+"_osm_basic.js", "w") as f:
        f.write(base_script)
        f.write(script)
    with open(city+"_osm_capacity.js", "w") as f:
        f.write(base_script)
        f.write(script_capacity)
    with open(city+"_osm_link_speed.js","w") as f:
        f.write(base_script)
        f.write(script_link_speed)
        
def get_scenario(city, h, w, bot, top):
    scnfile = "Scenario "+str(city)+".scn"
    txt = "ScenarioName=Base Scenario\n"+\
            "Node=Node "+str(city)+".txt\n"+\
            "Link=Link "+str(city)+".txt\n"+\
            "travelTimeModel=Greenshield\n"+\
            "maxAllowableCongestion=0.9\n"+\
            "calibrationBasis=maxCongestion"
    with open(scnfile, "w", encoding = "utf-8") as f:
        f.write(txt)
    net = ifn.IFN_Transport(scnfile)
    net.runScenario()

def scenario_data(city, h, w, bot, top):
    nodeFName = "Node "+str(city)+".txt"
    linkFName = "Link "+str(city)+".txt"
    csvFName = "Scenario "+str(city)+".csv"
    dfNode = pd.read_csv(nodeFName, sep=",")
    dfLink = pd.read_csv(linkFName, sep =",")
    dfCSV = pd.read_csv(csvFName, sep = ",")
    
    node1 = dfLink[["Node1"]]
    node1 = node1.set_index("Node1")
    dfNode = dfNode.rename({"NodeID":"Node1"},axis = 1)
    dfNode = dfNode.set_index("Node1")
    node1["X1"] = node1.index.map(dfNode["X"])
    node1["Y1"] = node1.index.map(dfNode["Y"])
    node1 = node1.reset_index()
    dfNode = dfNode.reset_index()
    
    node2 = dfLink[["Node2"]]
    node2 = node2.set_index("Node2")
    dfNode = dfNode.rename({"Node1":"Node2"},axis=1)
    dfNode = dfNode.set_index("Node2")
    node2["X2"] = node2.index.map(dfNode["X"])
    node2["Y2"] = node2.index.map(dfNode["Y"])
    node2 = node2.reset_index()
    
    dfFinal = pd.concat([node1,node2], axis = 1)
    
    country = get_city_country(city)
    pop = get_city_population(city)
    rank = get_rank(city)
    
    x_max, x_min = dfNode["X"].max(), dfNode["X"].min()
    y_max, y_min = dfNode["Y"].max(), dfNode["Y"].min()
    
    scale = min(h/(y_max-y_min), w/(x_max-x_min))
    if x_max-x_min < y_max-y_min:
        tx = (w-((x_max-x_min)*scale))/2
        ty = 0
    else:
        tx = 0
        ty = (h-((y_max-y_min)*scale))/2
    script_congestion = ""
    script_link_speed = ""
    script_capacity = ""
    script_flow = ""
    
    base_script = 'var w = window.innerWidth;\n'+\
                    'var h = window.innerHeight;\n'+\
                    'var city = "City : '+str(city)+'";\n'+\
                    'var country = "Country : '+str(country)+'";\n'+\
                    'var pop = "Population : '+str(pop)+'";\n'+\
                    'var ifn_rank = "IFN Rank : '+str(rank)+'";\n'+\
                    'var canvas = document.getElementById("myCanvas");\n'+\
                    'canvas.width = 0.98*w;\n'+\
                    'canvas.height = 0.98*h;\n'+\
                    'var margintop = 0.02/2*h;\n'+\
                    'var marginleft = 0.02/2*w;\n'+\
                    'canvas.style.marginTop = margintop.toString()+"px";\n'+\
                    'canvas.style.marginLeft = marginleft.toString()+"px";\n'+\
                    'var ctx = canvas.getContext("2d");\n'+\
                    'ctx.lineWidth = 1;\n'
    for x in range(len(dfLink)):
        #stroke_color = rgb_to_hex(dfFinal["Congestion"].min(), dfFinal["Congestion"].max(), dfFinal["Congestion"].iloc[x])
        try:
            congestion_value = dfCSV["Congestion"].iloc[x]
            congestion_max = dfCSV["Congestion"].max()
        except:
            print(x)
        if congestion_value <= bot*congestion_max :
            stroke_congestion = "low"
        elif congestion_value > bot*congestion_max and congestion_value <= top*congestion_max:
            stroke_congestion = "mid"
        else:
            stroke_congestion = "high"
        x1 = (dfFinal["X1"].iloc[x]-x_min)*scale+tx
        x2 = (dfFinal["X2"].iloc[x]-x_min)*scale+tx
        y1 = (dfFinal["Y1"].iloc[x]-y_min)*scale+ty
        y2 = (dfFinal["Y2"].iloc[x]-y_min)*scale+ty
        txt_congestion = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_congestion)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_congestion += txt_congestion
        
        link_speed_value = dfCSV["Speed"].iloc[x]
        link_speed_max = dfCSV["Speed"].max()
        if link_speed_value <= bot*link_speed_max:
            stroke_link_speed = "low"
        elif link_speed_value > bot*link_speed_max and link_speed_value <= top*link_speed_max:
            stroke_link_speed = "mid"
        else:
            stroke_link_speed = "high"
        txt_speed = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_link_speed)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_link_speed += txt_speed
        
        capacity_value = dfCSV["Capacity"].iloc[x]
        capacity_max = dfCSV["Capacity"].max()
        if capacity_value <= bot*capacity_max:
            stroke_capacity = "low"
        elif capacity_value > bot*capacity_max and capacity_value <= top*capacity_max:
            stroke_capacity = "mid"
        else:
            stroke_capacity = "high"
        txt_capacity = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_capacity)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_capacity += txt_capacity
        
        flow_value = dfCSV["Speed"].iloc[x]
        flow_max = dfCSV["Speed"].max()
        if flow_value <= bot*flow_max:
            stroke_flow = "low"
        elif flow_value > bot*flow_max and flow_value <= top*flow_max:
            stroke_flow = "mid"
        else:
            stroke_flow = "high"
        txt_flow = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_flow)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_flow += txt_flow
        
        
    with open(city+"_congestion.js", "w") as f:
        f.write(base_script)
        f.write(script_congestion)
    with open(city+"_link_speed.js", "w") as f:
        f.write(base_script)
        f.write(script_link_speed)
    with open(city+"_capacity.js","w") as f:
        f.write(base_script)
        f.write(script_capacity)
    with open(city+"_flow.js","w") as f:
        f.write(base_script)
        f.write(script_flow)
        
def get_rank(city):
    df = pd.read_excel("Sorted.xlsx")["City"].tolist()
    if city not in df:
        return "-"
    else:
        return df.index(city)
    
        
def get_city_country(city):
    geolocator = Nominatim(user_agent = "geoapiExcercises")
    location = geolocator.geocode(city)
    country = location.raw.get("display_name").split(", ")[-1]
    return country
        
def get_city_population(city):
    try:
        geolocator = Nominatim(user_agent = "geoapiExcercises")
        location = geolocator.geocode(city).raw.get("osm_id")
        url = "https://nominatim.openstreetmap.org/details.php?osmtype=R&osmid={}&class=boundary&addressdetails=1&hierarchy=0&group_hierarchy=1&format=json".format(location)
        val = requests.get(url)
        pop = json.loads(val.text).get("extratags").get("population")
        year = json.loads(val.text).get("extratags").get("census:population")
        if ";" in year:
            year = year.split(";")[-1]
        pop_year = str(pop)+" ("+str(year)+")"
    except:
        pop_year = "N/A"
    return pop_year

def compare_data(city1, city2 ,h,w, bot, top):
    nodeFName = "Node "+str(city1)+".txt"
    linkFName = "Link "+str(city1)+".txt"
    csvFName = "Scenario "+str(city1)+".csv"
    dfNode = pd.read_csv(nodeFName, sep=",")
    dfLink = pd.read_csv(linkFName, sep =",")
    dfCSV = pd.read_csv(csvFName, sep = ",")
    
    node1 = dfLink[["Node1"]]
    node1 = node1.set_index("Node1")
    dfNode = dfNode.rename({"NodeID":"Node1"},axis = 1)
    dfNode = dfNode.set_index("Node1")
    node1["X1"] = node1.index.map(dfNode["X"])
    node1["Y1"] = node1.index.map(dfNode["Y"])
    node1 = node1.reset_index()
    dfNode = dfNode.reset_index()
    
    node2 = dfLink[["Node2"]]
    node2 = node2.set_index("Node2")
    dfNode = dfNode.rename({"Node1":"Node2"},axis=1)
    dfNode = dfNode.set_index("Node2")
    node2["X2"] = node2.index.map(dfNode["X"])
    node2["Y2"] = node2.index.map(dfNode["Y"])
    node2 = node2.reset_index()
    
    dfFinal = pd.concat([node1,node2], axis = 1)
    
    country = get_city_country(city1)
    pop = get_city_population(city1)
    rank = get_rank(city1)
    
    x_max, x_min = dfNode["X"].max(), dfNode["X"].min()
    y_max, y_min = dfNode["Y"].max(), dfNode["Y"].min()
    
    scale = min(h/(y_max-y_min), w/(x_max-x_min))
    if x_max-x_min < y_max-y_min:
        tx = (w-((x_max-x_min)*scale))/2
        ty = 0
    else:
        tx = 0
        ty = (h-((y_max-y_min)*scale))/2
    script_congestion = ""
    
    base_script = 'var w = window.innerWidth;\n'+\
                    'var h = window.innerHeight;\n'+\
                    'var city1 = "City : '+str(city1)+'";\n'+\
                    'var country1 = "Country : '+str(country)+'";\n'+\
                    'var pop1 = "Population : '+str(pop)+'";\n'+\
                    'var ifn_rank1 = "IFN Rank : '+str(rank)+'";\n'+\
                    'var canvas = document.getElementById("canvas1");\n'+\
                    'canvas.width = 0.98*w;\n'+\
                    'canvas.height = 0.98*h;\n'+\
                    'var margintop = 0.02/2*h;\n'+\
                    'var marginleft = 0.02/2*w;\n'+\
                    'var ctx = canvas.getContext("2d");\n'+\
                    'ctx.lineWidth = 1;\n'
    for x in range(len(dfLink)):
        #stroke_color = rgb_to_hex(dfFinal["Congestion"].min(), dfFinal["Congestion"].max(), dfFinal["Congestion"].iloc[x])
        congestion_value = dfCSV["Congestion"].iloc[x]
        congestion_max = dfCSV["Congestion"].max()
        if congestion_value <= bot*congestion_max :
            stroke_congestion = "low"
        elif congestion_value > bot*congestion_max and congestion_value <= top*congestion_max:
            stroke_congestion = "mid"
        else:
            stroke_congestion = "high"
        x1 = (dfFinal["X1"].iloc[x]-x_min)*scale+tx
        x2 = (dfFinal["X2"].iloc[x]-x_min)*scale+tx
        y1 = (dfFinal["Y1"].iloc[x]-y_min)*scale+ty
        y2 = (dfFinal["Y2"].iloc[x]-y_min)*scale+ty
        txt_congestion = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_congestion)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_congestion += txt_congestion
    
    with open(city1+"_congestion.js", "w") as f:
        f.write(base_script)
        f.write(script_congestion)
        
        
    
    nodeFName = "Node "+str(city2)+".txt"
    linkFName = "Link "+str(city2)+".txt"
    csvFName = "Scenario "+str(city2)+".csv"
    dfNode = pd.read_csv(nodeFName, sep=",")
    dfLink = pd.read_csv(linkFName, sep =",")
    dfCSV = pd.read_csv(csvFName, sep = ",")
    
    node1 = dfLink[["Node1"]]
    node1 = node1.set_index("Node1")
    dfNode = dfNode.rename({"NodeID":"Node1"},axis = 1)
    dfNode = dfNode.set_index("Node1")
    node1["X1"] = node1.index.map(dfNode["X"])
    node1["Y1"] = node1.index.map(dfNode["Y"])
    node1 = node1.reset_index()
    dfNode = dfNode.reset_index()
    
    node2 = dfLink[["Node2"]]
    node2 = node2.set_index("Node2")
    dfNode = dfNode.rename({"Node1":"Node2"},axis=1)
    dfNode = dfNode.set_index("Node2")
    node2["X2"] = node2.index.map(dfNode["X"])
    node2["Y2"] = node2.index.map(dfNode["Y"])
    node2 = node2.reset_index()
    
    dfFinal = pd.concat([node1,node2], axis = 1)
    
    country = get_city_country(city2)
    pop = get_city_population(city2)
    rank = get_rank(city2)
    
    x_max, x_min = dfNode["X"].max(), dfNode["X"].min()
    y_max, y_min = dfNode["Y"].max(), dfNode["Y"].min()
    
    scale = min(h/(y_max-y_min), w/(x_max-x_min))
    if x_max-x_min < y_max-y_min:
        tx = (w-((x_max-x_min)*scale))/2
        ty = 0
    else:
        tx = 0
        ty = (h-((y_max-y_min)*scale))/2
    script_congestion = ""
    
    base_script = 'var w = window.innerWidth;\n'+\
                    'var h = window.innerHeight;\n'+\
                    'var city2 = "City : '+str(city2)+'";\n'+\
                    'var country2 = "Country : '+str(country)+'";\n'+\
                    'var pop2 = "Population : '+str(pop)+'";\n'+\
                    'var ifn_rank2 = "IFN Rank : '+str(rank)+'";\n'+\
                    'var canvas = document.getElementById("canvas2");\n'+\
                    'canvas.width = 0.98*w;\n'+\
                    'canvas.height = 0.98*h;\n'+\
                    'var margintop = 0.02/2*h;\n'+\
                    'var marginleft = 0.02/2*w;\n'+\
                    'var ctx = canvas.getContext("2d");\n'+\
                    'ctx.lineWidth = 1;\n'
    for x in range(len(dfLink)):
        #stroke_color = rgb_to_hex(dfFinal["Congestion"].min(), dfFinal["Congestion"].max(), dfFinal["Congestion"].iloc[x])
        congestion_value = dfCSV["Congestion"].iloc[x]
        if congestion_value <= bot :
            stroke_congestion = "low"
        elif congestion_value > bot and congestion_value <= top:
            stroke_congestion = "mid"
        else:
            stroke_congestion = "high"
        x1 = (dfFinal["X1"].iloc[x]-x_min)*scale+tx
        x2 = (dfFinal["X2"].iloc[x]-x_min)*scale+tx
        y1 = (dfFinal["Y1"].iloc[x]-y_min)*scale+ty
        y2 = (dfFinal["Y2"].iloc[x]-y_min)*scale+ty
        txt_congestion = "ctx.beginPath();\n"+\
            "ctx.strokeStyle = "+str(stroke_congestion)+";\n"+\
            "ctx.moveTo("+str(x1)+","+str(y1)+");\n"+\
            "ctx.lineTo("+str(x2)+","+str(y2)+");\n"+\
            "ctx.stroke();\n"
        script_congestion += txt_congestion
    
    with open(city2+"_congestion.js", "w") as f:
        f.write(base_script)
        f.write(script_congestion)

@app.route("/", methods = ["POST", "GET"])
def index():
    html = open("index.html").read()
    return html

@app.route("/form", methods = ["POST","GET"])
def form():
    html = open("form.html").read()
    return html

@app.route("/form_compare", methods = ["POST", "GET"])
def compare():
    html = open("form_compare.html").read()
    return html

@app.route("/compare", methods = ["POST", "GET"])
def draw_compare():
    if request.method == "POST":
        w = float(request.form.get("Width"))
        h = float(request.form.get("Height"))
        city1 = request.form.get("City1").title()
        city2 = request.form.get("City2").title()
        bot = float(request.form.get("bot_threshold"))
        top = float(request.form.get("top_threshold"))
    
    if ex(f"Node {city1}.txt") == False:
        download_OSM(city1,["motorway", "trunk", "primary", "secondary", "tertiary"], True)
    if ex(f"Node {city2}.txt") == False:
        download_OSM(city2,["motorway", "trunk", "primary", "secondary", "tertiary"], True)
    
    if ex(f"Scenario {city1}.csv") == False:
        get_scenario(city1, h, w, bot, top)
    if ex(f"Scenario {city2}.csv") == False:
        get_scenario(city2, h, w, bot, top)
    
    compare_data(city1,city2,h,w,bot,top)
    js1 = open(city1+"_congestion.js").read()
    js2 = open(city2+"_congestion.js").read()
    
    draw = open("compare.html").read().replace("//{js1}",js1).replace("//{js2}", js2)
    return draw

@app.route("/scenario", methods = ["POST", "GET"])
def scenario():
    if request.method == "POST":
        w = float(request.form.get("Width"))
        h = float(request.form.get("Height"))
        city = request.form.get("City").title()
        bot = float(request.form.get("bot_threshold"))
        top = float(request.form.get("top_threshold"))
    isSCC = True
    roadTypes = ["motorway", "trunk", "primary", "secondary", "tertiary"]
    if ex("Node {}.txt".format(city)) == False:
        download_OSM(city, roadTypes, isSCC)
    if ex("{}_osm_basic.js".format(city)) == False and ex("Node {}.txt".format(city)) == True:
        data_osm(city, h, w)
    if ex("Scenario {}.csv".format(city)) == False:
        get_scenario(city, h, w, bot, top)
    scenario_data(city,h,w, bot, top)
        

    scn = open("scenario.html").read()
    
    if request.method == "POST":
        selectedValue = city+"_"+request.form.get("choice", "congestion")
        print(selectedValue)
        return redirect (url_for("click_scenario", selectedValue = selectedValue))
    return scn

@app.route("/scenario/<selectedValue>", methods = ["POST", "GET"])
def click_scenario(selectedValue):
    city = selectedValue.split("_")[0]
    js = selectedValue + ".js"
    js = open(js).read()
    draw = open("scenario.html").read().replace("//{js}", js)
    if request.method == "POST":
        selectedValue = city + "_" + request.form.get("choice", "congestion")
        print(selectedValue)
        return redirect (url_for("click_scenario", selectedValue = selectedValue))
    return draw
    
app.run(host="localhost", port = 5000)