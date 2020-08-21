#!/usr/bin/env python2
# -*- coding: utf-8 -*-

'''
#SCRIPT DE CLASSIFICACAO POR BACIA
#Produzido por Geodatin - Dados e Geoinformacao
#DISTRIBUIDO COM GPLv2
'''

import ee 
import gee
import sys

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
    'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV7_filter/CA_col5_v7v2_2205',
    # 'inputAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/classificacoes/classesV11/',
    # 'inputAsset': 'projects/mapbiomas-workspace/public/collection4_1/mapbiomas_collection41_integration_v1',
    # 'inputAsset': "projects/mapbiomas-workspace/public/collection5/mapbiomas_collection50_integration_v1",
    # 'inputAsset': 'projects/mapbiomas-workspace/COLECAO5/classificacao/',
    'classMapB': [3, 4, 5, 9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33,36,39,41],
    'classNew': [3, 4, 3, 3,12,12,21,21,21,21,12,22,22,22,22,33,29,22,33,12,33,21,21,21],
    'collection': '5.0',
    'geral':  True,
    'isImg': True,  
    'inBacia': False,
    'version': '-3',
    'sufixo': '_col5_ver_v7v2_2205',
    # 'sufixo': '_version',  
    'assetBacia': "users/nerivaldogeo/bacias_caatinga_f",
    'assetBiomas': 'projects/mapbiomas-workspace/AUXILIAR/biomas_IBGE_250mil',
    'listaNameBacias': ['741','742','744', '745','746','749','751','752','753','754','755','756','757','758',
                        '759','76111','76116','7612','7613','7614','7615','7616', '7617','7618','7619','762',
                        '763','764','765','766','767','771','772','773', '774', '775','776','777','778'],
    'biome': 'CAATINGA', 
    'source': 'geodatin',
    'scale': 30,
    'driverFolder': 'AREA-EXPORT', 
    'prefImg' : 'RF_BACIA_',
    'sufImg' : '_RF-v3_baciaC5',
    'lsClasses': [3,4,12,21,22,33,29],
    'numeroTask': 0,
    'numeroLimit': 35,
    'conta' : {
        '0': 'caatinga01'
    }
}

def gerenciador(cont, paramet):
    #0, 18, 36, 54]
    #=====================================#
    # gerenciador de contas para controlar# 
    # processos task no gee               #
    #=====================================#
    numberofChange = [kk for kk in paramet['conta'].keys()]
    
    if str(cont) in numberofChange:

        print("conta ativa >> {} <<".format(paramet['conta'][str(cont)]))        
        gee.switch_user(paramet['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= paramet['numeroTask'], return_list= True)        
    
    elif cont > paramet['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont

##############################################
###     Helper function
###    @param item 
##############################################
def convert2featCollection (item):

    item = ee.Dictionary(item)

    feature = ee.Feature(ee.Geometry.Point([0, 0])).set(
        'classe', item.get('classe')).set("area", item.get('sum'))
        
    return feature

#########################################################################
####     Calculate area crossing a cover map (deforestation, mapbiomas)
####     and a region map (states, biomes, municipalites)
####      @param image 
####      @param geometry
#########################################################################

def calculateArea (image, pixArea, geometry):

    reducer = ee.Reducer.sum().group(1, 'classe')

    optRed = {
        'reducer': reducer,
        'geometry': geometry,
        'scale': param['scale'],
        'maxPixels': 1e12
    }

    areas = pixArea.addBands(image).reduceRegion(**optRed)

    #year = ee.Number(image.get('year'))
    
    areas = ee.List(areas.get('groups')).map(lambda item: convert2featCollection(item))
    areas = ee.FeatureCollection(areas)
    
    return areas

def iterandoXanoImCruda(imgAreaRef, limite, nomeB):

    gBacias = ee.FeatureCollection(param['assetBacia'])      

    if nomeB == '':
        imgMap = ee.List([])

        for nbacia in param['listaNameBacias']:

            bacTemp = gBacias.filter(ee.Filter.eq('nunivotto3', nbacia)).geometry()
            bacTemp = bacTemp.intersection(limite, 1)

            imgTemp = ee.Image( param['inputAsset'] + param['prefImg']  + nbacia + param['sufImg']).clip(bacTemp)
            imgMap = imgMap.add(imgTemp)
        
        imgMap = ee.Image(ee.ImageCollection(imgMap).mosaic())

    else:

        imgMap = ee.Image(param['inputAsset'] + param['prefImg'] + nomeB + param['sufImg']).clip(limite)

    areaGeral = ee.FeatureCollection([])
    
    for year in range(1985, 2020):

        bandAct = "classification_" + str(year)  

        areaTemp = calculateArea (imgMap.select(bandAct), imgAreaRef, limite)
        
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year))

        areaGeral = areaGeral.merge(areaTemp)   
    
    
    return areaGeral


def iterandoXano(imgAreaRef, limite):

    areaGeral = ee.FeatureCollection([])

    for year in range(1985, 2020): 
        
        if param['isImg'] == True:

            imgAct = 'classification_' + str(year)
            imgMap = ee.Image(param['inputAsset']).select(imgAct)
            
            if param['collection'] == '4.1':
                imgMap = imgMap.remap(param['classMapB'], param['classNew'])

        else:            
            
            imgAct = 'CAATINGA-' + str(year) + param['version']
            imgMap = ee.Image(param['inputAsset'] + imgAct).clip(limite)

        areaTemp = calculateArea (imgMap, imgAreaRef, limite)
        
        areaTemp = areaTemp.map( lambda feat: feat.set('year', year))

        areaGeral = areaGeral.merge(areaTemp)

        if param['collection'] == '4.1' and year == 2018:
            break

    return areaGeral

        
#exporta a imagem classificada para o asset
def processoExportar(areaFeat, nameT):  
    
    optExp = {
          'collection': areaFeat, 
          'description': nameT, 
          'folder': param["driverFolder"]        
        }
    
    task = ee.batch.Export.table.toDrive(**optExp)
    task.start() 
    print("salvando ... " + nameT + "..!")      

        

# get raster with area km2
pixelArea = ee.Image.pixelArea().divide(10000)
bioma250mil = ee.FeatureCollection(param['assetBiomas'])\
                    .filter(ee.Filter.eq('Bioma', 'Caatinga')).geometry()

gerenciador(0, param)

if param['geral'] == True:

    if param['inBacia'] == True:

        areaM = iterandoXanoImCruda(pixelArea, bioma250mil, '')

    else:
        areaM = iterandoXano(pixelArea, bioma250mil)
    
    nameCSV = 'areaXclasse_' + param['biome'] + '_Col' + param['collection'] + param['sufixo'] + param['version']
    processoExportar(areaM, nameCSV)

else:

    areaG = ee.FeatureCollection([])

    gBacias = ee.FeatureCollection(param['assetBacia'])

    for ii, nbacia in enumerate(param['listaNameBacias']):

        print("caculando bacia # {}: {}".format(ii, nbacia))

        baciaT = gBacias.filter(ee.Filter.eq('nunivotto3', nbacia)).geometry()

        baciaT = baciaT.intersection(bioma250mil, 1)

        if param[ 'inBacia'] == True:

            areaXbac = iterandoXanoImCruda(pixelArea, baciaT, nbacia)
        else:
            areaXbac = iterandoXano(pixelArea, baciaT)

            areaXbac = areaXbac.map(lambda feat: feat.set('bacia', nbacia))
        areaG = areaG.merge(areaXbac)

    
    nameCSV = 'areaXclasse_' + param['biome'] + '_AllBacias_C' + param['collection']  + param['sufixo']
    processoExportar(areaG, nameCSV)




