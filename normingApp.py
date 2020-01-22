#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

import tkinter
import tkinter.filedialog as filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar
# from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar
from matplotlib.backend_bases import key_press_handler
from matplotlib.widgets import SpanSelector
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MaxNLocator
import matplotlib.pyplot as plt
import numpy as np
import glob
#import matplotlib.pyplot as plt

import normAppLogic

class NormSpectra(tkinter.Tk):


    def __initAttributes__(self):
        self.appLogic = normAppLogic.normAppLogic()

        #control variables
        self.ifCreateNewRegion = False
        self.ifChooseActiveRegion = False
        self.ifAddPoint = False
        self.ifAutoUpdateNormalization = False
        self.ifApplyRadioVelocityCorrection = False
        self.numberOfActiveRegion = 0

        self.radVelDialog = None

        self.fileList = []
        self.currentFile = ""

    def __init__(self):
        tkinter.Tk.__init__(self)
        self.__initAttributes__()
        self.createMainWindow()

    def createMainWindow(self):
        self.createWindow()
        self.createControls()
        self.createMenu()
        self.createPlottingArea()

    def createWindow(self):
        self.frame = tkinter.Frame(self)
        self.frame.pack(fill=tkinter.BOTH, expand=1)
        self.wm_title("HANDY - Handy tool for spectra normalization")

        # img = tkinter.PhotoImage(file=os.path.join(os.path.dirname(os.path.realpath(__file__)),"handyColor.gif"))
        img = tkinter.PhotoImage(file=os.path.join(os.path.dirname(os.path.realpath(__file__)),"handy.gif"))
        self.tk.call('wm', 'iconphoto', self._w, img)

    def createMenu(self):

        menu = tkinter.Menu(self)
        self.config(menu=menu)
        #------------------------------------
        fileMenu1 = tkinter.Menu(menu)
        menu.add_cascade(label="Open", underline=0, menu=fileMenu1)
        fileMenu1.add_command(label="Open spectrum", command=self.onOpenSpectrum)
        fileMenu1.add_command(label="Open continuum file",\
                              command=self.onLoadContinuum)
        fileMenu1.add_command(label="Open theoretical spectrum",\
                              command=self.onLoadTheoreticalSectrum)
        fileMenu1.add_command(label="Exit", underline=0, command=self.onExit)
        #------------------------------------
        fileMenu2 = tkinter.Menu(menu)
        menu.add_cascade(label="Save", underline=0, menu=fileMenu2)
        fileMenu2.add_command(label="Save normed spectrum",\
                              command=self.onSaveNormedSpectrum)
        fileMenu2.add_command(label="Save normed spectrum VRAD corrected",\
                              command=self.onSaveVelocityCorrectedNormedSpectrum)
        fileMenu2.add_command(label="Save continuum",\
                              command=self.onSaveContinuum)
        fileMenu2.add_command(label="Save theoretical spectrum",\
                              command=self.onSaveTheoreticalSpectrum)
        #------------------------------------
        fileMenu3 = tkinter.Menu(menu)
        menu.add_cascade(label="Grids", underline=0, menu=fileMenu3)
        self.vlevel = tkinter.IntVar()
        lG = self.appLogic.gridDefinitions.listAvailibleGrids()
        self.appLogic.gridDefinitions.setChoosenGrid(lG[0])
        self.onChooseGrid() # load default grid
        for i, gridName in enumerate(lG):
            fileMenu3.add_radiobutton(label = gridName,
                                      var = self.vlevel,
                                      value = i,
                                      command = self.onChooseGrid
                                      )
        # self.vlevel.set(0)

    def onChooseGrid(self):
        lG = self.appLogic.gridDefinitions.listAvailibleGrids()
        numOfGrid = self.vlevel.get()
        self.appLogic.gridDefinitions.setChoosenGrid(lG[numOfGrid])
        print("Set {} grid".format(lG[numOfGrid]))
        # print(d)
        paramsList, folder, refWave, paramsNum, paramsMult, fluxFilesFilter, skipRows, waveColumn, fluxColumn, comments = self.appLogic.gridDefinitions.setGridParams()
        self.appLogic.specSynthesizer.setGrid(
            folder = folder,
            refWave = refWave,
            paramsList = paramsList,
            paramsNum = paramsNum,
            paramsMult = paramsMult,
            fluxFilesFilter = fluxFilesFilter,
            skipRows = skipRows,
            waveColumn = waveColumn,
            fluxColumn = fluxColumn,
            comments = comments,
        )
        d = self.appLogic.gridDefinitions.getDefinedVariables()
        setVal = {True: 'normal', False: 'disabled'}
        self.teffScale['state'] = setVal[d["teff"]]
        self.loggScale['state'] = setVal[d["logg"]]
        self.vmicScale['state'] = setVal[d["vmic"]]
        self.meScale['state'] = setVal[d["me"]]
        if d["teff"]:
            self.teffScale['from_'],self.teffScale['to'] = self.appLogic.specSynthesizer.getRangesOfParameter("teff")
        if d["logg"]:
            self.loggScale['from_'], self.loggScale['to'] = self.appLogic.specSynthesizer.getRangesOfParameter("logg")
        if d["vmic"]:
            self.vmicScale['from_'] ,self.vmicScale['to'] = self.appLogic.specSynthesizer.getRangesOfParameter("vmic")
        if d["me"]:
            minim, maxim = self.appLogic.specSynthesizer.getRangesOfParameter("me")
            if minim == 0: #TODO conversion of units should be done better
                minim = -2
            else:
                minim = np.round(np.log10(minim),2)
            maxim = np.round(np.log10(maxim),2)
            self.meScale['from_'] ,self.meScale['to'] = minim, maxim

    def onOpenSpectrum(self):
        dirname = os.getcwd()
        ftypes = [('All files', '*'),('FITS files', '*fits'),('Plain text', '*.txt *.dat')]
        answer = filedialog.askopenfilenames(title="Open spectrum...", initialdir=dirname, filetypes=ftypes)
        if answer:
            self.fileList = answer
            fileName = self.fileList[0]
            self.currentFile = fileName
            skipRows=1
            colWave=0
            colFlux=1
            self.appLogic.readSpectrum(fileName,\
                                       colWave=colWave,\
                                       colFlux=colFlux,\
                                       skipRows=skipRows)

        self.appLogic.continuumRegionsLogic.updateRegionsAndPoints(self.appLogic.spectrum)
        self.appLogic.continuum.wave = []
        self.appLogic.continuum.flux = []
        if self.ifAutoUpdateNormalization:
            self.appLogic.normSpectrum()
        self.onAlreadyNormed(reprint = False)

        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux,ifAutoscale=True)


    def onLoadContinuum(self):
        dirname = os.getcwd()
        ftypes = [('Plain text', '*.cont'),('All files', '*')]
        answer = filedialog.askopenfilenames(title="Open ranges file...", initialdir=dirname, filetypes=ftypes)
        if answer:
            fileName = answer[0]
            self.appLogic.continuumRegionsLogic.readRegionsFile(self.appLogic.spectrum,\
                                                            fileName)

            self.appLogic.continuumRegionsLogic.updateRegionsAndPoints(self.appLogic.spectrum)
            order = str(self.appLogic.continuumRegionsLogic.getOrderOfActiveRegion())
            self.currentOrder.set(order)
            if self.ifAutoUpdateNormalization:
                self.appLogic.normSpectrum()
            contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
            self.replotUpdatedRanges(contRegionsWaveAndFlux)

    def onLoadTheoreticalSectrum(self):
        dirname = os.getcwd()
        ftypes = [('Plain text', '*.txt *.dat *.syn'),('All files', '*')]
        answer = filedialog.askopenfilenames(title="Open spectrum...", initialdir=dirname, filetypes=ftypes)
        if answer:
            fileName = answer[0]
            skipRows=1
            colWave=0
            colFlux=1
            self.appLogic.readTheoreticalSpectrum(fileName,\
                                                  colWave=colWave,\
                                                  colFlux=colFlux,\
                                                  skipRows=skipRows)

        self.line23.set_data(self.appLogic.theoreticalSpectrum.wave,\
                             self.appLogic.theoreticalSpectrum.flux)
        if self.appLogic.theoreticalSpectrum.wave is not None and len(self.appLogic.theoreticalSpectrum.wave)!=0:
            self.updateErrorPlot()
        self.canvas.draw()

    def onExit(self):
        self.quit()

    def onSaveNormedSpectrum(self):
        initialName = "out.norm"
        if self.appLogic.spectrum.name is not None:
            initialName = self.appLogic.spectrum.name.split('.')[-2]+".norm"
        fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.spectrum.wave is not None:
            # self.appLogic.saveNormedSpectrum(fileName,self.ifSaveCorrectedvrad.get())
            self.appLogic.saveNormedSpectrum(fileName,False)

    def onSaveVelocityCorrectedNormedSpectrum(self):
        initialName = "out.norm"
        if self.appLogic.spectrum.name is not None:
            initialName = self.appLogic.spectrum.name.split('.')[-2]+"_rv.norm"
        fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.spectrum.wave is not None:
            self.appLogic.saveNormedSpectrum(fileName,True)
            # self.appLogic.saveSpectrum(fileName)

    def onSaveContinuum(self):
        initialName = "out.cont"
        if self.appLogic.spectrum.name is not None:
            initialName = self.appLogic.spectrum.name.split('.')[-2]+".cont"
        fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.spectrum.wave is not None:
            self.appLogic.continuumRegionsLogic.saveRegionsFile(self.appLogic.spectrum,\
                                                                fileName)

    def onSaveTheoreticalSpectrum(self):
        initialName = "out.syn"
        if self.appLogic.spectrum.name is not None:
            initialName = self.appLogic.spectrum.name.split('.')[-2]+".syn"
        fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.theoreticalSpectrum.wave is not None:
            self.appLogic.saveTheoreticalSpectrum(fileName)

    def createControls(self):
        # Create several frames for grouping buttons
        self.controlFrame = tkinter.Frame(self.frame)
        self.controlFrameA=tkinter.Frame(self.controlFrame)
        self.controlFrameB=tkinter.Frame(self.controlFrame)
        self.controlFrameC=tkinter.Frame(self.controlFrame)

        WENS = tkinter.W+tkinter.E+tkinter.N+tkinter.S
        #=======================================================================
        self.bttn11 = tkinter.Button(self.controlFrameA,\
                                    text = "Back",\
                                    command = self.onBack)
        self.bttn11.grid(row = 0, column = 0, sticky = WENS)

        self.bttn21 = tkinter.Button(self.controlFrameA,\
                                    text = "Choose region",\
                                    command = self.onChooseActiveRegion)
        self.bttn21.grid(row = 1, column = 0, sticky = WENS)

        self.bttn31 = tkinter.Button(self.controlFrameA,\
                                     text = "Create region",\
                                     command = self.onCreateNewActiveRegion)
        self.bttn31.grid(row = 2, column = 0, sticky = WENS)

        self.currentOrder = tkinter.StringVar()
        self.bttn41 = tkinter.Spinbox(self.controlFrameA,\
                                        from_=1,\
                                        to=10,\
                                        command=self.onUpdateOrder,\
                                        textvariable=self.currentOrder,\
                                        state = "readonly",\
                                        )
                                     # text = "Create new active region",\
                                     # command = self.onCreateNewActiveRegion)
        self.bttn41.grid(row = 3, column = 0, sticky = WENS)
        #-----------------------------------------------------------------------
        self.bttn12 = tkinter.Button(self.controlFrameA,\
                                     text = "Next spectrum",\
                                     command = self.onNextSpectrum)
        self.bttn12.grid(row = 0, column = 1, sticky = WENS)

        self.bttn22 = tkinter.Button(self.controlFrameA,\
                                    text = "Add special point",\
                                    command = self.onAddSpecialPoint)
        self.bttn22.grid(row = 1, column = 1, sticky = WENS)

        self.bttn32 = tkinter.Button(self.controlFrameA,\
                                    text = "Auto fit special points",\
                                    command = self.onAutoFitSpecialPoints)
        self.bttn32.grid(row = 2, column = 1, sticky = WENS)

        self.bttn42 = tkinter.Label(self.controlFrameA, text=" <--- Adjust order")
        self.bttn42.grid(row = 3, column = 1, sticky = WENS)
        #-----------------------------------------------------------------------
        self.bttn13 = tkinter.Button(self.controlFrameA,\
                                     text = "Normalize",\
                                     command = self.onNormalize)
        self.bttn13.grid(row = 0, column = 2, sticky = WENS)

        self.bttn23 = tkinter.Button(self.controlFrameA,\
                                    text = "Auto update",\
                                    command = self.onSetAutoUpdateNormalization)
        self.bttn23.grid(row = 1, column = 2, sticky = WENS)

        self.bttn33 = tkinter.Button(self.controlFrameA,\
                                    text = "Radial velocity",\
                                    command = self.onRadialVelocity)
        self.bttn33.grid(row = 2, column = 2, sticky = WENS)
        #=======================================================================

        self.backgroundColor = self.bttn11.cget("bg")
        self.activeBackground = self.bttn11.cget("activebackground")

        #=======================================================================
        self.teffVar = tkinter.DoubleVar(value = 22000)
        self.loggVar = tkinter.DoubleVar(value = 3.8)
        self.vmicVar = tkinter.DoubleVar(value = 2)
        self.meVar = tkinter.DoubleVar(value = 0.0)
        self.vsiniVar = tkinter.DoubleVar(value = 0)
        self.vmacVar = tkinter.DoubleVar(value = 0)
        self.resolution = tkinter.DoubleVar() # set value when initializing window
        # https://stackoverflow.com/questions/41225071/python-tkinter-spinbox-seems-to-reset-the-variable-value
        hor = tkinter.HORIZONTAL
        self.teffScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.teffVar,
                                        orient = hor,
                                        label = "Teff",
                                        from_ = 15000,
                                        to = 30000,
                                        resolution = 50,
                                        # sliderlength = 30,
                                        #length = 200,
                                        )
        self.teffScale.grid(row = 0, column = 0, columnspan = 2, sticky = WENS)

        self.loggScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.loggVar,
                                        orient = hor,
                                        label = "logg",
                                        from_ = 3.0,
                                        to = 4.5,
                                        resolution = 0.05)
        self.loggScale.grid(row = 1, column = 0, sticky = WENS)

        self.vmicScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.vmicVar,
                                        orient = hor,
                                        label = 'vmic',
                                        from_ = 0,
                                        to = 15,
                                        resolution = 1,
                                        )
        self.vmicScale.grid(row = 1, column = 1, sticky = WENS)

        self.vmacScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.vmacVar,
                                        orient = hor,
                                        label = "vmac",
                                        from_ = 0,
                                        to = 50,
                                        resolution = 1,
                                        length = 150,
                                        )
        self.vmacScale.grid(row = 0, column = 2, sticky = WENS)


        self.vsiniScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.vsiniVar,
                                        orient = hor,
                                        label = "vsini",
                                        from_ = 0,
                                        to = 200,
                                        resolution = 1,
                                        length = 150,
                                        )
        self.vsiniScale.grid(row = 1, column = 2, sticky = WENS)

        self.meScale = tkinter.Scale(self.controlFrameB,
                                    variable = self.meVar,
                                    orient = hor,
                                    label = "[M/H]",
                                    from_ = -1, #TODO work around low metallicity bug
                                    to = 0.3,
                                    resolution = 0.1,
                                    # length = 30,
                                    )
        self.meScale.grid(row = 0, column = 3, columnspan = 2, sticky = WENS)

        # self.resolutionScale = tkinter.Scale(self.controlFrameB,
        #                                 variable = self.resolution,
        #                                 orient = hor,
        #                                 label = 'resolution',
        #                                 from_ = 1000,
        #                                 to = 100000,
        #                                 resolution = 1000,
        #                                 length = 150,
        #                                 )
        # self.resolutionScale = tkinter.Entry(self.controlFrameB,
        #                         textvariable = self.resolution,
        #                         )

        self.resolutionLabel = tkinter.Label(self.controlFrameB,
                                             text = "resolution",
                                             )
        self.resolutionLabel.grid(row = 1, column = 3, sticky = WENS)

        self.resolutionScale = tkinter.Spinbox(self.controlFrameB,
                                textvariable = self.resolution,
                                values = (1000,2000,5000,10000,20000,50000,100000,np.inf),
                                state = 'readonly',
                                width = 7,
                                )
        self.resolution.set(np.inf) # Must be like that :(
        self.resolutionScale.grid(row = 1, column = 4, sticky = WENS)

        self.bttnClearTheorSpec = tkinter.Button(self.controlFrameB,\
                                    text = "Clear\ntheoretical\nspectrum",\
                                    command = self.onClearTheoreticalSpectrum)
        self.bttnClearTheorSpec.grid(row = 0, column = 5, rowspan = 1, sticky = WENS)

        self.bttnLoadTheorSpec = tkinter.Button(self.controlFrameB,\
                                    text = "Compute\ntheoretical\nspectrum",\
                                    command = self.onComputeTheoreticalSpectrum)
        self.bttnLoadTheorSpec.grid(row = 1, column = 5, rowspan = 1, sticky = WENS)

        # self.ifSaveCorrectedvrad = tkinter.IntVar()
        # self.chButtonCorrectedVRad = tkinter.Checkbutton(self.controlFrameC,
        #                                                 text = "Save\ncorrected\nfor\nvrad?",
        #                                                 variable = self.ifSaveCorrectedvrad,
        #                                                 #height = 20,
        #                                                 )
        # self.chButtonCorrectedVRad.grid(row = 0, column = 0, sticky = WENS)

        self.ifAlreadyNormed = tkinter.IntVar()
        self.workWithNormedSpectrum = tkinter.Checkbutton(self.controlFrameC,
                                                        text = "Already\nnormalised\nspectrum?",
                                                        variable = self.ifAlreadyNormed,
                                                        command = self.onAlreadyNormed,
                                                        )
        self.workWithNormedSpectrum.grid(row = 1, column = 0, sticky = WENS)

        self.bttnOpenSaveWindow = tkinter.Button(self.controlFrameC,\
                                    text = "Plot\nfitted\nspectrum",\
                                    command = self.onOpenSavePlot)
        self.bttnOpenSaveWindow.grid(row = 2, column = 0, sticky = WENS)

        # self.variables = tkinter.Text(self.controlFrameC, width = 50, height = 5,\
        #                               wrap = tkinter.WORD,state="disabled")
        # self.variables.pack(side=tkinter.LEFT,fill=tkinter.BOTH, expand=1)

        self.controlFrameA.grid(row = 0, column = 0, sticky = WENS)
        self.controlFrameB.grid(row = 0, column = 1, sticky = WENS)
        self.controlFrameC.grid(row = 0, column = 2, sticky = WENS)
        self.controlFrame.pack()

    def onAlreadyNormed(self,reprint = True):
        if self.ifAlreadyNormed.get() == 1:
            # print("Spectrum is already normed!!!")
            self.appLogic.ifOnNormedSpectrum(True)
            self.bttn11['state'] = 'disabled'
            self.bttn21['state'] = 'disabled'
            self.bttn31['state'] = 'disabled'
            self.bttn12['state'] = 'disabled'
            self.bttn22['state'] = 'disabled'
            self.bttn32['state'] = 'disabled'
            self.bttn13['state'] = 'disabled'
            self.bttn23['state'] = 'disabled'
        else:
            self.appLogic.ifOnNormedSpectrum(False)
            self.bttn11['state'] = 'normal'
            self.bttn21['state'] = 'normal'
            self.bttn31['state'] = 'normal'
            self.bttn12['state'] = 'normal'
            self.bttn22['state'] = 'normal'
            self.bttn32['state'] = 'normal'
            self.bttn13['state'] = 'normal'
            self.bttn23['state'] = 'normal'

        self.numberOfActiveRegion = self.appLogic.continuumRegionsLogic.activeRegionNumber
        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux)

    def onUpdateOrder(self):
        order = int(self.currentOrder.get())
        self.appLogic.updateOrderOfActiveRegion(order)
        if self.ifAutoUpdateNormalization:
            self.appLogic.normSpectrum()
        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux)

    def onBack(self):
        self.appLogic.continuumRegionsLogic.restoreLast()
        self.numberOfActiveRegion = self.appLogic.continuumRegionsLogic.activeRegionNumber
        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux)
        if self.ifAutoUpdateNormalization:
            self.onNormalize()

    def onChooseActiveRegion(self):
        self.ifCreateNewRegion = False
        self.ifChooseActiveRegion = not self.ifChooseActiveRegion
        self.ifAddPoint = False
        self.setButtons(self.bttn21,self.ifChooseActiveRegion)

    def onCreateNewActiveRegion(self):
        self.ifCreateNewRegion = not self.ifCreateNewRegion
        self.ifChooseActiveRegion = False
        self.ifAddPoint = False
        self.setButtons(self.bttn31,self.ifCreateNewRegion)

    def onAddSpecialPoint(self):
        self.ifCreateNewRegion = False
        self.ifChooseActiveRegion = False
        self.ifAddPoint = not self.ifAddPoint
        self.setButtons(self.bttn22,self.ifAddPoint)

    def setButtons(self,button,boolKeyVar):
        self.bttn21.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.bttn31.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.bttn22.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        if self.ifAddPoint:
            self.span.set_visible(False)
        if self.ifChooseActiveRegion:
            self.span.set_visible(False)
        if boolKeyVar:
            button.configure(bg = "#567",activebackground="#678")
        else:
            self.span.set_visible(True)
            button.configure(bg = self.backgroundColor,activebackground=self.activeBackground)

    def resetButtons(self):
        self.bttn21.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.bttn31.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.bttn22.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.span.set_visible(True)

    def onNextSpectrum(self):
        if not self.currentFile:  # do nothing if no files yet selected
            return
        currentIndex = self.fileList.index(self.currentFile)
        nextIndex = (currentIndex + 1) % len(self.fileList)
        fileName = self.fileList[nextIndex]
        self.currentFile = fileName
        skipRows = 1
        colWave = 0
        colFlux = 1
        self.appLogic.readSpectrum(fileName, \
                                   colWave=colWave, \
                                   colFlux=colFlux, \
                                   skipRows=skipRows)

        self.appLogic.continuumRegionsLogic.updateRegionsAndPoints(self.appLogic.spectrum)
        self.appLogic.continuum.wave = []
        self.appLogic.continuum.flux = []
        if self.ifAutoUpdateNormalization:
            self.appLogic.normSpectrum()
        self.onAlreadyNormed(reprint=False)

        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux, ifAutoscale=True)
        return

    def onAutoFitSpecialPoints(self):
        self.appLogic.continuumRegionsLogic.autoFitPoints(self.appLogic.theoreticalSpectrum)
        if self.ifAutoUpdateNormalization:
            self.appLogic.normSpectrum()
        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux)


    def onNormalize(self):
        self.appLogic.normSpectrum()
        if self.appLogic.spectrum.wave is not None:
            self.updateNormedPlot()
            self.canvas.draw()

    def onSetAutoUpdateNormalization(self):
        self.ifAutoUpdateNormalization = not self.ifAutoUpdateNormalization
        if self.ifAutoUpdateNormalization:
            self.onNormalize()
            self.bttn23.configure(bg = "#567",activebackground="#678")
        else:
            self.bttn23.configure(bg = self.backgroundColor,activebackground=self.activeBackground)

    def onRadialVelocity(self):
        if np.any(self.appLogic.theoreticalSpectrum.wave)\
           and self.appLogic.spectrum is not None:
           if self.radVelDialog is None:
                self.radVelDialog = radialVelocityDialog(self.appLogic,self.onCloseRadialVelocityDialog)
                self.radVelDialog.wm_protocol('WM_DELETE_WINDOW', lambda: self.onCloseRadialVelocityDialog())
        else:
            print("WARNING:NormSpectra.onRadialVelocity\n"\
                 +"Load theoretical spectra first!")

    def onComputeTheoreticalSpectrum(self):
        self.appLogic.computeTheoreticalSpectrum(self.teffVar.get(),
                                                self.loggVar.get(),
                                                self.vmicVar.get(),
                                                self.meVar.get(),
                                                self.vsiniVar.get(),
                                                self.vmacVar.get(),
                                                float(self.resolution.get()),
                                                )
        wt = self.appLogic.theoreticalSpectrum.wave if self.appLogic.theoreticalSpectrum.wave is not None else []
        ft = self.appLogic.theoreticalSpectrum.flux if self.appLogic.theoreticalSpectrum.flux is not None else []
        self.line23.set_data(wt,ft)
        if self.appLogic.theoreticalSpectrum.wave is not None and len(self.appLogic.theoreticalSpectrum.wave)!=0:
            self.updateErrorPlot()
        self.canvas.draw()

    def onClearTheoreticalSpectrum(self):
        self.appLogic.theoreticalSpectrum.wave = None
        self.appLogic.theoreticalSpectrum.flux = None
        self.line23.set_data([],[])
        self.updateErrorPlot()
        self.canvas.draw()

    def onOpenSavePlot(self):

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        w = self.appLogic.normedSpectrum.wave if self.appLogic.normedSpectrum.wave is not None else []
        f = self.appLogic.normedSpectrum.flux if self.appLogic.normedSpectrum.flux is not None else []
        wt = self.appLogic.theoreticalSpectrum.wave if self.appLogic.theoreticalSpectrum.wave is not None else []
        ft = self.appLogic.theoreticalSpectrum.flux if self.appLogic.theoreticalSpectrum.flux is not None else []

        line11,line12, = ax.plot(w,f,'b-',
                                   wt,ft,'k--',
                                   )
        ax.set_ylim([0.0,1.1])
        ax.set_xlim(self.ax1.get_xlim())
        ax.set_xlabel('Wavelength $[\AA]$')
        ax.set_ylabel('Flux')

        plt.show()

    def createPlottingArea(self):

        self.plotFrame = tkinter.Frame(self.frame)
        self.dpi = 100
        self.fig = Figure((5.0, 5.0), dpi=self.dpi)
        # self.fig = Figure((5.0, 5.0), dpi=self.dpi,tight_layout=True)
        # self.fig.tight_layout(w_pad = 0.0)
        self.fig.subplots_adjust(wspace=0.0, hspace=0.0, top=0.95, bottom=0.05, left=0.05, right=0.95)
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(5, 1)
        self.canvas = FigCanvas(self.fig, master=self.plotFrame)
        self.canvas.draw()

        # self.ax1 = self.fig.add_subplot(311)
        self.ax1 = self.fig.add_subplot(gs[:2])
        self.ax1.grid(True)
        self.line11,self.line12,self.line13,=self.ax1.plot([],[],'k-',\
                                                           [],[],'ro',\
                                                           [],[],'b-')
        # self.ax2 = self.fig.add_subplot(312,sharex=self.ax1)
        self.ax2 = self.fig.add_subplot(gs[2:4],sharex=self.ax1)
        self.ax2.grid(True)
        self.line21,self.line22,self.line23 = self.ax2.plot([],[],'k',\
                                                            [],[],'b',\
                                                            [],[],'b')
        # self.ax3 = self.fig.add_subplot(313,sharex=self.ax1)
        self.ax3 = self.fig.add_subplot(gs[-1],sharex=self.ax1)
        self.ax3.grid(True)
        self.ax3.yaxis.set_major_locator(MaxNLocator(nbins=3,prune='upper'))
        self.line31, = self.ax3.plot([],[],'b')

        self.ax1.set_autoscaley_on(True)
        #self.ax2.set_autoscaley_on(False)
        self.ax2.set_ylim([0.2,1.1])

        box = self.ax1.get_position()

        self.canvas.mpl_connect('button_press_event', self.onPlotClick)
        self.canvas.mpl_connect('button_release_event', self.onPlotRealise)
        #self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('key_press_event', self.onKeyPress)
        self.toolbar = NavigationToolbar(self.canvas, self.plotFrame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.plotFrame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

        #span selector
        self.span = SpanSelector(self.ax1, self.onUsingSpanSelector,\
                                 'horizontal', useblit=True,\
                                 rectprops=dict(alpha=0.5, facecolor='red'),\
                                 button=1)
        #self.span.set_visible(False)

    def onKeyPress(self,event):
        if event.key == 'n':
            if self.appLogic.spectrum.name is not None:
                fit = os.path.join(os.path.dirname(self.appLogic.spectrum.name), "*fits")
                # print(self.appLogic.spectrum.name)
                # print(fit)
                filesInFolder=glob.glob(fit)
                filesInFolder.sort()
                n = filesInFolder.index(self.appLogic.spectrum.name) + 1
                if n < len(filesInFolder):
                    fileName = filesInFolder[n]
                    skipRows=1
                    colWave=0
                    colFlux=1
                    self.appLogic.readSpectrum(fileName,\
                                               colWave=colWave,\
                                               colFlux=colFlux,\
                                               skipRows=skipRows)
                    self.appLogic.continuumRegionsLogic.updateRegionsAndPoints(self.appLogic.spectrum)
                    if self.ifAutoUpdateNormalization:
                        self.appLogic.normSpectrum()
                    contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
                    self.replotUpdatedRanges(contRegionsWaveAndFlux,ifAutoscale=True)
                else:
                    print("Last spectrum in choosen folder!")
        key_press_handler(event, self.canvas, self.toolbar)
        print("TODO: add some shortcuts to buttons")

    def onPlotClick(self,event):
        if self.toolbar.mode!='':
            # If zooming, etc. just return
            return
        if event.button == 1:
            if self.ifAddPoint:
                self.appLogic.continuumRegionsLogic.addPoint(event.xdata,\
                                                             event.ydata,\
                                                             self.appLogic.spectrum)
            if self.ifChooseActiveRegion:
                self.appLogic.continuumRegionsLogic.changeActiveRegion(event.xdata,\
                                                                       event.ydata)
        if event.button == 2:
            self.appLogic.continuumRegionsLogic.changeActiveRegion(event.xdata,\
                                                                   event.ydata)
        if event.button == 3:
            self.appLogic.continuumRegionsLogic.deleteRegionOrPoint(event.xdata,\
                                                                    event.ydata)
        if self.ifAutoUpdateNormalization:
            self.appLogic.normSpectrum()
        self.numberOfActiveRegion = self.appLogic.continuumRegionsLogic.activeRegionNumber
        order = str(self.appLogic.continuumRegionsLogic.getOrderOfActiveRegion())
        self.currentOrder.set(order)
        contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
        self.replotUpdatedRanges(contRegionsWaveAndFlux)
        #self.appLogic.continuumRegionsLogic.printSpecialPoints()
        #self.appLogic.continuumRegionsLogic.printRegions()

    def onPlotRealise(self,event):
        if self.toolbar.mode!='':
            # If zooming, etc. just return
            return
        if event.button == 1:
            if self.ifAddPoint:
                self.ifAddPoint=False
                self.resetButtons()
            if self.ifChooseActiveRegion:
                self.ifChooseActiveRegion=False
                self.resetButtons()



    def onUsingSpanSelector(self,xmin, xmax):
        if self.appLogic.spectrum.wave is not None:
            if sum((self.appLogic.spectrum.wave > xmin) & (self.appLogic.spectrum.wave < xmax)) == 0:
                print("WARING: Chosen range doesn't contain any points!")
            else:
                newRange = [xmin, xmax]
                self.appLogic.continuumRegionsLogic.addRegion(newRange,\
                          ifCreateNewRegion=self.ifCreateNewRegion)
                self.ifCreateNewRegion = False
                self.resetButtons()
                self.numberOfActiveRegion = self.appLogic.continuumRegionsLogic.activeRegionNumber
                order = str(self.appLogic.continuumRegionsLogic.getOrderOfActiveRegion())
                self.currentOrder.set(order)
                if self.ifAutoUpdateNormalization:
                    self.appLogic.normSpectrum()
                contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
                self.replotUpdatedRanges(contRegionsWaveAndFlux)
        else:
            print("WARNING: NormSpectra.onUsingSpanSelector\nLoad spectrum first")
        #self.appLogic.continuumRegionsLogic.printRegions()

    def replotUpdatedRanges(self,contRegionsWaveAndFlux,ifAutoscale=False):
        colorGen = self.colorGenerator()
        w = self.appLogic.spectrum.wave if self.appLogic.spectrum.wave is not None else []
        f = self.appLogic.spectrum.flux if self.appLogic.spectrum.flux is not None else []
        self.line11.set_data(w,f)

        # Plot all ranges
        for _ in range(len(self.ax1.lines)-3): # Remove all lines of ranges
            self.ax1.lines.pop()
        for i,region in enumerate(contRegionsWaveAndFlux):
            w = []
            f = []
            regCol='r'
            if i != self.numberOfActiveRegion: # Active region is red
                regCol = next(colorGen)
            for r in region:
                self.ax1.plot(r[0],r[1],c=regCol)

        # Plot specialPoints
        if len(self.appLogic.continuumRegionsLogic.specialPoints) == 0:
            self.line12.set_data([],[])
        else:
            x,y = self.appLogic.getValuesForPlotSpecialPoints()
            self.line12.set_data(x,y)

        # Plot when update normed spectrum
        if self.appLogic.spectrum.wave is not None:
            self.updateNormedPlot()

        if ifAutoscale: # when read new spectrum autoscale
            self.ax1.set_autoscale_on(True)
            self.ax1.relim()
            self.ax1.autoscale_view(True,True,True)
            self.toolbar.update()

        self.canvas.draw()

    def updateNormedPlot(self):
        self.line21.set_data(self.appLogic.normedSpectrum.wave,\
                             self.appLogic.normedSpectrum.flux)
        self.line22.set_data([self.appLogic.spectrum.wave[0],\
                              self.appLogic.spectrum.wave[-1]],\
                              [1,1])
        self.line13.set_data(self.appLogic.continuum.wave,\
                             self.appLogic.continuum.flux)
        self.line13.set_zorder(10)

        if self.appLogic.theoreticalSpectrum.wave is not None and len(self.appLogic.theoreticalSpectrum.wave)!=0:
            self.updateErrorPlot()


    def updateErrorPlot(self):
        if self.appLogic.normedSpectrum.wave is None or len(self.appLogic.normedSpectrum.wave) == 0 or self.appLogic.theoreticalSpectrum.wave is None:
            self.line31.set_data([], [])
        else:
            mask = self.appLogic.normedSpectrum.flux != 0
            x = self.appLogic.normedSpectrum.wave[mask]
            diff = np.interp(x,
                                 self.appLogic.theoreticalSpectrum.wave,
                                 self.appLogic.theoreticalSpectrum.flux) - self.appLogic.normedSpectrum.flux[mask]
            self.line31.set_data(x, diff)
            diff = np.nan_to_num(diff)
            self.ax3.set_ylim([np.min(diff),np.max(diff)])

    def colorGenerator(self):
        while True:
            yield 'b'
            yield 'g'
            #yield 'r'
            yield 'c'
            yield 'm'

    def onCloseRadialVelocityDialog(self):
        if self.radVelDialog.ifApplyRadialVelocity:
            # TODO: Correct regions for radial velocity? Only in some cases:
            # TODO: For now comment this correction
            #self.appLogic.continuumRegionsLogic.applyRadialVelocity(self.radVelDialog.radialVelocity)
            self.appLogic.applyRadialVelocity(self.radVelDialog.radialVelocity)
            if self.ifAlreadyNormed.get() != 1:
                self.appLogic.normSpectrum()
            else:
                self.onAlreadyNormed()
            #------------ REPLOT
            contRegionsWaveAndFlux = self.appLogic.getContinuumRangesForPlot()
            self.replotUpdatedRanges(contRegionsWaveAndFlux)
        self.radVelDialog.destroy()
        self.radVelDialog = None
        #print("WORKS")


class radialVelocityDialog(tkinter.Toplevel):
    def __init__(self,appLogicClass,closeFunction):
        tkinter.Toplevel.__init__(self)

        self.appLogicClass = appLogicClass

        self.levels=[0.5,0.7,0.9]
        self.ifApplyRadialVelocity = False
        self.radialVelocity=-self.appLogicClass.radialVelocity

        self.close = closeFunction
        self.createPlottingArea()
        self.createControls()



    def createPlottingArea(self):
        self.plotFrame = tkinter.Frame(self)
        self.dpi = 100
        self.fig = Figure((4.0, 3.0), dpi=self.dpi,tight_layout=True)
        self.canvas = FigCanvas(self.fig, master=self.plotFrame)
        self.canvas.draw()
        self.ax = self.fig.add_subplot(111)
        self.ax.plot([0,1],[1,1],'k-')
        self.canvas.draw()
        tkinter.Label(self.plotFrame , text="Cross correlation function").pack()
        self.canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.plotFrame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    def createControls(self):
        self.controlFrame = tkinter.Frame(self)
        WENS = tkinter.W+tkinter.E+tkinter.N+tkinter.S

        tkinter.Label(self.controlFrame , text="Level 1").grid(column=0, row=0)
        tkinter.Label(self.controlFrame , text="Level 2").grid(column=0, row=1)
        tkinter.Label(self.controlFrame , text="Level 3").grid(column=0, row=2)

        spinboxValues = tuple(np.around(np.arange(0,1.01,0.05),2))
        var1 = tkinter.DoubleVar()
        var2 = tkinter.DoubleVar()
        var3 = tkinter.DoubleVar()
        self.sp1 = tkinter.Spinbox(self.controlFrame,\
                              values=spinboxValues,\
                              state='readonly',\
                              textvariable=var1,\
                              command=self.onSpinBox)
        var1.set(self.levels[0])
        self.sp1.grid(column=1, row=0)

        self.sp2 = tkinter.Spinbox(self.controlFrame,\
                              values=spinboxValues,\
                              state='readonly',\
                              textvariable=var2,\
                              command=self.onSpinBox)
        var2.set(self.levels[1])
        self.sp2.grid(column=1, row=1)

        self.sp3 = tkinter.Spinbox(self.controlFrame,\
                              values=spinboxValues,\
                              state='readonly',\
                              textvariable=var3,\
                              command=self.onSpinBox)
        var3.set(self.levels[2])
        self.sp3.grid(column=1, row=2)

        reject = tkinter.Button(self.controlFrame , text="Reject", command=self.onReject)
        reject.grid(column=0, row=3, columnspan = 2, sticky = WENS)

        #-----------------------------------------------------------------------

        tkinter.Label(self.controlFrame , text="Minimum wavelength").grid(column=2, row=0)
        tkinter.Label(self.controlFrame , text="Maximum wavelength").grid(column=2, row=1)
        tkinter.Label(self.controlFrame , text="Velocity step").grid(column=2, row=2)
        tkinter.Label(self.controlFrame , text="Maximum velocity").grid(column=2, row=3)

        self.minWave = tkinter.Entry(self.controlFrame)
        self.minWave.grid(column=3, row=0)
        self.minWave.insert(tkinter.END, 4450.0)

        self.maxWave = tkinter.Entry(self.controlFrame)
        self.maxWave.grid(column=3, row=1)
        self.maxWave.insert(tkinter.END, 4700.0)

        self.velocityStep = tkinter.Entry(self.controlFrame)
        self.velocityStep.insert(tkinter.END, 0.5)
        self.velocityStep.grid(column=3, row=2)

        self.maxVelocity = tkinter.Entry(self.controlFrame)
        self.maxVelocity.insert(tkinter.END, 200)
        self.maxVelocity.grid(column=3, row=3)

        #-----------------------------------------------------------------------

        self.text = tkinter.Text(self.controlFrame, wrap="word",height=1,width=15)
        self.text.grid(column=4, row=0)
        self.text.insert(tkinter.END,-self.appLogicClass.radialVelocity)
        radVel = tkinter.Button(self.controlFrame, text="Compute velocity", command=self.onComputeVelocity)
        radVel.grid(column=4, row=1, sticky = WENS)

        applyChanges = tkinter.Button(self.controlFrame, text="Apply correction", command=self.onApplyChanges)
        applyChanges.grid(column=4, row=2,rowspan=2, sticky = WENS)
        #-----------------------------------------------------------------------

        self.controlFrame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    def onSpinBox(self):
        self.levels = [float(self.sp1.get()),float(self.sp2.get()),float(self.sp3.get())]

    def onComputeVelocity(self):
        # print(float(self.minWave.get()),float(self.maxWave.get()),\
        #       float(self.maxVelocity.get()),float(self.velocityStep.get()))
        self.radialVelocity = self.appLogicClass.radialVelocityEstimator.getRadialVelocity(
                                   self.appLogicClass.spectrum.wave,\
                                   self.appLogicClass.spectrum.flux,\
                                   self.appLogicClass.theoreticalSpectrum.wave,\
                                   self.appLogicClass.theoreticalSpectrum.flux,\
                                   minWave=float(self.minWave.get()),\
                                   maxWave=float(self.maxWave.get()),\
                                   velocityMax=float(self.maxVelocity.get()),\
                                   velocityStep=float(self.velocityStep.get()),\
                                   quiet=True,\
                                   levels=self.levels)
        self.text.delete("1.0", "end")  # if you want to remove the old data
        self.text.insert(tkinter.END,self.radialVelocity)
        self.updatePlot()

    def onApplyChanges(self):
        try:
            self.radialVelocity = np.round(float(self.text.get("1.0",tkinter.END)),1)
        except:
            self.text.delete("1.0", "end")
            self.text.insert(tkinter.END,"Write number!")
        else:
            self.ifApplyRadialVelocity = True
            self.close()


    def updatePlot(self):
        self.ax.clear()
        self.ax.plot(self.appLogicClass.radialVelocityEstimator.velCCF,
                            self.appLogicClass.radialVelocityEstimator.ccf)
        maxCCF=np.max(self.appLogicClass.radialVelocityEstimator.ccf)
        minCCF=np.min(self.appLogicClass.radialVelocityEstimator.ccf)
        for divide,(r1,r2) in zip(self.levels,self.appLogicClass.radialVelocityEstimator.fitRoots):
            self.ax.plot([r1,r2],[(maxCCF-minCCF)*divide+minCCF,\
                            (maxCCF-minCCF)*divide+minCCF],\
                            'k-')
            self.ax.plot([(r1+r2)/2,(r1+r2)/2],\
                        [(maxCCF-minCCF)*divide+minCCF-(maxCCF-minCCF)/20,\
                        (maxCCF-minCCF)*divide+minCCF+(maxCCF-minCCF)/20],\
                        'k-')
        self.ax.set_autoscale_on(True)
        self.ax.relim()
        self.ax.autoscale_view(True,True,True)
        self.canvas.draw()

    def onReject(self):
        self.close()
        #self.destroy()


def main():

    app=NormSpectra()
    w, h = app.winfo_screenwidth(), app.winfo_screenheight()
    app.geometry("%dx%d+0+0" % (w, h))
    app.mainloop()


if __name__ == '__main__':
    main()
