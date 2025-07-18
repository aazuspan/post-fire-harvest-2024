library(tidyverse)
library(nlme)
library(plyr)


####read in data
salvage<-read.csv("./annual_trends_perc 02022024.csv", sep=",",header=T,fill=T)

###change na's to zero for other ownerships
salvage$salvage_rate[salvage$owner=="other"&is.na(salvage$salvage_rate)] <- 0

TREND_LWD <- 2.8
TREND_COL <- "white"
TREND_CEX <- 1.8
TREND_LTY <- "dotted"
MARKER_TYPE <- "o"
ASTERISK_SIZE <- 3.5


##read in landscape metrics
long_metrics<-read.csv("./annual_mean_patch_area_20240301.csv", sep=",",header=T,fill=T)

#change owner names in long metrics
long_metrics$owner<-revalue(long_metrics$owner, c("Federal"="Federal", "Private"="Private", "Total"="All"))
levels(long_metrics$owner)

#make metrics wide
metrics = long_metrics %>% 
  spread(metric, value)

salvage <- merge(salvage,metrics, by.x=c("owner","year"),  by.y=c("owner","year"), all=T)


salvage$lsalvage_area <- log10(salvage$salvage_area+1)
salvage$ltotal_area <- log10(salvage$total_area+1)

############create variable for step and trend 

n <- dim(salvage)

###create step year variable
salvage$step2005 <- rep(0,n[1])
salvage$step2005[salvage$year>2004] <-1
salvage$step2004 <- rep(0,n[1])
salvage$step2004[salvage$year>2003] <-1
salvage$step2003 <- rep(0,n[1])
salvage$step2003[salvage$year>2002] <-1
salvage$step2002 <- rep(0,n[1])
salvage$step2002[salvage$year>2001] <-1
salvage$step2001 <- rep(0,n[1])
salvage$step2001[salvage$year>2000] <-1
salvage$step2000 <- rep(0,n[1])
salvage$step2000[salvage$year>1999] <-1
salvage$step1999 <- rep(0,n[1])
salvage$step1999[salvage$year>1998] <-1
salvage$step1998 <- rep(0,n[1])
salvage$step1998[salvage$year>1997] <-1
salvage$step1997 <- rep(0,n[1])
salvage$step1997[salvage$year>1996] <-1
salvage$step1996 <- rep(0,n[1])
salvage$step1996[salvage$year>1995] <-1
salvage$step1995 <- rep(0,n[1])
salvage$step1995[salvage$year>1994] <-1
salvage$step1994 <- rep(0,n[1])
salvage$step1994[salvage$year>1993] <-1

###create trend year variable
salvage$trend1994 <- salvage$year-1994
salvage$trend1994[salvage$year<1994] <- 0
salvage$trend1995 <- salvage$year-1995
salvage$trend1995[salvage$year<1995] <- 0
salvage$trend1996 <- salvage$year-1996
salvage$trend1996[salvage$year<1996] <- 0
salvage$trend1997 <- salvage$year-1997
salvage$trend1997[salvage$year<1997] <- 0
salvage$trend1998 <- salvage$year-1998
salvage$trend1998[salvage$year<1998] <- 0
salvage$trend1999 <- salvage$year-1999
salvage$trend1999[salvage$year<1999] <- 0
salvage$trend2000 <- salvage$year-2000
salvage$trend2000[salvage$year<2000] <- 0
salvage$trend2001 <- salvage$year-2001
salvage$trend2001[salvage$year<2001] <- 0
salvage$trend2002 <- salvage$year-2002
salvage$trend2002[salvage$year<2002] <- 0
salvage$trend2003 <- salvage$year-2003
salvage$trend2003[salvage$year<2003] <- 0
salvage$trend2004 <- salvage$year-2004
salvage$trend2004[salvage$year<2004] <- 0
salvage$trend2005 <- salvage$year-2005
salvage$trend2005[salvage$year<2005] <- 0
salvage$trend2006 <- salvage$year-2006
salvage$trend2006[salvage$year<2006] <- 0


###create indicator variables for no salvage

salvage$indzero.rate <- rep(0,n[1])
salvage$indzero.rate[salvage$salvage_rate==0] <- 1

salvage$indzero.total <- rep(0,n[1])
salvage$indzero.total[salvage$total_area==0] <- 1

salvage$indzero.salvage <- rep(0,n[1])
salvage$indzero.salvage[salvage$salvage_area==0] <- 1

###ADD YEARS WITH <1000 ha burned

salvage$pa1991 <- rep(0,n[1])
salvage$pa1991[salvage$year==1991] <- 1

salvage$pa1993 <- rep(0,n[1])
salvage$pa1993[salvage$year==1993] <- 1

salvage$pa1995 <- rep(0,n[1])
salvage$pa1995[salvage$year==1995] <- 1

salvage$pa1997 <- rep(0,n[1])
salvage$pa1997[salvage$year==1997] <- 1

salvage$pa1998 <- rep(0,n[1])
salvage$pa1998[salvage$year==1998] <- 1

salvage$pa2003 <- rep(0,n[1])
salvage$pa2003[salvage$year==2003] <- 1

salvage$pa2010 <- rep(0,n[1])
salvage$pa2010[salvage$year==2010] <- 1

      
       
############################### CODE TO MAKE FIGURE    ###########################
png(file="./salvage_metrics_figure3.png", units= "in", width=9.5, height=8.5, res=600)
par( mfrow= c(3,3) )


op<-par(no.readonly=TRUE)
par(oma=c(2,2,2,2))

par(op)
par(oma=c(5,5,3,0),mar=c(3,3,2,2),mfrow=c(3,3), omi=c(0.3,0.4,0.2,0))

##############################  AREA #######################



########## ALL OWNERSHIPS AREA



salvage_area.final.gls <- gls(lsalvage_area ~ 
                                trend1997 + year  + pa1991 + pa1993 + pa1997 
                              ,
                              data=salvage[salvage$owner=="All",],na.action=na.omit,method="ML")
summary(salvage_area.final.gls)

##create null model to calculate r squared 
salvage_area.All.null.gls <- gls(lsalvage_area ~ 
                                   1,
                                 data=salvage[salvage$owner=="All",],na.action=na.omit,method="ML")
summary(salvage_area.All.null.gls)
tss <-  sum(residuals(salvage_area.All.null.gls)^2)
sse <- sum(residuals(salvage_area.final.gls)^2)
1-sse/tss

########


##########make figure with final model

plot(lsalvage_area~year, data=salvage[salvage$owner=="All",],   
     pch=21, col=TREND_COL, bg="#909090", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="")


coef(salvage_area.final.gls)

###add first part 
points(c(1986,1997), c(coef(salvage_area.final.gls)[1]+ 1986*coef(salvage_area.final.gls)[3],
                       1997*coef(salvage_area.final.gls)[3]+coef(salvage_area.final.gls)[1])
       , type="l", col="black", lwd=TREND_LWD)

##add second part
points(c(1997,2017), c(coef(salvage_area.final.gls)[1]+1997*coef(salvage_area.final.gls)[3],
                       2017*coef(salvage_area.final.gls)[3]+coef(salvage_area.final.gls)[1]+
                         (2017-1997)*coef(salvage_area.final.gls)[2]), type="l", col="black", lwd=TREND_LWD)

text(1997, 4, expression("*"), cex=ASTERISK_SIZE)






##########  FEDERAL OWNERSHIP AREA   ########################

##final
salvage_area.Fed.gls <- gls(lsalvage_area ~ 
                              step1998  + trend1998 + pa1991 + pa1993 + pa1995 + pa1997 
                            ,
                            data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(salvage_area.Fed.gls)

##create null model to calculate r squared 
salvage_area.All.null.gls <- gls(lsalvage_area ~ 
                                   1,
                                 data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(salvage_area.All.null.gls)
tss <-  sum(residuals(salvage_area.All.null.gls)^2)
sse <- sum(residuals(salvage_area.Fed.gls)^2)
1-sse/tss  ##this is r squared


########


##########make figure with final model

plot(lsalvage_area~year, data=salvage[salvage$owner=="Federal",],   
     pch=21, col=TREND_COL, bg="#33a02c", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="")

coef(salvage_area.Fed.gls)

###add first part -DOES THE BREAK YEARGETINLCUDED IN BOTH?
points(c(1986,1998), c(coef(salvage_area.Fed.gls)[1],
                       coef(salvage_area.Fed.gls)[1])
       , type="l", col="black", lwd=TREND_LWD,lty=TREND_LTY)

##add second part
points(c(1998,2017), c(coef(salvage_area.Fed.gls)[1]+(1998-1998)*coef(salvage_area.Fed.gls)[3] + coef(salvage_area.Fed.gls)[2],
                       (2017-1998)*coef(salvage_area.Fed.gls)[3]+coef(salvage_area.Fed.gls)[1]+
                         coef(salvage_area.Fed.gls)[2]), type="l",lwd=TREND_LWD, col="black")




text(1998, 4, expression("*"), cex=ASTERISK_SIZE)
text(1998, 3.68, expression("*"), cex=ASTERISK_SIZE)
text(2000, 4, expression("*"), cex=ASTERISK_SIZE)

########## PRIVATE OWNERSHIP AREA  ##########################

##final
salvage_area.Priv.gls <- gls(lsalvage_area ~ 
                               year + step1997 +pa1991 + pa1993 + pa1995  + pa1997 + pa2003 
                             ,
                             data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_area.Priv.gls)

plot(lsalvage_area~year, data=salvage[salvage$owner=="Private",],  
     pch=21, col=TREND_COL, bg="#1f78b4", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="")

##create null model to calculate r squared 
salvage_area.Priv.null.gls <- gls(lsalvage_area ~ 
                                   1,
                                 data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_area.Priv.null.gls)
tss <-  sum(residuals(salvage_area.Priv.null.gls)^2)
sse <- sum(residuals(salvage_area.Priv.gls)^2)
1-sse/tss  ##this is r squared

coef(salvage_area.Priv.gls)

###add first part 
points(c(1986,1997), c(coef(salvage_area.Priv.gls)[1]+ 1986*coef(salvage_area.Priv.gls)[2],
                       1996*coef(salvage_area.Priv.gls)[2]+coef(salvage_area.Priv.gls)[1]) , type="l", lwd=TREND_LWD, col="black")

##add second part
points(c(1997,2017), c(coef(salvage_area.Priv.gls)[1]+ 1997*coef(salvage_area.Priv.gls)[2] 
                       + coef(salvage_area.Priv.gls)[3], 2016*coef(salvage_area.Priv.gls)[2]+coef(salvage_area.Priv.gls)[1] 
                       + coef(salvage_area.Priv.gls)[3]), type="l", lwd=TREND_LWD, col="black")


##############################  RATES  #####################3
##########make figure with final model


########## ALL OWNERSHIPS FIGURE


##final
salvage_rate.All.final.gls <- gls(salvage_rate ~ 
                                    step1996   + pa1993 
                                  ,
                                  data=salvage[salvage$owner=="All",],na.action=na.omit,method="ML")
summary(salvage_rate.All.final.gls)





##create null model to calculate r squared 
salvage_rate.All.null.gls <- gls(salvage_rate ~ 
                                   1,
                                 data=salvage[salvage$owner=="All",],na.action=na.omit,method="ML")
summary(salvage_rate.All.null.gls)
tss <-  sum(residuals(salvage_rate.All.null.gls)^2)
sse <- sum(residuals(salvage_rate.All.final.gls)^2)
1-sse/tss


########

plot(salvage_rate~year, data=salvage[salvage$owner=="All",],   
     pch=21, col=TREND_COL, bg="#909090", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="", ylim=c(0,30))


coef(salvage_rate.All.final.gls)

###add first part -DOES THE BREAK YEARGETINLCUDED IN BOTH?
points(c(1986,1996), c(coef(salvage_rate.All.final.gls)[1],
                       coef(salvage_rate.All.final.gls)[1])
       ,type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


##add second part
points(c(1996,2017), c(coef(salvage_rate.All.final.gls)[1]+coef(salvage_rate.All.final.gls)[2],
                       coef(salvage_rate.All.final.gls)[2]+coef(salvage_rate.All.final.gls)[1]), type="l", col="black", 
       lwd=TREND_LWD, lty=TREND_LTY)

text(1996, 28, expression("*"), cex=ASTERISK_SIZE)
text(1996, 25.7, expression("*"), cex=ASTERISK_SIZE)


#####  FEDERAL RATES
###years area burned<1000 ha pa1991 + pa1993 + pa1995 + pa1997 + pa1998
salvage_rate.Fed.gls <- gls(salvage_rate ~ 
                              step1996  + pa1991 + pa1993 + pa1995  + pa1998
                            , correlation = corARMA(p =1, q = 0),
                            data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(salvage_rate.Fed.gls)

#correlation = corARMA(p =1, q = 0),
##This is a chisquare with 1 deg of freedom ---- do this with your final model

###2*((-32.57962 ##This is a chisquare with 1 deg of freedom ---- do this with your final model

2*((-68.49701 +70.89845))

1-pchisq(4.80288,1)

#p=0.0.0284122 so phi is sig different from zero))


###new r2
residuals <- residuals(salvage_rate.Fed.gls)
residuals.lag1 <- c(NA,residuals[-length(residuals)])
phi <- -0.5863478
residuals.ar1 <- residuals-phi*residuals.lag1
sse.ar1 <- sum(residuals.ar1[!is.na(residuals.ar1)]^2)
r2.ar1 <- 1-sse.ar1/tss
r2.ar1
sse.ar1

#####



plot(salvage_rate~year, data=salvage[salvage$owner=="Federal",],  
     pch=21, col=TREND_COL, bg="#33a02c", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="", ylim=c(0,30))

coef(salvage_rate.Fed.gls)


###add first part -DOES THE BREAK YEARGETINLCUDED IN BOTH?
points(c(1986,1996), c(coef(salvage_rate.Fed.gls)[1],
                       coef(salvage_rate.Fed.gls)[1])
       ,type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


##add second part
points(c(1996,2017), c(coef(salvage_rate.Fed.gls)[1]+coef(salvage_rate.Fed.gls)[2],
                       coef(salvage_rate.Fed.gls)[2]+coef(salvage_rate.Fed.gls)[1]), type="l", col="black", 
       lwd=TREND_LWD, lty=TREND_LTY)
text(1996.5, 28, expression("*"), cex=ASTERISK_SIZE)
text(1996.5, 25.7, expression("*"), cex=ASTERISK_SIZE)


#####  PRIVATE RATES
##final
salvage_area.Priv.gls <- gls(salvage_rate ~ 
                               pa1993 + pa1997 + pa2003 
                             ,
                             data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_area.Priv.gls)
##create null model to calculate r squared 
salvage_rate.Priv.null.gls <- gls(salvage_rate ~ 
                                   1,
                                 data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_rate.Priv.null.gls)
tss <-  sum(residuals(salvage_rate.Priv.null.gls)^2)
sse <- sum(residuals(salvage_area.Priv.gls)^2)
1-sse/tss






########




plot(salvage_rate~year, data=salvage[salvage$owner=="Private",],   
     pch=21, col=TREND_COL, bg="#1f78b4", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="",  ylim=c(0,30))


coef(salvage_area.Priv.gls)
###add first part 
points(c(1986,2017), c(coef(salvage_area.Priv.gls)[1],
                       coef(salvage_area.Priv.gls)[1])
       ,  type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


coef(salvage_area.Priv.gls)



##############  PATCH SIZES 

##################  patch size
salvage$area[is.na(salvage$area)] <- 0
##final
p_salvage_area.All.gls <- gls(area ~ 
                               pa1993 + pa1997
                            ,
                            data=salvage[salvage$owner=="All",],na.action=na.omit,method="ML")
summary(p_salvage_area.All.gls)


##create null model to calculate r squared 
p_salvage_area.All.null.gls <- gls(area ~ 
                                    1,
                                  data=salvage[salvage$owner=="All",],na.action=na.omit,method="ML")
summary(p_salvage_area.All.null.gls)
tss <-  sum(residuals(p_salvage_area.All.null.gls)^2)
sse <- sum(residuals(p_salvage_area.All.gls)^2)
1-sse/tss


########

 

##########make figure with final model

#plot(area~year, data=salvage[salvage$owner=="All",], 
plot(area~year, data=salvage[salvage$owner=="All",],   
     pch=21, col=TREND_COL, bg="#909090", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE,ylab="", xlab="", ylim=c(0,25))

coef(p_salvage_area.All.gls)

###add first part 
points(c(1986,2017), c(coef(p_salvage_area.All.gls)[1],
                       coef(p_salvage_area.All.gls)[1])
       ,  type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)






##FEDERAL PATCH SIZE


p_salvage_area.Fed.gls <- gls(area ~ 
                             step1997 +  pa1993 + pa1995   + pa1998
                            , correlation = corARMA(p =1, q = 0),
                            data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(p_salvage_area.Fed.gls)

###new r2
residuals <- residuals(p_salvage_area.Fed.gls)
residuals.lag1 <- c(NA,residuals[-length(residuals)])
phi <- -0.6673855
residuals.ar1 <- residuals-phi*residuals.lag1
sse.ar1 <- sum(residuals.ar1[!is.na(residuals.ar1)]^2)
r2.ar1 <- 1-sse.ar1/tss
r2.ar1
sse.ar1

#####

##########make figure with final model
plot(area~year, data=salvage[salvage$owner=="Federal",], 
     pch=21, col=TREND_COL, bg="#33a02c", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE,ylab="", xlab="", ylim=c(0,25))

coef(p_salvage_area.Fed.gls)


###add first part -DOES THE BREAK YEARGETINLCUDED IN BOTH?
points(c(1986,1996), c(coef(p_salvage_area.Fed.gls)[1],
                       coef(p_salvage_area.Fed.gls)[1])
       ,type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


##add second part
points(c(1996,2017), c(coef(p_salvage_area.Fed.gls)[1]+coef(p_salvage_area.Fed.gls)[2],
                       coef(p_salvage_area.Fed.gls)[2]+coef(p_salvage_area.Fed.gls)[1]), type="l", col="black", 
       lwd=TREND_LWD, lty=TREND_LTY)



text(1996, 23.5, expression("*"), cex=ASTERISK_SIZE)
text(1996, 21.8, expression("*"), cex=ASTERISK_SIZE)

p_salvage_area.Priv.gls <- gls(area ~ 
                               trend1997  
                             ,
                             data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(p_salvage_area.Priv.gls)

##create null model to calculate r squared 
p_salvage_area.Priv.null.gls <- gls(area ~ 
                                     1,
                                   data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(p_salvage_area.Priv.null.gls)
tss <-  sum(residuals(p_salvage_area.Priv.null.gls)^2)
sse <- sum(residuals(p_salvage_area.Priv.gls)^2)
1-sse/tss


########


##########make figure with final model

plot(area~year, data=salvage[salvage$owner=="Private",], 
     pch=21, col=TREND_COL, bg="#1f78b4", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.5, cex.main=1.5, type=MARKER_TYPE, ylab="", xlab="", ylim=c(0,25))


coef(p_salvage_area.Priv.gls)

###add first part -DOES THE BREAK YEARGETINLCUDED IN BOTH?
points(c(1986,1997), c(coef(p_salvage_area.Priv.gls)[1],
                       coef(p_salvage_area.Priv.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

##add second part
points(c(1997,2017), c(coef(p_salvage_area.Priv.gls)[1]+(1997-1997)*coef(p_salvage_area.Priv.gls)[2],
                       (2017-1997)*coef(p_salvage_area.Priv.gls)[2]+coef(p_salvage_area.Priv.gls)[1]),  type="l", col="black", lwd=TREND_LWD, lty=1)

text(1997, 23.5, expression("*"), cex=ASTERISK_SIZE)




mtext(text="Fire Year",side=1,line=0.5,outer=TRUE, cex=1.5)
mtext(text="Mean Patch Size (ha)",side=2,line=0.5,outer=TRUE, cex=1.25, at=0.18)
mtext(text="Harvest Rate (%)",side=2,line=0.5,outer=TRUE, cex=1.25, at=0.51)
mtext(text="log Harvest Area (ha) ",side=2,line=0.5,outer=TRUE, cex=1.25, at=0.84)

mtext(text="   All                                     Federal                               Private",
      side=3,line=-1,outer=TRUE, cex=1.5)

dev.off()
