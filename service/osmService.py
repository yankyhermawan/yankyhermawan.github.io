import pandas as pd
import gcsfs
from geopy.geocoders import Nominatim
import requests
import json

fs = gcsfs.GCSFileSystem(project="zeta-embassy-387512")
    

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

def scenario_data(city, h, w):
    gcs_path_csv = f"gs://ifn-database/scenario_{city}.csv"
    gcs_path_node = f"gs://ifn-database/node_{city}.txt"
    gcs_path_link = f"gs://ifn-database/link_{city}.txt"
    dfNode = pd.read_csv(gcs_path_node, sep=",")
    dfLink = pd.read_csv(gcs_path_link, sep=",")
    dfCSV = pd.read_csv(gcs_path_csv, sep=",", usecols=range(16))
    
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
    
    base_script = 'var w = window.innerWidth;\n'+\
                    'var h = window.innerHeight;\n'+\
                    'var city = "City : '+str(city)+'";\n'+\
                    'var country = "Country : '+str(country)+'";\n'+\
                    'var pop = "Population : '+str(pop)+'";\n'+\
                    'var canvas = document.getElementById("myCanvas");\n'+\
                    'canvas.width = 0.98*w;\n'+\
                    'canvas.height = 0.98*h;\n'+\
                    'var margintop = 0.02/2*h;\n'+\
                    'var marginleft = 0.02/2*w;\n'+\
                    'canvas.style.marginTop = margintop.toString()+"px";\n'+\
                    'canvas.style.marginLeft = marginleft.toString()+"px";\n'+\
                    'var ctx = canvas.getContext("2d");\n'+\
                    'ctx.lineWidth = 1;\n'
    ###     LINK CONGESTION
    for x in range(len(dfCSV)):
        congestion_value = dfCSV["Congestion"].iloc[x]       
        if congestion_value <= 0.3 :
            stroke_congestion = "low"
        elif congestion_value > 0.3 and congestion_value <= 0.6:
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
        base_script += txt_congestion
    return base_script