#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import json
import csv
import sys
import arqParametros as arqParam

try:
    ee.Initialize()
    print('The Earth Engine package initialized successfully!')
except ee.EEException as e:
    print('The Earth Engine package failed to initialize!')
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
sys.setrecursionlimit(1000000000)





param = {
    'lsBiomas': ['CAATINGA'],
    'asset_bacias': 'users/diegocosta/caatinga_bh_new',
    'assetBiomas' : "users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas",
    'assetMapbiomasP': 'projects/mapbiomas-workspace/public/collection4_1/mapbiomas_collection41_integration_v1'    
}

imgMapbiomas = ee.Image(param['assetMapbiomasP']).select('classification_2018')
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

#nome das bacias que fazem parte do bioma
nameBacias = [
      '732','741','742','743','744', '745','746','747','751','752',
      '753', '754','755','756','757','758','759','762','763','764','765',
      '766','767','771','772','773', '774', '775','776','777','778',
      '7611','7612','7613','7614','7615','7616', '7617','7618','7619'
]
nameBacias = ['764','778']

arqFeitos = open("ocorrencia/strataCaatinga.csv", 'w+')
text = 'strata_id,pop'
arqFeitos.write(text + '\n')
for _nbacia in nameBacias:

    selectBacia = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', _nbacia)).first()

    imgMapTemp = imgMapbiomas.clip(selectBacia)

    count = imgMapTemp.reduceRegion(
        reducer= ee.Reducer.count(),
        geometry= selectBacia.geometry(),
        scale= 30,
        maxPixels= 1e13
    )
    count = count.values().get(0).getInfo()
    
    text = "{},{}".format(_nbacia, count)
    print(text)
    arqFeitos.write(text + '\n')

arqFeitos.close()