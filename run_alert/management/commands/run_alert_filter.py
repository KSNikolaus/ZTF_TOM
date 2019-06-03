from django.core.management.base import BaseCommand
from tom_alerts.models import BrokerQuery
from tom_alerts.alerts import get_service_class, get_service_classes
from datetime import datetime 
import os
import fastavro
import requests
lightcurve_path = os.environ.get("lightcurve_path")
target_path = os.environ.get("target_path")
import numpy as np
import time
import sys
import shutil
import matplotlib.pyplot as plt
import io
from astropy.time import Time
plt.switch_backend('agg')
import astropy.units as u



def plot_phot(lightcurve,output_name):      
    plt.rc('font', family='serif')
    plt.rc('xtick', labelsize='x-small')
    plt.rc('ytick', labelsize='x-small')
    fig = plt.figure(figsize=(4, 3))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel('HJD-2450000')
    ax.set_ylabel('mag')
    filt_color = {'g':'g','r':'r','i':'k'}   
    for filt in np.unique(lightcurve[:,3]):
        try:
            index = (lightcurve[:,3] == filt) & (lightcurve[:,4]!='1')
            plt.errorbar(lightcurve[index,0].astype(float)-2450000,lightcurve[index,1].astype(float),yerr=lightcurve[index,2].astype(float), fmt='.'+filt_color[str(filt)], label= filt_color[str(filt)])
            
            index = (lightcurve[:,3] == filt) & (lightcurve[:,4]=='1')
            plt.scatter(lightcurve[index,0].astype(float)-2450000,lightcurve[index,1].astype(float),marker='v',c=filt_color[str(filt)],alpha = 0.5)

        except:
            index = lightcurve[:,3] == filt   
            plt.errorbar(lightcurve[index,0].astype(float)-2450000,lightcurve[index,1].astype(float),yerr=lightcurve[index,2].astype(float),fmt='.'+filt_color[str(filt)], label= filt_color[str(filt)])

    plt.gca().invert_yaxis()
    lgd=ax.legend(loc='center left',numpoints=1,bbox_to_anchor=(1.0,0.5))
    plt.savefig(output_name+'.png',bbox_extra_artists=(lgd,), bbox_inches='tight')
        

def save_lightcurve(lightcurve,output_name,object_name):    
    plot_phot(lightcurve,output_name)
    print(output_name)
    np.savetxt(output_name+'.dat', lightcurve.astype(str),fmt='%s')
    name = object_name
    loc = output_name+'.dat'
    locR = lightcurve_path+'Rfilter/'+name+'R.dat'
    locG = lightcurve_path+'Gfilter/'+name+'G.dat'
    lcd = open(loc, 'r')
    lcdr = open(locR, 'w')
    lcdg = open(locG, 'w')
    lclr = []
    lclg = []
    for line in lcd:
        if 'r' in line:
            lclr.append(line)
        if 'g' in line:
            lclg.append(line)

    for idx in range(len(lclr)):
        lcdr.write(lclr[idx].split(' r ')[0]+'\n')

    for idx in range(len(lclg)):
        lcdg.write(lclg[idx].split(' g ')[0]+'\n')

    lcd.close()
    lcdr.close()
    lcdr.close()



def extract_photometry(packet):
    time = []
    mag = []
    emag = []      
    filters = []
    flags = []
    filt_dict = {1:'g',2:'r',3:'i'} 
    previous_measurements = packet['prv_candidates']     
    for index in range(len(previous_measurements)):      
        time.append(previous_measurements[index]['jd'])
        if previous_measurements[index]['magpsf'] == None :       
            mag.append(previous_measurements[index]['diffmaglim'])
            emag.append(0)
            flags.append(1)
        
        else:
            mag.append(previous_measurements[index]['magpsf'])
            emag.append(previous_measurements[index]['sigmapsf'])
            flags.append(0)
        
        filters.append(filt_dict[previous_measurements[index]['fid']]) 
    
    time.append(packet['candidate']['jd'])
    mag.append(packet['candidate']['magpsf'])
    emag.append(packet['candidate']['sigmapsf'])
    filters.append(filt_dict[packet['candidate']['fid']])
    flags.append(0)
    lightcurve = np.c_[time,mag,emag,filters,flags]
        
    return lightcurve

    
def analyze_individual_alert(alert):
    avro_name = alert['avro']   
    response = requests.get(avro_name)
    try:
        freader = fastavro.reader(io.BytesIO(response.content))
        for packet in freader:
            previous_candidates = packet['prv_candidates']
            lightcurve = extract_photometry(packet)
            directory_name = 'plots'
            object_name = alert['objectId']
            save_lightcurve(lightcurve,lightcurve_path+object_name,object_name)      #output

    except:
	    pass



class Command(BaseCommand):
    help = "run an alert query"


    def add_arguments(self, parser):
       parser.add_argument('--query_name', help='indicates name of query to run') 
       #Django doc. -> how parser works: https://docs.djangoproject.com/en/2.2/howto/custom-management-commands/


    def handle(self, *args, **options):
        query = BrokerQuery.objects.get(name=options['query_name'])
        broker_class = get_service_class(query.broker)()
        alerts = broker_class.fetch_alerts(query.parameters_as_dict)
        targetdir = target_path+'targetlist.dat'
        targetlist = open(targetdir ,'r+')
        targetlines = []
        for line in targetlist:
            targetlines.append(line)
        
        for alert in alerts:
            now = datetime.now()
            print(now, alert, '\n')
            analyze_individual_alert(alert)
            if str(alert['objectId']) in str(targetlines):
                pass

            else: 
                alert = broker_class.fetch_alert(alert['lco_id'])
                target = broker_class.to_target(alert)
                target.save()
                broker_class.process_reduced_data(target, alert)
                targetlist.write(alert['objectId']+'\n')
        
        targetlist.close()


