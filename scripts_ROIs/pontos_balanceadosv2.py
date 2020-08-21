#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Produzido por Geodatin - Dados e Geoinformacao
DISTRIBUIDO COM GPLv2
@author: geodatin
"""

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
    'bioma': ["CAATINGA",'CERRADO','MATAATLANTICA'], 
    'asset_bacias': 'users/diegocosta/baciasRecticadaCaatinga',
    'asset_IBGE': 'users/SEEGMapBiomas/bioma_1milhao_uf2015_250mil_IBGE_geo_v4_revisao_pampa_lagoas',
    # 'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/PtosXBaciasBalanceados/',
    'outAsset': 'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalv2/',
    'assetMapbiomasP': 'projects/mapbiomas-workspace/public/collection4_1/mapbiomas_collection41_integration_v1',
    'asset_Mosaic': 'projects/mapbiomas-workspace/MOSAICOS/workspace-c3',
    'classMapB': [3,4,5,9,12,13,15,18,19,20,21,22,23,24,25,26,29,30,31,32,33],
    'classNew':  [3,4,3,3,12,12,21,21,21,21,21,22,22,22,22,33,29,22,33,12,33],
    'janela': 5,
    'escala': 30,
    'sampleSize': 0,
    'metodotortora': True,
    'lsClasse': ['3','4','12','21','22','33','29'],
    'lsPtos': [300,300,300,300,300,300,300],
    'tamROIsxClass': 4000,
    'minROIs': 1500,
    "anoColeta": 2015,
    'anoInicial': 1985,
    'anoFinal': 2019,
    "anoIntInit": 2002,
    "anoIntFin": 2018,
    'sufix': "_1",
    'numeroTask': 6,
    'numeroLimit': 40,
    'conta' : {
        '0': 'caatinga01',
        '5': 'caatinga02',
        '10': 'caatinga03',
        '15': 'caatinga04',
        '20': 'caatinga05',        
        '25': 'solkan1201',
        '27': 'diegoGmail',
        '30': 'rodrigo',
        '34': 'Rafael'        
    },
}


limite_bioma = ee.Geometry.Polygon(arqParam.lsPtos_limite_bioma)

biomas = ee.FeatureCollection(param['asset_IBGE']).filter(
    ee.Filter.inList('CD_LEGENDA',  param['bioma']))    

# ftcol poligonos com as bacias da caatinga
ftcol_bacias = ee.FeatureCollection(param['asset_bacias'])

list_anos = [k for k in range(param['anoInicial'],param['anoFinal'])]


print('Analisando desde o ano {} hasta o {} '.format(list_anos[0], list_anos[-1]))

indexIni = list_anos.index(param['anoIntInit'])
indexFin = list_anos.index(param['anoIntFin'])

# @collection1: mapas de uso e cobertura Mapbiomas ==> para extrair as areas estaveis
# collection1 = ee.ImageCollection(dirsamples).filterMetadata('biome', 'equals', bioma)
collection41 = ee.Image(param['assetMapbiomasP']).clip(biomas.geometry())

# @mosaicos: ImageCollection com os mosaicos de Mapbiomas 
mosaicos = ee.ImageCollection(param['asset_Mosaic']).filter(
    ee.Filter.inList('biome',  param['bioma']))

terrain = ee.Image("JAXA/ALOS/AW3D30_V1_1").select("AVE")
slope = ee.Terrain.slope(terrain)
square = ee.Kernel.square(**{'radius': 3}) 

# Remap todas as imagens mapbiomas
lsBndMapBiomnas = []
imgMapbiomas = ee.Image().toByte()

for year in list_anos:

    band = 'classification_' + str(year)
    lsBndMapBiomnas.append(band)

    imgTemp = collection41.select(band).remap(param['classMapB'], param['classNew'])

    imgMapbiomas = imgMapbiomas.addBands(imgTemp.rename(band))


imgMapbiomas = imgMapbiomas.select(lsBndMapBiomnas)
# print(imgMapbiomas.bandNames().getInfo())
collection41 = None

# carregando a lista de nomes das bacias 
lsBacias = arqParam.listaNameBacias
print("=== lista de nomes de bacias carregadas ===")
print("=== {} ===".format(lsBacias))

#=====================================#
# gerenciador de contas para controlar# 
# processos task no gee               #
#=====================================#
def gerenciador(cont, param):    
    
    numberofChange = [kk for kk in param['conta'].keys()]

    if str(cont) in numberofChange:
        
        gee.switch_user(param['conta'][str(cont)])
        gee.init()        
        gee.tasks(n= param['numeroTask'], return_list= True)        
    
    elif cont > param['numeroLimit']:
        cont = 0
    
    cont += 1    
    return cont


# def homogenisarValoresaMaximos (mkey, mval):
    
#     temp = ee.Number(ee.List(mval).get(2))
    
#     mval = ee.Algorithms.If(
#                   ee.Algorithms.IsEqual(temp.lt(param['minROIs']), 1),
#                   ee.List(mval).replace(temp, param['minROIs']), ee.List(mval))

#     return mval

# calcula a proporsão que significa os pontos da classe do total de ROIS
def calcProporsion(valor, total):

    proporsion = ee.Number(valor).divide(total)
    
    valorN_Amost = proporsion.multiply(param['sampleSize'])

    valorMaxn = valorN_Amost.max(param['minROIs'])  

    return valorMaxn.int()

def calcProporsionTortora(valor, total):
    
    proporsion = ee.Number(valor).divide(total)
    
    valorN_Amost = ee.Number(7.568).multiply(proporsion).multiply(
                        ee.Number(1.0).subtract(proporsion)).divide(0.000625)

    valorMaxn = valorN_Amost.max(param['minROIs'])  

    return valorMaxn.int()

#metodo retorna amostras de tamanhos diferentes, por classe, de acordo com a quantidade
#presente na bacia
def criar_amostras_por_classe (imgClassAnalises, limite):    
    
    # classes = []

    #numero de minimo de samples para classes pouco presentes
    # nSamplesMin = 1000
    #numero maximo de samples - para o metodo balanceado por area    
    
    paramtRedReg = {
        'reducer': ee.Reducer.frequencyHistogram(),
        'geometry': imgClassAnalises.geometry(),
        'scale': param['escala'],         
        'maxPixels':1e13
    }    

    histogramClasses =  imgClassAnalises.reduceRegion(**paramtRedReg)
    histogramClasses = histogramClasses.values().get(0).getInfo()
    print(histogramClasses)

    total = sum(histogramClasses.values())
    classes = histogramClasses.keys()
    
    ###############################################################################
    #   calcula a quantidade de amostras que representarao bem cada classe,    ####
    #   de acorco com a porcentagem de presenca dessa classe na bacia e a      ####
    #   representatividade estatistica                                         ####
    #   n = z2*(p*(1-p))/E2 ===> z = 1.96 ====> E = 0.025 ==> no = 1/E2        ####
    #   n = (B*N*(1-N))/E2  indice de tortora (1978) e congalton (1957)        ####
    ###############################################################################
    
    lsROIsNum = []
    for cc in classes:

        proporsion = histogramClasses[cc]/total
        # Valor representativo de uma quantidade 

        if param['metodotortora'] == False:            
            valorN_Amost = proporsion * param['sampleSize']
            valorMax = max(valorN_Amost, param['minROIs'])           
        
        else:                  
            
            valorN_Amost = (7.568 * proporsion * (1.0 - proporsion))/ (0.000625)        
            valorMax = max(valorN_Amost, param['minROIs'])   
        
        lsROIsNum.append(int(valorMax))    
    
    print('### Levando todos os valores mínimos ao máximo fixado ###')
    # get o valor do maximo
    valorMaximo = max(lsROIsNum)
    for ii in range(len(lsROIsNum)):
        
        vv = lsROIsNum[ii]
        if vv != param['minROIs']:
            lsROIsNum[ii] = valorMaximo

    return lsROIsNum, classes

#salva ftcol para um assetindexIni
def saveToAsset(collection, name):    
    
    optExp = {
            'collection': collection, 
            'description': name, 
            'assetId': param['outAsset'] + name           
    }
    
    task = ee.batch.Export.table.toAsset(**optExp)
    task.start()
    
    print("exportando ROIs da bacia $s ...!", name)

# retorna uma lista com as strings referentes a janela dada, por exemplo em janela 5, no ano 1Nan999, o metodo retornaria
# ['classification_1997', 'classification_1998', 'classification_1999', 'classification_2000', 'classification_2001']
# desse jeito pode-se extrair as bandas referentes as janelas
def mapeiaAnos(ano, janela, anos):
    
    lsBandAnos = ['classification_'+str(item) for item in anos]

    # primeiroAno = anos[0]
    # ultimoAno = anos[-1]

    primeiroAno = param['anoInicial']
    ultimoAno = param['anoFinal'] - 1
    indice = anos.index(ano)

    if ano == primeiroAno:
        return lsBandAnos[0:janela]

    elif ano == anos[1]:
        return lsBandAnos[0:janela]

    elif ano == anos[-2]:
        return lsBandAnos[-janela:]

    elif ano == ultimoAno:
        return lsBandAnos[-janela:]

    else:
        return lsBandAnos[indice-2: indice+3]

#variavel que define o metodo de amostragem. o metodo 2 balanceia por area e por representatividade estatistica
def iterate_bacias(bacia, colAnos, nomeBacia):
    
    #colecao responsavel por executar o controle de execucao, caso optem por executar o codigo em terminais paralelos,
    #ou seja, em mais de um terminal simultaneamente..
    #caso deseje executar num unico terminal, deixar colecao vazia. 
    
    # baciasFeitas = ['$nome_bacia1', '$nome_bacia2', 'e assim por diante..'] 
    # nomeBacia = bacia.get('nunivotto3').getInfo()

        
    BuffBacia = ee.Feature(bacia).geometry().buffer(35000) 
    colecaoPontos = ee.FeatureCollection([])
    # imgBacia = collection1.clip(BuffBacia)        
    
    anoCount = param['anoIntInit']
    # lsNoPtos = []
        
    for intervalo in colAnos:

        bandActiva = 'classification_' + str(anoCount)
        
        print( "banda activa: " + bandActiva)
        print(intervalo)
    
        imgTemp = imgMapbiomas.select(intervalo).clip(BuffBacia)
        imgTemp = imgTemp.set("system:footprint", BuffBacia)
        
        #@reducida: cria uma imagem que cada pixel diz quanto variou entre todas as bandas
        reducida =  imgTemp.reduce(ee.Reducer.countDistinct())
        reducida = reducida.eq(1)
        
        #@imgTemp: sera o mapa de uso e cobertura Mapbiomas ao que sera masked com as classes 
        #estaveis na janela de 5 anos       
        imgTemp = imgTemp.select(bandActiva)       
        imgTemp = imgTemp.mask(reducida).rename(['class'])

        # print("imgTemp ", imgTemp.bandNames().getInfo())
    
        # este metodo devolve um dictionario com os valores das classes minimo e máximo 
        if anoCount == param['anoIntInit']:

            lspontosAmostra, lsClasse = criar_amostras_por_classe(imgTemp, BuffBacia)               
   
            #transforma o dicionario em dois vetores, um para classes e outros para as quantidades
            #que devem ser extraidas
            
            lsClasse = [int(kk) for kk in lsClasse]
            print( "lista das classes ", lsClasse)
            print( "numero de ptos X classe", lspontosAmostra)
            

        mosaicosBaciaAno = ee.Image(mosaicos.filter(ee.Filter.eq('year', anoCount))\
                                    .filterBounds(BuffBacia).median()).clip(BuffBacia)
        
        #passando a geometria da bacia de novo para o mosaico 
        
        mosaicosBaciaAno = mosaicosBaciaAno.addBands(imgTemp)
        mosaicosBaciaAno = mosaicosBaciaAno.mask(reducida)
        mosaicosBaciaAno = mosaicosBaciaAno.clip(BuffBacia)
        mosaicosBaciaAno = mosaicosBaciaAno.set("system:footprint", BuffBacia)       
        
        #opcoes para o sorteio estratificadoBuffBacia        
        ptosTemp = mosaicosBaciaAno.stratifiedSample(            
            numPoints= 0,
            classBand= 'class',
            region= BuffBacia,
            scale= 30,
            classValues= lsClasse,
            classPoints= lspontosAmostra,
            # tileScale= 2,
            geometries= True
        )
        #insere informacoes em cada ft
        ptosTemp = ptosTemp.map(lambda ponto: ponto.set({'year': anoCount, 'bacia': nomeBacia}))
        # ptosTemp = ptosTemp.map(lambda ponto: ponto.set({})) 

        ptosTemp = ptosTemp.filter(ee.Filter.notNull(['amp_evi2', 'amp_gv', 'amp_ndfi', 'amp_ndvi', 'amp_ndwi']))       

        #merge com colecoes anteriores 
        colecaoPontos = colecaoPontos.merge(ptosTemp)
        anoCount+=1
    
    saveToAsset(colecaoPontos, str(nomeBacia) + param['sufix'])
    

## Revisando todos as Bacias que foram feitas 
arqFeitos = open("registros/lsBaciasROIsfeitasBalanceadas.txt", 'r')

baciasFeitas = [] 

for ii in arqFeitos.readlines():    
    ii = ii[:-1]
    # print(" => " + str(ii))
    baciasFeitas.append(ii)

# if len(baciasFeitas) > 0:
    
#     print("listando Bacias Feitas")
    
#     for ii in baciasFeitas:
#         print("==> " + ii)

arqFeitos = open("registros/lsBaciasROIsfeitasBalanceadas.txt", 'a+')

# creando a lista de bandas em janelas de 5 anos

colectAnos = map(lambda ano: mapeiaAnos(ano, param['janela'], list_anos), list_anos)
newColectAnos = [k for k in colectAnos]

for ii in newColectAnos[indexIni : indexFin + 1]:
    print(ii)
print("index : ", list_anos.index(param['anoIntInit']))
print("index : ", list_anos.index(param['anoIntFin']))

# print("colecao de anos ", newColectAnos[-1:])

colectAnos = None
cont = 0
lsBacias = ['7616']
for item in lsBacias:
    
    if item not in baciasFeitas:

        print("fazendo bacia " + item)        
    
        baciaTemp = ftcol_bacias.filter(ee.Filter.eq('nunivotto3', item)).first()
        # baciasBuff = ftcol_bacias.filterBounds(baciaTemp.geometry())

        # lsNamesBacias = baciasBuff.reduceColumns(ee.Reducer.toList(), ['nunivotto3']).get('list').getInfo()
        # print("lista de Bacias vizinhas", lsNamesBacias)
        
        # print(baciaTemp.getInfo()['properties'])
        iterate_bacias(
            ee.Feature(baciaTemp), 
            newColectAnos[indexIni : indexFin + 1], # newColectAnos[indexIni : indexFin],
            item)
        
        print("salvando ROIs bacia: << {} >>".format(item))

        arqFeitos.write(item + param['sufix'] + '\n')
         
        cont = gerenciador(cont, param)
    
arqFeitos.close()
