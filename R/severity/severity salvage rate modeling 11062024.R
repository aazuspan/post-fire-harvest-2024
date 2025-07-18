library(tidyverse)
library(nlme)


####read in salvage data
salvage_dat<-read.csv("./severity_rate_data.csv", sep=",",header=T,fill=T)
n <- dim(salvage_dat)

TREND_LWD <- 2.25
TREND_COL <- "white"
TREND_CEX <- 1.6
TREND_LTY <- "dotted"
MARKER_TYPE <- "o"
ASTERISK_SIZE <- 3.5


###ADD YEARS WITH <1000 ha burned

salvage_dat$pa1986 <- rep(0,n[1])
salvage_dat$pa1986[salvage_dat$year==1986] <- 1

salvage_dat$pa1987 <- rep(0,n[1])
salvage_dat$pa1987[salvage_dat$year==1987] <- 1

salvage_dat$pa1988 <- rep(0,n[1])
salvage_dat$pa1988[salvage_dat$year==1988] <- 1

salvage_dat$pa1989 <- rep(0,n[1])
salvage_dat$pa1989[salvage_dat$year==1989] <- 1

salvage_dat$pa1990 <- rep(0,n[1])
salvage_dat$pa1990[salvage_dat$year==1990] <- 1

salvage_dat$pa1991 <- rep(0,n[1])
salvage_dat$pa1991[salvage_dat$year==1991] <- 1

salvage_dat$pa1992 <- rep(0,n[1])
salvage_dat$pa1992[salvage_dat$year==1992] <- 1

salvage_dat$pa1993 <- rep(0,n[1])
salvage_dat$pa1993[salvage_dat$year==1993] <- 1

salvage_dat$pa1994 <- rep(0,n[1])
salvage_dat$pa1994[salvage_dat$year==1994] <- 1

salvage_dat$pa1995 <- rep(0,n[1])
salvage_dat$pa1995[salvage_dat$year==1995] <- 1

salvage_dat$pa1996 <- rep(0,n[1])
salvage_dat$pa1996[salvage_dat$year==1996] <- 1

salvage_dat$pa1997 <- rep(0,n[1])
salvage_dat$pa1997[salvage_dat$year==1997] <- 1

salvage_dat$pa1998 <- rep(0,n[1])
salvage_dat$pa1998[salvage_dat$year==1998] <- 1

salvage_dat$pa2000 <- rep(0,n[1])
salvage_dat$pa2000[salvage_dat$year==2000] <- 1

salvage_dat$pa2001 <- rep(0,n[1])
salvage_dat$pa2001[salvage_dat$year==2001] <- 1

salvage_dat$pa2003 <- rep(0,n[1])
salvage_dat$pa2003[salvage_dat$year==2003] <- 1

salvage_dat$pa2004 <- rep(0,n[1])
salvage_dat$pa2004[salvage_dat$year==2004] <- 1

salvage_dat$pa2005 <- rep(0,n[1])
salvage_dat$pa2005[salvage_dat$year==2005] <- 1

salvage_dat$pa2006 <- rep(0,n[1])
salvage_dat$pa2006[salvage_dat$year==2006] <- 

salvage_dat$pa2009 <- rep(0,n[1])
salvage_dat$pa2009[salvage_dat$year==2009] <- 1

salvage_dat$pa2010 <- rep(0,n[1])
salvage_dat$pa2010[salvage_dat$year==2010] <- 1

salvage_dat$pa2011 <- rep(0,n[1])
salvage_dat$pa2011[salvage_dat$year==2011] <- 1

salvage_dat$pa2016 <- rep(0,n[1])
salvage_dat$pa2016[salvage_dat$year==2016] <- 1


salvage_dat$trend1993 <- salvage_dat$year-1993
salvage_dat$trend1993[salvage_dat$year<1993] <- 0

salvage_dat$trend1992 <- salvage_dat$year-1992
salvage_dat$trend1992[salvage_dat$year<1992] <- 0





#correlation = corARMA(p =1, q = 0),
################################################################################################################################
################################################################################################################################

########################################### MAKE   FIGURE WITH FINAL MODELS ######################################### 

################################################################################################################################
################################################################################################################################
png(file="./severity_rate_figure4.png", units= "in", width=8, height=8.5, res=600)
par(mfrow = c(4, 2))#, tcl=-0.5,  mai=c(0.6,0.3,0.3,0.3))

op<-par(no.readonly=TRUE)
#par(oma=c(2,2,2,2))

#par(op)
par(oma=c(5,5,3,5),mar=c(3,3,2,2),mfrow=c(4,2), omi=c(0.3,0.4,0.2,0.1))


#################    HIGH SEVERITY  #########################################################


###years<1000ha pa1991 +pa1993 + pa1995 + pa 1997 + pa1998  
###FEDERAL
salvage<-salvage_dat[salvage_dat$severity=="High",]
high_rate.fed.gls <- gls(salvage_rate~ 
                                 step1996  +pa1993 + pa1995 +  pa1998 
                         , 
                         data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(high_rate.fed.gls)

##create null model
salvage_high.Fed.null.gls <- gls(salvage_rate ~ 
                                          1,
                                  data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(salvage_high.Fed.null.gls)
tss <-  sum(residuals(salvage_high.Fed.null.gls)^2)
sse <- sum(residuals(high_rate.fed.gls)^2)
1-sse/tss
#####



plot(salvage_rate~year, data=salvage[salvage$owner=="Federal",], 
     pch=21, col=TREND_COL, bg="red", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,45), type=MARKER_TYPE, ylab="", xlab="")

coef(high_rate.fed.gls)

###add first part 
points(c(1986,1996), c(coef(high_rate.fed.gls)[1],
                       coef(high_rate.fed.gls)[1])
       , type="l", col="black", lwd=2, lty=TREND_LTY)

##add second part
points(c(1996,2017), c(coef(high_rate.fed.gls)[1] + coef(high_rate.fed.gls)[2],
                       coef(high_rate.fed.gls)[1]+ coef(high_rate.fed.gls)[2]), type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)
text(1996, 39, expression("*"), cex=ASTERISK_SIZE)
text(1996, 34, expression("*"), cex=ASTERISK_SIZE)



###PRIVATE
#years <1000 ha  pa1991 + pa1993  + pa1995 + pa1997 + pa2003

salvage<-salvage_dat[salvage_dat$severity=="High",]
plot(salvage_rate~year, data=salvage[salvage$owner=="Private",],  
     pch=21, col=TREND_COL, bg="red", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5,ylim=c(0,45), type=MARKER_TYPE, ylab="", xlab="" )

high_rate.priv.gls <- gls(salvage_rate~ 
                                   pa1993   + pa2003 
                          , 
                          data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(high_rate.priv.gls)

##create null model
salvage_high.Priv.null.gls <- gls(salvage_rate ~ 
                                         1,
                                 data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_high.Priv.null.gls)
tss <-  sum(residuals(salvage_high.Priv.null.gls)^2)
sse <- sum(residuals(high_rate.priv.gls)^2)
1-sse/tss


coef(high_rate.priv.gls)

###add first part 
points(c(1986,2017), c(coef(high_rate.priv.gls)[1],
                       coef(high_rate.priv.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)



#######################        MODERATE SEVERITY ###############################
##years <1000 ha pa1991 +pa1993 + pa1995 + pa1997 + pa1998  
###FEDERAL
salvage<-salvage_dat[salvage_dat$severity=="Moderate",]
mod_rate.fed.gls <- gls(salvage_rate~ 
                                step1996  +pa1991 +pa1993 + pa1995 +  pa1998 
                        , correlation = corARMA(p =1, q = 0),
                        data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(mod_rate.fed.gls)

###new r2
residuals <- residuals(mod_rate.fed.gls)
residuals.lag1 <- c(NA,residuals[-length(residuals)])
phi <- -0.4102891
residuals.ar1 <- residuals-phi*residuals.lag1
sse.ar1 <- sum(residuals.ar1[!is.na(residuals.ar1)]^2)
r2.ar1 <- 1-sse.ar1/tss
r2.ar1
sse.ar1
#####

plot(salvage_rate~year, data=salvage[salvage$owner=="Federal",], 
     pch=21, col=TREND_COL, bg="orange", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,35), type=MARKER_TYPE, ylab="", xlab="")

coef(mod_rate.fed.gls)

###add first part 
###add first part 
points(c(1986,1996), c(coef(mod_rate.fed.gls)[1],
                       coef(mod_rate.fed.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

##add second part
points(c(1996,2017), c(coef(mod_rate.fed.gls)[1] + coef(mod_rate.fed.gls)[2],
                       coef(mod_rate.fed.gls)[1]+ coef(mod_rate.fed.gls)[2]), type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

text(1996, 31, expression("*"), cex=ASTERISK_SIZE)
text(1996, 27.3, expression("*"), cex=ASTERISK_SIZE)


###PRIVATE
###years<1000ha pa1991 +pa1993 + pa1995 + pa1997  + pa2003 + pa2010  
salvage<-salvage_dat[salvage_dat$severity=="Moderate",]

mod_rate.priv.gls <- gls(salvage_rate~ 
                                 trend1997    + pa2003 + pa2010 
                         ,
                         data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(mod_rate.priv.gls)


##create null model
salvage_mod.Priv.null.gls <- gls(salvage_rate ~ 
                                          1,
                                  data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_mod.Priv.null.gls)
tss <-  sum(residuals(salvage_mod.Priv.null.gls)^2)
sse <- sum(residuals(mod_rate.priv.gls)^2)
1-sse/tss


salvage<-salvage_dat[salvage_dat$severity=="Moderate",]
plot(salvage_rate~year, data=salvage[salvage$owner=="Private",],  
     pch=21, col=TREND_COL, bg="orange", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,35), type=MARKER_TYPE, ylab="", xlab="")

###add first part 
points(c(1986,1997), c(coef(mod_rate.priv.gls)[1],
                       coef(mod_rate.priv.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


###add second part
points(c(1997,2017), c(coef(mod_rate.priv.gls)[1] +(1997-1997)*coef(mod_rate.priv.gls)[2] ,
                       coef(mod_rate.priv.gls)[1] + (2017-1997)*coef(mod_rate.priv.gls)[2])
       , type="l", col="black", lwd=TREND_LWD)

text(1997, 31, expression("*"), cex=ASTERISK_SIZE)

########################   LOW SEVERITY   ###########################
#years<1000 ha  pa1986 + pa1991 + pa1992 +pa1993 + pa1994 +  pa1995 + pa1997 + pa1998  +  pa2010 + pa2011  

salvage<-salvage_dat[salvage_dat$severity=="Low",]
low_rate.fed.gls <- gls(salvage_rate~ 
                                 step1992  + pa1991 + pa1998  #+ price
                         , correlation = corARMA(p =1, q = 0),
                         data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(low_rate.fed.gls)

###new r2
residuals <- residuals(low_rate.fed.gls)
residuals.lag1 <- c(NA,residuals[-length(residuals)])
phi <- -0.4241721
residuals.ar1 <- residuals-phi*residuals.lag1
sse.ar1 <- sum(residuals.ar1[!is.na(residuals.ar1)]^2)
r2.ar1 <- 1-sse.ar1/tss
r2.ar1
sse.ar1
#####


salvage<-salvage_dat[salvage_dat$severity=="Low",]
plot(salvage_rate~year, data=salvage[salvage$owner=="Federal",],  
     pch=21, col=TREND_COL, bg="steelblue1", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,35), type=MARKER_TYPE, ylab="", xlab="")

coef(low_rate.fed.gls)

###add first part 
points(c(1986,1992), c(coef(low_rate.fed.gls)[1],
                       coef(low_rate.fed.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

##add second part
points(c(1992,2017), c(coef(low_rate.fed.gls)[1] + coef(low_rate.fed.gls)[2],
                       coef(low_rate.fed.gls)[1] + coef(low_rate.fed.gls)[2])
      , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


text(1992, 31, expression("*"), cex=ASTERISK_SIZE)
text(1992, 27.3, expression("*"), cex=ASTERISK_SIZE)



###PRIATE LOW SEVEIRTY
#years<1000 ha pa1986 + pa1989+ pa1990 + pa1991  +pa1993 + pa1994 +  pa1995 + pa1996 +  pa1997 + pa1998  + pa2000 + pa2001+ pa2003 + pa2004 + pa2005 + pa2006+  pa2009 + pa2010 + pa2011 + pa2016
##final
low_rate.priv.gls <- gls(salvage_rate~
                                 trend1993  + pa2003
                         ,
                         data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(low_rate.priv.gls)

##create null model
salvage_low.Priv.null.gls <- gls(salvage_rate ~ 
                                         1,
                                 data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_low.Priv.null.gls)
tss <-  sum(residuals(salvage_low.Priv.null.gls)^2)
sse <- sum(residuals(low_rate.priv.gls)^2)
1-sse/tss

salvage<-salvage_dat[salvage_dat$severity=="Low",]
plot(salvage_rate~year, data=salvage[salvage$owner=="Private",], 
     pch=21, col=TREND_COL, bg="steelblue1", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,35), type=MARKER_TYPE, ylab="", xlab="")
###add first part 
points(c(1986,1993), c(coef(low_rate.priv.gls)[1],
                       coef(low_rate.priv.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

##add second part
points(c(1993,2017), c(coef(low_rate.priv.gls)[1] + (1993-1993)*coef(low_rate.priv.gls)[2],
                       coef(low_rate.priv.gls)[1] + (2017-1993)*coef(low_rate.priv.gls)[2]
), type="l", col="black", lwd=TREND_LWD)

text(1993, 31, expression("*"), cex=ASTERISK_SIZE)

#################      VERY LOW SEVERITY   #############################################
#years<1000 ha pa1991 +pa1993  +  pa1995 + pa1997 + pa1998   + pa2011     
salvage<-salvage_dat[salvage_dat$severity=="Very low",]
vlow_rate.fed.gls <- gls(salvage_rate~ 
                                 step1992 + pa1991  +pa1998  #+ price #but p=0.1385 w slightly lower AIC
                         , 
                         data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(vlow_rate.fed.gls)




###new r2
##create null model
salvage_rate.All.null.gls <- gls(salvage_rate ~ 
                                         1,
                                 data=salvage[salvage$owner=="Federal",],na.action=na.omit,method="ML")
summary(salvage_rate.All.null.gls)
tss <-  sum(residuals(salvage_rate.All.null.gls)^2)
sse <- sum(residuals(vlow_rate.fed.gls)^2)
1-sse/tss
#####

coef(vlow_rate.fed.gls)

salvage<-salvage_dat[salvage_dat$severity=="Very low",]
plot(salvage_rate~year, data=salvage[salvage$owner=="Federal",],  
     pch=21, col=TREND_COL, bg="royalblue3", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,30), type=MARKER_TYPE, ylab="", xlab="")

###add first part 
points(c(1986,1992), c(coef(vlow_rate.fed.gls)[1],
                       coef(vlow_rate.fed.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

##add second part
points(c(1992,2017), c(coef(vlow_rate.fed.gls)[1] + coef(vlow_rate.fed.gls)[2],
                       coef(vlow_rate.fed.gls)[1] + coef(vlow_rate.fed.gls)[2]
), type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)

#text(2015, 12, expression("*"), cex=ASTERISK_SIZE)


text(1992, 27, expression("*"), cex=ASTERISK_SIZE)
text(1992, 23.5, expression("*"), cex=ASTERISK_SIZE)

#####very low severity private
#years<1000 ha pa1986 +  pa1991 + pa1992 +pa1993  +  pa1995 + pa1997 + pa1998  + pa2003 + pa2005 + pa2009 + pa2010 
salvage<-salvage_dat[salvage_dat$severity=="Very low",]

vlow_rate.priv.gls <- gls(salvage_rate~ 
                                  trend1995 + pa1992 # + pa2010
                          , 
                          data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(vlow_rate.priv.gls)


##create null model
salvage_vlow.Priv.null.gls <- gls(salvage_rate ~ 
                                         1,
                                 data=salvage[salvage$owner=="Private",],na.action=na.omit,method="ML")
summary(salvage_vlow.Priv.null.gls)
tss <-  sum(residuals(salvage_vlow.Priv.null.gls)^2)
sse <- sum(residuals(vlow_rate.priv.gls)^2)
1-sse/tss

salvage<-salvage_dat[salvage_dat$severity=="Very low",]
plot(salvage_rate~year, data=salvage[salvage$owner=="Private",], 
     pch=21, col=TREND_COL, bg="royalblue3", cex=TREND_CEX, cex.lab=1.5, cex.axis=1.3, cex.main=1.5, ylim=c(0,30), type=MARKER_TYPE, ylab="", xlab="")

###add first part 
points(c(1986,1995), c(coef(vlow_rate.priv.gls)[1],
                       coef(vlow_rate.priv.gls)[1])
       , type="l", col="black", lwd=TREND_LWD, lty=TREND_LTY)


###add second part
points(c(1995,2017), c(coef(vlow_rate.priv.gls)[1] +(1995-1995)*coef(vlow_rate.priv.gls)[2] ,
                       coef(vlow_rate.priv.gls)[1] + (2017-1995)*coef(vlow_rate.priv.gls)[2])
       , type="l", col="black", lwd=TREND_LWD)


text(1995, 27, expression("*"), cex=ASTERISK_SIZE)




mtext(text="Fire Year",side=1,line=0.5,outer=TRUE, cex=1.25)
mtext(text="Harvest Rate (%)",side=2,line=0.5,outer=TRUE, cex=1.25)

mtext(text="Federal",side=3,line=-1,outer=TRUE, cex=1.25, at=0.26)
mtext(text="Private",side=3,line=-1,outer=TRUE, cex=1.25, at=0.76)


mtext(text="Unburned/Low",side=4,line=-1,outer=TRUE, cex=1.1, at=0.13)
mtext(text="Low",side=4,line=-1,outer=TRUE, cex=1.1, at=0.38)
mtext(text="Moderate",side=4,line=-1,outer=TRUE, cex=1.1, at=0.63)
mtext(text="High",side=4,line=-1,outer=TRUE, cex=1.1, at=0.88)

dev.off()
