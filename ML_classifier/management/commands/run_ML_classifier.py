from django.core.management.base import BaseCommand
from datetime import datetime 
import os
import requests
import numpy as np
import time
import sys
from natsort import natsorted
import matplotlib.pyplot as plt
from matplotlib.pyplot import text
from astropy.time import Time
plt.switch_backend('agg')
import astropy.units as u
lightcurve_path = os.environ.get("lightcurve_path")
target_path = os.environ.get("target_path")
features_path = os.environ.get("features_path")

from pyLIMA import event
from pyLIMA import telescopes
from pyLIMA import microlmodels
from LIA import models
from LIA import microlensing_classifier


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

    return class_results



def pyLIMAfit(filename, color):

    ML_event = event.Event()
    ML_event.name = str(filename).replace(".dat","")
    ML_event.ra = 269.39166666666665 
    ML_event.dec = -29.22083333333333
    
    fileDirectoryR = lightcurve_path+'Rfilter/'+str(filename)
    fileDirectoryG = lightcurve_path+'Gfilter/'+str(filename)
    data_1 = np.loadtxt(fileDirectoryR)
    telescope_1 = telescopes.Telescope(name='LCOGT', camera_filter='R', light_curve_magnitude=data_1)
    data_2 = np.loadtxt(fileDirectoryG)
    telescope_2 = telescopes.Telescope(name='LCOGT', camera_filter='G', light_curve_magnitude=data_2)
    if color == 'R':
        ML_event.telescopes.append(telescope_1)

    if color == 'G':
        ML_event.telescopes.append(telescope_2)

    ML_event.find_survey('LCOGT')
    ML_event.check_event()
    PSPL_model = microlmodels.create_model('PSPL', ML_event)
    ML_event.fit(model_1,'DE')
    ML_event.fits[0].produce_outputs()

    try:
        initial_parameters = [ getattr(ML_event.fits[-2].outputs.fit_parameters, key) for 
                              key in ML_event.fits[-2].outputs.fit_parameters._fields[:4]]

        PSPL_model.parameters_guess = initial_parameters
        ML_event.fit(PSPL_model,'LM')
        ML_event.fits[-1].produce_outputs()

    except:
        pass

    output1 = plt.figure(1)
    plt.savefig('lightcurve_path+str(filename).replace(".dat","")+pyLIMA1.png')
    output2 = plt.figure(2)
    plt.savefig('lightcurve_path+str(filename).replace(".dat","")+pyLIMA2.png')

    
    return 0



class Command(BaseCommand):
    help = "classify lightcurves"

    def handle(self, *args, **options):
        class_results = classify_lightcurves()
        filename = class_results[0]
        nothing = pyLIMAfit(filename, 'G')











