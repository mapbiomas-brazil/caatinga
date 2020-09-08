library(ggplot2)
library(dplyr)

###########################################
## TA

options(scipen=10000000)
aa=read.csv("C:/Users/Mapbiomas/Desktop/col5/gerfiltros.csv",
            sep=";",header = T, encoding = "UTF-8")
names(aa)
head(aa,5)
tail(aa,5)



## Filtro col 5 x Col 5 SF
aaa2=filter(aa, (Class == 3 | Class == 4 |Class == 12 |Class == 21 |Class == 22 |Class == 29 |Class == 33)
            & (colf == "F5" | colf == "5-Final" |colf == "SF" )) #| cversao == "4-INT" | cversao =="5-Final"))
head(aaa2,5)
tail(aaa2,5)

# ## filtro p/ arquivo gerfiltros 
# aaa1=filter(aa, (Class == 3 | Class == 4 |Class == 12 |Class == 21 |Class == 22 |Class == 29 |Class == 33)
#            & (versao == "v4"| versao == "v5" | versao == "v1055" | versao == "v2055" ))
# head(aaa1,5)
# tail(aaa1,5)
# 
# 
# 
# ## filtro p/ arquivo gerfiltros 
# aaa2=filter(aa, (Class == 3 | Class == 4 |Class == 12 |Class == 21 |Class == 22 |Class == 29 |Class == 33)
#             & (COL == "COL5")) #| cversao == "4-INT" | cversao =="5-Final"))
# head(aaa2,5)
# tail(aaa2,5)

#aaa=filter(aa, (Class == 3 | Class == 4 |Class == 12 |Class == 21 |Class == 22 |Class == 29 |Class == 33))
# head(LPI,5)
# tail(LPI,5)


########################################################################################
########################################################################################
##AREA

png(filename="C:/Users/Mapbiomas/Desktop/geralBioma_filtros_col5.png", 
    width=30, height=40, units= "cm",pointsize=14, res=150)

ggplot(aaa2, aes(x=ANO, y=VALOR,colour = factor(colversa))) + 
  geom_point(aes(x=ANO, y=VALOR),alpha=0.7,size=4.5)+
  geom_line(aes(x=ANO, y=VALOR),alpha=0.7,size=2)+
  #geom_text(aes(label=MUN),vjust = "inward", hjust = "inward")+
  xlab("Anos")+ 
  ylab("Valores")+
  labs(factor = "Legenda") +
  theme(legend.title=element_blank())+
  scale_x_continuous(breaks = c(1985, 1988, 1991, 1994, 1997, 
                                2000,2003,2006,2009,
                                2012,2015,2018))+
  #scale_y_continuous(limits=c(0,0.69))+  
  scale_color_manual(values=c("yellow", "magenta", "red","blue", "green", "orange","black", "gray"))+
  #guides(color=guide_legend("Classes"))+
  theme(axis.title.x = element_text(size = 12,face = "bold"))+ 
  theme(axis.title.y = element_text(size = 12,face = "bold"))+
  theme(strip.text.x = element_text(size = 12, face = "bold"))+ 
  theme(strip.text.y = element_text(size = 12, face = "bold"))+
  #geom_smooth(method='lm',color="red")+ #method='lm'
  #geom_smooth(aes(x=ANO, y=VALOR/100, group=Class),method='lm',color="red")+
  
  #geom_smooth(aes(x=ANO, y=VALOR, group=Class),method = "lm", formula = y ~ splines::bs(x, 6),color="red")+
  facet_grid(Class~Metrica,scales = "free_y") 
  #facet_grid(Metrica~Class,scales = "free_y") 
  #facet_grid(Metrica~Ecorregion,scales = "free_y") 


dev.off()
########################################################################################
########################################################################################
##AREA BACIAS

options(scipen=10000000)
bb=read.csv("C:/Users/Mapbiomas/Desktop/col5/geral_bacia_c4_c5v2.csv",
            sep=";",header = T, encoding = "UTF-8")
names(bb)
head(bb,5)
tail(bb,5)
# LPI=filter(aa, (Metrica == "LPI") & (Newclass == 2 | Newclass == 14))
# head(LPI,5)
# tail(LPI,5)

# bb=filter(bb, (classe != 0))
# names(bb)
# head(bb,5)
# tail(bb,5)

nrow(bb)
bb1=bb[1:9089,]
bb2=bb[9090:17557,]

##########################################################################################

png(filename="C:/Users/Mapbiomas/Desktop/P2_geralBacia_c4_c5v2a.png", 
    width=50, height=60, units= "cm",pointsize=12, res=600)

ggplot(bb2, aes(x=ANO, y=VALOR,colour = factor(versao))) + 
  geom_point(aes(x=ANO, y=VALOR),alpha=0.7,size=1.5)+
  geom_line(aes(x=ANO, y=VALOR),alpha=0.7,size=1)+
  #geom_text(aes(label=MUN),vjust = "inward", hjust = "inward")+
  xlab("Anos")+ 
  ylab("Valores")+
  labs(factor = "Legenda") +
  theme(legend.title=element_blank())+
  # scale_x_continuous(breaks = c(1985, 1988, 1991, 1994, 1997, 
  #                               2000,2003,2006,2009,
  #                               2012,2015,2018))+
  scale_x_continuous(breaks = c(1985, 1990,1995, 2000, 2005, 2010, 
                                2015,2020))+
  #scale_y_continuous(limits=c(0,0.69))+  
  scale_color_manual(values=c("#f99f40", "#129912"))+
  #guides(color=guide_legend("Classes"))+
  theme(axis.title.x = element_text(size = 8,face = "bold"))+ 
  theme(axis.title.y = element_text(size = 8,face = "bold"))+
  theme(strip.text.x = element_text(size = 8, face = "bold"))+ 
  theme(strip.text.y = element_text(size = 8, face = "bold"))+
  #geom_smooth(method='lm',color="red")+ #method='lm'
  #geom_smooth(aes(x=ANO, y=VALOR/100, group=Class),method='lm',color="red")+
  
  #geom_smooth(aes(x=ANO, y=VALOR, group=Class),method = "lm", formula = y ~ splines::bs(x, 6),color="red")+
  facet_grid(Bacia~Class,scales = "free_y") 
  #facet_grid(Class~Bacia,scales = "free_y") 
  

dev.off()
