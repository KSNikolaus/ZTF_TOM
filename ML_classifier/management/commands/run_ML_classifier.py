from django.core.management.base import BaseCommand
from datetime import datetime 
import os
import requests
import numpy as np
import time
import sys
from tom_targets.models import Target
from natsort import natsorted
import matplotlib.pyplot as plt
from matplotlib.pyplot import text
from astropy.time import Time
plt.switch_backend('agg')
import astropy.units as u
lightcurve_path = os.environ.get("lightcurve_path")
target_path = os.environ.get("target_path")
features_path = os.environ.get("features_path")

from LIA import models
from LIA import microlensing_classifier
from pyLIMA import event
from pyLIMA import telescopes
from pyLIMA import microlmodels


def classify_lightcurves():
    dataFileNamesR = []
    dataFileNamesG = []
    fileDirectoryR = lightcurve_path+'Rfilter/'
    fileDirectoryG = lightcurve_path+'Gfilter/'
    fileDirectoryClassifiedR = lightcurve_path+'classified/Rfilter/'
    fileDirectoryClassifiedG = lightcurve_path+'classified/Gfilter/'

    for f in os.listdir(fileDirectoryR):
        if f.endswith('.dat'):
            dataFileNamesR.append(f)

    for f in os.listdir(fileDirectoryG):
        if f.endswith('.dat'):
            dataFileNamesG.append(f)

    dataFileNamesR = natsorted(dataFileNamesR)
    dataFileNamesG = natsorted(dataFileNamesG)
    rf, pca = models.create_models(features_path+'all_features.txt', features_path+'pca_features.txt')
    class_results = []

    for filename in dataFileNamesR:
        data=np.loadtxt(fileDirectoryR+filename, usecols=np.arange(0,3))
        mjd=[float(i) for i in data[:,0]]
        mag=[float(i) for i in data[:,1]]
        magerr=[float(i) for i in data[:,2]]

        sosort = np.array([mjd,mag,magerr]).T
        sosort = sosort[sosort[:,0].argsort(),]
        mjd = sosort[:,0]
        mag = sosort[:,1]
        magerr = sosort[:,2]+0.0001

        prediction, ml_pred = microlensing_classifier.predict(mag, magerr, rf, pca)[0:2]
        #print('filename: ', filename, 'prediction: ', prediction, 'ml_pred = ', ml_pred)
        result = [filename, prediction, ml_pred]
        class_results.append(result)
        ml_pred = str(ml_pred)
        ml_pred = ml_pred.replace("[", "")
        ml_pred = ml_pred.replace("]", "")
        location = fileDirectoryClassifiedR+ml_pred+str(filename)
        np.savetxt(location, data,fmt='%s')

    for filename in dataFileNamesG:
        data=np.loadtxt(fileDirectoryG+filename, usecols=np.arange(0,3))
        mjd=[float(i) for i in data[:,0]]
        mag=[float(i) for i in data[:,1]]
        magerr=[float(i) for i in data[:,2]]

        sosort = np.array([mjd,mag,magerr]).T
        sosort = sosort[sosort[:,0].argsort(),]
        mjd = sosort[:,0]
        mag = sosort[:,1]
        magerr = sosort[:,2]

        prediction, ml_pred = microlensing_classifier.predict(mag, magerr, rf, pca)[0:2]
        #print('filename: ', filename, 'prediction: ', prediction, 'ml_pred = ', ml_pred)
        result = [filename, prediction, ml_pred]
        class_results.append(result)
        ml_pred = str(ml_pred)
        ml_pred = ml_pred.replace("[", "")
        ml_pred = ml_pred.replace("]", "")
        location = fileDirectoryClassifiedG+ml_pred+str(filename)
        np.savetxt(location, data,fmt='%s')

        targetname = str(filename).replace("R.dat","")
        targetname = targetname.replace("G.dat","")
        print(targetname)
        target = Target.objects.get(name=targetname)
        target.save(extras={'Microlensing probability': {'probability': ml_pred, 'timestamp': datetime.datetime.now()}})

    return class_results



def pyLIMAfit(filename):

    ML_event = event.Event()
    ML_event.name = str(filename).replace(".dat","")
    ML_event.ra = 269.39166666666665 
    ML_event.dec = -29.22083333333333
    
    fileDirectoryR = lightcurve_path+'Rfilter/'+str(filename)
    fileDirectoryG = lightcurve_path+'Gfilter/'+str(filename)
    if ML_event.name.endswith('R'): #color == 'R':
        data_1 = np.loadtxt(fileDirectoryR)
        telescope_1 = telescopes.Telescope(name='LCOGT', camera_filter='R', light_curve_magnitude=data_1)
        ML_event.telescopes.append(telescope_1)

    if ML_event.name.endswith('G'): #color == 'G':
        data_2 = np.loadtxt(fileDirectoryG)
        telescope_2 = telescopes.Telescope(name='LCOGT', camera_filter='G', light_curve_magnitude=data_2)
        ML_event.telescopes.append(telescope_2)

    ML_event.find_survey('LCOGT')
    ML_event.check_event()
    PSPL_model = microlmodels.create_model('PSPL', ML_event)
    ML_event.fit(PSPL_model,'DE')
    ML_event.fits[-1].produce_outputs()
    try:
        initial_parameters = [ getattr(ML_event.fits[-2].outputs.fit_parameters, key) for 
                              key in ML_event.fits[-2].outputs.fit_parameters._fields[:4]]

        PSPL_model.parameters_guess = initial_parameters
        ML_event.fit(PSPL_model,'LM')
        ML_event.fits[-1].produce_outputs()

    except:
        pass

    output1 = plt.figure(1)
    plt.savefig(lightcurve_path+'pyLIMA_fits/'+str(filename).replace(".dat","")+'_pyLIMA_fit.png')
    output2 = plt.figure(2)
    plt.savefig(lightcurve_path+'pyLIMA_fits/'+str(filename).replace(".dat","")+'_pyLIMA_parameters.png')
    plt.close('all')

    return 0



class Command(BaseCommand):
    help = "classify lightcurves"

    def handle(self, *args, **options):
        class_results = classify_lightcurves()  #[[filename, prediction, ml_pred], [filename, prediction, ml_pred],...]
        for idx in range(len(class_results)):
            targetname = str(class_results[idx][0]).replace(".dat","")
            if targetname.endswith('R'):
                targetname = targetname.replace("R","")

            if targetname.endswith('G'):
                targetname = targetname.replace("G","")

            


            #targetname = str(filename).replace("R.dat","")
            #targetname = targetname.replace("G.dat","")
            #print(targetname)
            #target = Target.objects.get(name=targetname)
            #target.save(extras={'Microlensing probability': ml_pred})

            nothing = 0
        
        for idx in range(len(class_results)):
            if class_results[idx][2] > 0.16:
                filename = class_results[idx][0]
                try:                
                    nothing = pyLIMAfit(filename)

                except:
                   print('bad ML probability')

            plt.close('all')













