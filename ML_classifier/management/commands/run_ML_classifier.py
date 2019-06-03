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

from LIA import models
from LIA import microlensing_classifier


def classify_lightcurves():

    #print('classify_lightcurves')
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
        location = fileDirectoryClassifiedR+str(ml_pred)+str(filename)

        np.savetxt(location+'.dat', data,fmt='%s')

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
        location = fileDirectoryClassifiedG+str(ml_pred)+str(filename)

        np.savetxt(location+'.dat', data,fmt='%s')

    return class_results








class Command(BaseCommand):
    help = "classify lightcurves"

    def handle(self, *args, **options):
        class_results = classify_lightcurves()











