import ee
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



def exportROIs(ROIs, nameR):  

    optExp = {
        'collection': ROIs, 
        'description': nameR, 
        'folder':  'CSV_ROis'    
    }

    task = ee.batch.Export.table.toDrive(**optExp)
    task.start()
       
    print (" ## salvando ROI:  < {} > \n  ## para o folder  < CSV_ROis >... !".format(
        nameR
    ))


def GetPolygonsfromFolder(assetFolder):
    
    getlistPtos = ee.data.getList(assetFolder)

    cont = 0
    for idAsset in getlistPtos: 
        
        path_ = idAsset.get('id')
        print(path_) 
        lsFile =  path_.split("/")
        name = lsFile[-1]   

        names = name.split('_')

        if names[1] == '0':
            print("coletando primeiro")
            ColectionPtos = ee.FeatureCollection(path_)
        elif names[1] == '1':
            ColectionPtos = ColectionPtos.merge(ee.FeatureCollection(path_))
            exportROIs(ColectionPtos, names[0]) 
            print("coletando segundo e exportando {} --> {}".format(cont, names[0]))
            cont += 1


param = {
    'assetRois': {'id':'projects/mapbiomas-workspace/AMOSTRAS/col5/CAATINGA/ROIsXBaciasBalmin300v3'},
    # 'bacias' : [ '759', '766','767','771','7612','7613','7614','7615','772', '773', '775', 
    #              '777', '763','7618', '765', '762', '746', '7619', '7616', '7617',  '745', 
    #              '747', '732', '743','752', '751','755','758' , '757'],
}

GetPolygonsfromFolder(param['assetRois'])