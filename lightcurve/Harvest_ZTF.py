import numpy as np
import requests
import os
import time
import sys
import shutil
import matplotlib.pyplot as plt
import fastavro
import io
import datetime
from astropy.time import Time
plt.switch_backend('agg')
from astroquery.vizier import Vizier
import astropy.units as u
import astropy.coordinates as coord
from astropy.coordinates import Angle
vizier = Vizier(columns=['phot_variable_flag'])


def crossmatch_GAIA(ra,dec):
    try:
        match = vizier.query_region(coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg),frame='icrs'),radius=Angle(1, "arcsec"),catalog='I/345/gaia2')[0]
        return match[0][0]

    except:
        return None



def parse_conf_file(conf_file_adress, conf_file_name):
    configpath = os.path.join(conf_file_adress, conf_file_name)
    parameter_dictionary = {}
    
    with open(configpath,'r') as infile:
        for line in infile:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    col = line.split()
            
                    try:
                        parameter_dictionary[col[0]] = col[1]

                    except:   
                        parameter_dictionary[col[0]] = None

    return parameter_dictionary


def find_ztf_alerts(parameter_dictionary, page_number = None):
    request = parameter_dictionary['archive']
    request += '?'

    for index,key in enumerate(parameter_dictionary.keys()):    
        if '__' in key:
            if key == 'jd__gt':            
                time_now = Time(str(datetime.datetime.now()))
                time_limit = time_now.jd-float(parameter_dictionary[key])             
                request += key+'='+str(time_limit)+'&'

            else:
                request += key+'='+parameter_dictionary[key]+'&'

    if page_number: 
        request += 'page='+str(page_number)+'&'

    response = requests.get(request+'format=json').json()

    return response


def find_individual_alert(parameter_dictionary,lco_id):
    request = parameter_dictionary['archive']
    request += str(lco_id)   
    response = requests.get(request+'?format=json').json()

    return response


def analyze_individual_alert2(parameter_dictionary, alert):
    avro_name = alert['avro']   
    response = requests.get(avro_name)

    try:
        freader = fastavro.reader(io.BytesIO(response.content))
        for packet in freader:
            previous_candidates = packet['prv_candidates']
            min_number_points = float(parameter_dictionary['min_number_points'])-1
            if len(previous_candidates)>=min_number_points:
                lightcurve = extract_photometry2(packet)
                directory_name = time.strftime("./%Y_%m_%d/")
                try:
                    os.makedirs(time.strftime(directory_name))
                except:
                    pass

                object_name = alert['objectId']
                save_lightcurve(lightcurve,directory_name+object_name)      #output

    except:
	    pass
     

def analyze_individual_alert(parameter_dictionary, alert):
    directory_name = time.strftime("./%Y_%m_%d/")
    try:
        os.makedirs(time.strftime(directory_name))

    except:
        pass

    object_name = alert['objectId']  
    previous_measurements = alert['prv_candidate']
    min_number_points = float(parameter_dictionary['min_number_points'])-1

    if len(previous_measurements)>=min_number_points:        
	# check GAIA variability flag
        GAIA_flag = crossmatch_GAIA(alert['candidate']['ra'],alert['candidate']['dec'])
        
        if GAIA_flag != 'VARIABLE':
            lightcurve = extract_photometry(alert)
            directory_name = time.strftime("./%Y_%m_%d/")
            
            try:
                os.makedirs(time.strftime(directory_name))
            
            except:
                pass
        
        object_name = alert['objectId']     
        save_lightcurve(lightcurve,directory_name+object_name)      #output
    
    else:
        #import pdb; pdb.set_trace() 
        pass



def save_lightcurve(lightcurve,output_name):    
    plot_phot(lightcurve,output_name)
    np.savetxt(output_name+'.dat', lightcurve.astype(str),fmt='%s')
    

def extract_photometry(alert):
    time = []
    mag = []
    emag = []      
    filters = []
    previous_measurements = alert['prv_candidate']
    for index in range(len(previous_measurements)):
        #import pdb; pdb.set_trace()
        time.append(previous_measurements[index]['candidate']['jd'])
        mag.append(previous_measurements[index]['candidate']['magpsf'])
        emag.append(previous_measurements[index]['candidate']['sigmapsf'])
        filters.append(previous_measurements[index]['candidate']['filter'])
                
    time.append(alert['candidate']['jd'])
    mag.append(alert['candidate']['magpsf'])
    emag.append(alert['candidate']['sigmapsf'])
    filters.append(alert['candidate']['filter'])
    lightcurve = np.c_[time,mag,emag,filters]
        
    return lightcurve


def extract_photometry2(packet):
    time = []
    mag = []
    emag = []      
    filters = []
    flags = []
    filt_dict = {1:'g',2:'r',3:'i'} 
    previous_measurements = packet['prv_candidates']  
    #import pdb; pdb.set_trace()
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
        
    
    
    
if __name__ == '__main__':   
    parameter_dictionary = parse_conf_file('','Harvest_Conf.txt')
    already_parse = []
    ZTF_ALERTS = find_ztf_alerts(parameter_dictionary)
	
    for page_number in range(ZTF_ALERTS['pages']):
        ZTF_alerts = find_ztf_alerts(parameter_dictionary, page_number = page_number+1)
        
        for index, alert in enumerate(ZTF_alerts['results']):
            print(index,alert['objectId'])
        
        if alert['objectId'] in already_parse:
            pass
        
        else:
            one_alert = find_individual_alert(parameter_dictionary,alert['lco_id'])
            analyze_individual_alert2(parameter_dictionary, one_alert)
            already_parse.append(alert['objectId'])
    
    

#import pdb; pdb.set_trace()
        
