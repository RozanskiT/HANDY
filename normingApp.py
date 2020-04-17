#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

import tkinter
from tkinter import ttk
from tkinter.font import Font
import tkinter.filedialog as filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar
# from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar
from matplotlib.backend_bases import key_press_handler
from matplotlib.widgets import SpanSelector
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter, MaxNLocator
from matplotlib.collections import LineCollection
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

    def __init__(self):
        tkinter.Tk.__init__(self)
        self.__initAttributes__()
        self.createMainWindow()

    def createMainWindow(self):
        self.WENS = tkinter.W+tkinter.E+tkinter.N+tkinter.S
        self.createWindow()
        self.createControls()
        self.createMenu()
        self.createPlottingArea()
        
    def createWindow(self):
        self.frame = tkinter.Frame(self)
        self.frame.pack(fill=tkinter.BOTH, expand=1)
        self.wm_title("HANDY - Handy tool for spectra normalization")

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
        fileMenu2.add_command(label="Save notes",\
                              command=self.onSaveNotes)                           
        fileMenu2.add_separator()
        fileMenu2.add_command(label="Save all",\
                        command=self.onSaveAll) 
        #------------------------------------
        fileMenu3 = tkinter.Menu(menu)
        menu.add_cascade(label="Spectrum", underline=0, menu=fileMenu3)
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
        fileMenu3.add_separator()
        self._syntheNumber = len(lG)
        fileMenu3.add_radiobutton(label = "SYNTHE",
                            var = self.vlevel,
                            value = len(lG),
                            command = self.onChooseSYNTHE
                            )
        #------------------------------------
        fileMenu4 = tkinter.Menu(menu)
        menu.add_cascade(label="Line labels", underline=0, menu=fileMenu4)

        self.labelSettings = tkinter.IntVar()
        self.labelSettings.set(0)

        fileMenu4.add_radiobutton(label="No labels", value=0, variable=self.labelSettings, command = self.onCheckLabelSettings)
        fileMenu4.add_separator()
        fileMenu4.add_radiobutton(label="Show all", value=1, variable=self.labelSettings, command = self.onCheckLabelSettings)
        fileMenu4.add_radiobutton(label="On hower", value=2, variable=self.labelSettings, command = self.onCheckLabelSettings)

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
        self.vmacScale['state'] = setVal[True]
        self.vsiniScale['state'] = setVal[True]
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

    def onChooseSYNTHE(self):
        setVal = {True: 'normal', False: 'disabled'}
        self.vmacScale['state'] = setVal[False]
        self.vsiniScale['state'] = setVal[True]
        self.teffScale['state'] = setVal[True]
        self.loggScale['state'] = setVal[True]
        self.vmicScale['state'] = setVal[True]
        self.meScale['state'] = setVal[True]

        self.teffScale['from_'], self.teffScale['to'] = 4000, 35000
        self.loggScale['from_'], self.loggScale['to'] = 2.0, 6.0
        self.vmicScale['from_'], self.vmicScale['to'] = 0.0, 15.0
        self.meScale['from_'], self.meScale['to'] = -3.0, 0.6

    def onCheckLabelSettings(self):
        self.updateLinesAnnotations()
        self.canvas.draw()


    def onOpenSpectrum(self):
        dirname = os.getcwd()
        ftypes = [('All files', '*'),('FITS files', '*fits'),('Plain text', '*.txt *.dat')]
        answer = filedialog.askopenfilenames(title="Open spectrum...", initialdir=dirname, filetypes=ftypes)
        if answer:
            self.fileList = answer
            fileName = self.fileList[0]
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

        self.updateNotesOnNewSpectrum()

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

    def onSaveNormedSpectrum(self, verbose=True):
        initialName = "out.norm"
        if self.appLogic.spectrum.name is not None:
            fileName = os.path.splitext(self.appLogic.spectrum.name)[0] + ".norm"
        if verbose:
            initialName = os.path.basename(fileName)
            fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.spectrum.wave is not None and len(self.appLogic.spectrum.wave) != 0:
            # self.appLogic.saveNormedSpectrum(fileName,self.ifSaveCorrectedvrad.get())
            self.appLogic.saveNormedSpectrum(fileName,False)

    def onSaveVelocityCorrectedNormedSpectrum(self, verbose=True):
        initialName = "out_rv.norm"
        if self.appLogic.spectrum.name is not None:
            fileName = os.path.splitext(self.appLogic.spectrum.name)[0] + "_rv.norm"
        if verbose:
            initialName = os.path.basename(fileName)
            fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.spectrum.wave is not None and len(self.appLogic.spectrum.wave) != 0:
            self.appLogic.saveNormedSpectrum(fileName,True)
            # self.appLogic.saveSpectrum(fileName)

    def onSaveContinuum(self, verbose=True):
        initialName = "out.cont"
        if self.appLogic.spectrum.name is not None:
            fileName = os.path.splitext(self.appLogic.spectrum.name)[0] + ".cont"
        if verbose:
            initialName = os.path.basename(fileName)
            fileName = filedialog.asksaveasfilename(initialfile=initialName)
        if fileName and self.appLogic.spectrum.wave is not None and len(self.appLogic.spectrum.wave) != 0:
            self.appLogic.continuumRegionsLogic.saveRegionsFile(self.appLogic.spectrum,\
                                                                fileName)

    def onSaveTheoreticalSpectrum(self, verbose=True):
        initialName = "out.syn"
        if self.appLogic.spectrum.name is not None:
            fileName = os.path.splitext(self.appLogic.spectrum.name)[0] + ".syn"
        if verbose:
            initialName = os.path.basename(fileName)
            fileName = filedialog.asksaveasfilename(initialfile=initialName)
        print(fileName)
        if fileName and self.appLogic.theoreticalSpectrum.wave is not None and len(self.appLogic.theoreticalSpectrum.wave) != 0:
            self.appLogic.saveTheoreticalSpectrum(fileName)

    def onSaveAll(self):
        self.onSaveNormedSpectrum(verbose=False)
        self.onSaveVelocityCorrectedNormedSpectrum(verbose=False)
        self.onSaveContinuum(verbose=False)
        self.onSaveTheoreticalSpectrum(verbose=False)
        self.onSaveNotes()

    def createControls(self):
        # Create several frames for grouping buttons
        self.controlNote = ttk.Notebook(self.frame)

        self.controlFrameA=tkinter.Frame(self.controlNote)
        self.controlFrameB=tkinter.Frame(self.controlNote)
        self.controlFrameC=tkinter.Frame(self.controlNote)
        self.controlFrameD=tkinter.Frame(self.controlNote)
        self.controlFrameE=tkinter.Frame(self.controlNote)
        

        self.createNormalizationControls()
        self.createModellingControls()
        self.createOutputPlotControls()
        self.createLabelControls()
        self.createSpectrumNotes()

        self.controlFrameA.pack()
        self.controlFrameB.pack()
        self.controlFrameC.pack()
        self.controlFrameD.pack()
        self.controlFrameE.pack()

        self.controlNote.add(self.controlFrameA, text = "Controls")
        self.controlNote.add(self.controlFrameB, text = "Model")
        self.controlNote.add(self.controlFrameC, text = "Plot")
        self.controlNote.add(self.controlFrameD, text = "Labels")
        self.controlNote.add(self.controlFrameE, text = "Notes")

        self.controlNote.pack(fill=tkinter.BOTH, expand=0)

    def createNormalizationControls(self):
        
        #=======================================================================
        self.bttn11 = tkinter.Button(self.controlFrameA,\
                                    text = "Back",\
                                    command = self.onBack)
        self.bttn11.grid(row = 0, column = 0, sticky = self.WENS)

        self.bttn21 = tkinter.Button(self.controlFrameA,\
                                    text = "Choose region",\
                                    command = self.onChooseActiveRegion)
        self.bttn21.grid(row = 1, column = 0, sticky = self.WENS)

        self.bttn31 = tkinter.Button(self.controlFrameA,\
                                     text = "Create region",\
                                     command = self.onCreateNewActiveRegion)
        self.bttn31.grid(row = 2, column = 0, sticky = self.WENS)

        #-----------------------------------------------------------------------
        self.bttn12 = tkinter.Button(self.controlFrameA,\
                                     text = "Next spectrum",\
                                     command = self.onNextSpectrum)
        self.bttn12.grid(row = 0, column = 1, sticky = self.WENS)

        self.bttn22 = tkinter.Button(self.controlFrameA,\
                                    text = "Add special point",\
                                    command = self.onAddSpecialPoint)
        self.bttn22.grid(row = 1, column = 1, sticky = self.WENS)

        self.bttn32 = tkinter.Button(self.controlFrameA,\
                                    text = "Auto fit special points",\
                                    command = self.onAutoFitSpecialPoints)
        self.bttn32.grid(row = 2, column = 1, sticky = self.WENS)

        # self.bttn42 = tkinter.Label(self.controlFrameA, text=" <--- Adjust order")
        # self.bttn42.grid(row = 3, column = 1, sticky = self.WENS)
        #-----------------------------------------------------------------------
        self.bttn13 = tkinter.Button(self.controlFrameA,\
                                     text = "Normalize",\
                                     command = self.onNormalize)
        self.bttn13.grid(row = 0, column = 2, sticky = self.WENS)

        self.bttn23 = tkinter.Button(self.controlFrameA,\
                                    text = "Auto update",\
                                    command = self.onSetAutoUpdateNormalization)
        self.bttn23.grid(row = 1, column = 2, sticky = self.WENS)

        self.bttn33 = tkinter.Button(self.controlFrameA,\
                                    text = "Radial velocity",\
                                    command = self.onRadialVelocity)
        self.bttn33.grid(row = 2, column = 2, sticky = self.WENS)
        #=======================================================================

        self.currentOrder = tkinter.StringVar()
        self.bttn14 = tkinter.Spinbox(self.controlFrameA,\
                                        from_=1,\
                                        to=10,\
                                        width=2,\
                                        command=self.onUpdateOrder,\
                                        textvariable=self.currentOrder,\
                                        state = "readonly",\
                                        font = Font(size=12)
                                        )
                                     # text = "Create new active region",\
                                     # command = self.onCreateNewActiveRegion)
        self.bttn14.grid(row = 0, column = 3, rowspan = 3, sticky = self.WENS)

        self.backgroundColor = self.bttn11.cget("bg")
        self.activeBackground = self.bttn11.cget("activebackground")

    def createModellingControls(self):
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
                                        # length = 400,
                                        )
        self.teffScale.grid(row = 0, column = 0, columnspan = 2, sticky = self.WENS)

        self.loggScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.loggVar,
                                        orient = hor,
                                        label = "logg",
                                        from_ = 3.0,
                                        to = 4.5,
                                        resolution = 0.05,
                                        length = 250,
                                        )
        self.loggScale.grid(row = 1, column = 0, sticky = self.WENS)

        self.vmicScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.vmicVar,
                                        orient = hor,
                                        label = 'vmic',
                                        from_ = 0,
                                        to = 15,
                                        resolution = 1,
                                        length = 250,
                                        )
        self.vmicScale.grid(row = 1, column = 1, sticky = self.WENS)

        self.vmacScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.vmacVar,
                                        orient = hor,
                                        label = "vmac",
                                        from_ = 0,
                                        to = 50,
                                        resolution = 1,
                                        length = 250,
                                        )
        self.vmacScale.grid(row = 0, column = 2, sticky = self.WENS)


        self.vsiniScale = tkinter.Scale(self.controlFrameB,
                                        variable = self.vsiniVar,
                                        orient = hor,
                                        label = "vsini",
                                        from_ = 0,
                                        to = 200,
                                        resolution = 1,
                                        length = 150,
                                        )
        self.vsiniScale.grid(row = 1, column = 2, sticky = self.WENS)

        self.meScale = tkinter.Scale(self.controlFrameB,
                                    variable = self.meVar,
                                    orient = hor,
                                    label = "[M/H]",
                                    from_ = -1, #TODO work around low metallicity bug
                                    to = 0.3,
                                    resolution = 0.1,
                                    length = 250,
                                    )
        self.meScale.grid(row = 0, column = 3, columnspan = 2, sticky = self.WENS)

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
        self.resolutionLabel.grid(row = 1, column = 3, sticky = self.WENS)

        self.resolutionScale = tkinter.Spinbox(self.controlFrameB,
                                textvariable = self.resolution,
                                values = (1000,2000,5000,10000,20000,50000,100000,np.inf),
                                state = 'readonly',
                                width = 7,
                                )
        self.resolution.set(np.inf) # Must be like that :(
        self.resolutionScale.grid(row = 1, column = 4, sticky = self.WENS)

        self.bttnClearTheorSpec = tkinter.Button(self.controlFrameB,\
                                    text = "Clear\ntheoretical\nspectrum",\
                                    command = self.onClearTheoreticalSpectrum)
        self.bttnClearTheorSpec.grid(row = 0, column = 5, rowspan = 1, sticky = self.WENS)

        self.bttnLoadTheorSpec = tkinter.Button(self.controlFrameB,\
                                    text = "Compute\ntheoretical\nspectrum",\
                                    command = self.onComputeTheoreticalSpectrum)
        self.bttnLoadTheorSpec.grid(row = 1, column = 5, rowspan = 1, sticky = self.WENS)

        self.ifAlreadyNormed = tkinter.IntVar()
        self.workWithNormedSpectrum = tkinter.Checkbutton(self.controlFrameB,
                                                        text = "Already\nnormalised\nspectrum?",
                                                        variable = self.ifAlreadyNormed,
                                                        command = self.onAlreadyNormed,
                                                        )
        self.workWithNormedSpectrum.grid(row = 0, column = 6,rowspan=2, sticky = self.WENS)

    def createOutputPlotControls(self):
        self.bttnOpenSaveWindow = tkinter.Button(self.controlFrameC,\
                                    text = "Plot fitted spectrum",\
                                    command = self.onOpenSavePlot)
        self.bttnOpenSaveWindow.grid(row = 2, column = 0, sticky = self.WENS)

    def createLabelControls(self):
        self._visibility_depth = tkinter.DoubleVar(value = 0.95)
        self.appLogic.setLabelsThreshold(self._visibility_depth.get())
        self.labelScale = tkinter.Scale(self.controlFrameD,
                            variable = self._visibility_depth,
                            orient = tkinter.HORIZONTAL,
                            label = "Line depth",
                            from_ = 0,
                            to = 1,
                            resolution = 0.01,
                            command = self.onUpdateLabelDepth,
                            length = 200,
                            )
        self.labelScale.pack(anchor="w")

    def createSpectrumNotes(self):

        topframe = tkinter.Frame(self.controlFrameE)
        topframe.pack(side=tkinter.TOP)   

        self.spectrumBasenameVar = tkinter.StringVar()
        tkinter.Label(topframe, textvariable=self.spectrumBasenameVar).pack(side=tkinter.LEFT)
        self.spectrumBasenameVar.set("Spectrum name: " + self.appLogic.getSpectrumBaseName())
        note_data = self.appLogic.getNoteData()

        bottomframe = tkinter.Frame(self.controlFrameE)
        bottomframe.pack(side=tkinter.BOTTOM, expand=0)  

        leftbottomframe = tkinter.Frame(bottomframe)
        leftbottomframe.pack(side=tkinter.LEFT, expand=0)

        rightbottomframe = tkinter.Frame(bottomframe)
        rightbottomframe.pack(side=tkinter.LEFT, expand=0) 
        #-------------------------------------- TEFF
        self.noteTeff = tkinter.StringVar()
        self.noteTeffLabel = tkinter.Label(leftbottomframe,
                                        text = "teff",
                                        )
        self.noteTeffEntry = tkinter.Entry(leftbottomframe,
                                            textvariable = self.noteTeff,
                                            )
        self.noteTeff.set(note_data['teff'])
        self.noteTeffLabel.grid(row = 1, column = 1, sticky = self.WENS)
        self.noteTeffEntry.grid(row = 1, column = 2, sticky = self.WENS)
        #-------------------------------------- LOGG
        self.noteLogg = tkinter.StringVar()
        self.noteLoggLabel = tkinter.Label(leftbottomframe,
                                        text = "logg",
                                        )
        self.noteLoggEntry = tkinter.Entry(leftbottomframe,
                                            textvariable = self.noteLogg,
                                            )
        self.noteLogg.set(note_data['logg'])
        self.noteLoggLabel.grid(row = 2, column = 1, sticky = self.WENS)
        self.noteLoggEntry.grid(row = 2, column = 2, sticky = self.WENS)
        #-------------------------------------- ME
        self.noteMe = tkinter.StringVar()
        self.noteMeLabel = tkinter.Label(leftbottomframe,
                                        text = "me",
                                        )
        self.noteMeEntry = tkinter.Entry(leftbottomframe,
                                            textvariable = self.noteMe,
                                            )
        self.noteMe.set(note_data['me'])
        self.noteMeLabel.grid(row = 3, column = 1, sticky = self.WENS)
        self.noteMeEntry.grid(row = 3, column = 2, sticky = self.WENS)
        #========================================
        #-------------------------------------- VMIC
        self.noteVmic = tkinter.StringVar()
        self.noteVmicLabel = tkinter.Label(leftbottomframe,
                                        text = "vmic",
                                        )
        self.noteVmicEntry = tkinter.Entry(leftbottomframe,
                                            textvariable = self.noteVmic,
                                            )
        self.noteVmic.set(note_data['vmic'])
        self.noteVmicLabel.grid(row = 1, column = 3, sticky = self.WENS)
        self.noteVmicEntry.grid(row = 1, column = 4, sticky = self.WENS)
        #-------------------------------------- VSINI
        self.noteVsini = tkinter.StringVar()
        self.noteVsiniLabel = tkinter.Label(leftbottomframe,
                                        text = "vsini",
                                        )
        self.noteVsiniEntry = tkinter.Entry(leftbottomframe,
                                            textvariable = self.noteVsini,
                                            )
        self.noteVsini.set(note_data['vsini'])
        self.noteVsiniLabel.grid(row = 2, column = 3, sticky = self.WENS)
        self.noteVsiniEntry.grid(row = 2, column = 4, sticky = self.WENS)
        #-------------------------------------- VMAC
        self.noteVmac = tkinter.StringVar()
        self.noteVmacLabel = tkinter.Label(leftbottomframe,
                                        text = "vmac",
                                        )
        self.noteVmacEntry = tkinter.Entry(leftbottomframe,
                                            textvariable = self.noteVmac,
                                            )
        self.noteVmac.set(note_data['vmac'])
        self.noteVmacLabel.grid(row = 3, column = 3, sticky = self.WENS)
        self.noteVmacEntry.grid(row = 3, column = 4, sticky = self.WENS)

        #======================================= Notes
        self.noteText = tkinter.StringVar()
        self.noteTextDisplay = tkinter.Text(rightbottomframe,height=5)
        self.noteText.set(note_data['text_notes'])
        self.noteTextDisplay.insert(tkinter.INSERT, self.noteText.get())        
        self.noteTextDisplay.pack(side=tkinter.LEFT, expand=True, fill=tkinter.Y)

        #======================================= SAVE NOTES BUTTON
        self.noteSaveBttn = tkinter.Button(rightbottomframe,\
                            text = "Save notes",\
                            command = self.onSaveNotes)
        self.noteSaveBttn.pack(side=tkinter.LEFT, expand=True, fill=tkinter.Y)

        self.noteGetParamsBttn = tkinter.Button(rightbottomframe,\
                            text = "Get paramters\nfrom model",\
                            command = self.onGetParamsFromModel)
        self.noteGetParamsBttn.pack(side=tkinter.LEFT, expand=True, fill=tkinter.Y)

        self.noteSetParamsBttn = tkinter.Button(rightbottomframe,\
                            text = "Set model\nfrom notes",\
                            command = self.onSetModelFromNotes)
        self.noteSetParamsBttn.pack(side=tkinter.LEFT, expand=True, fill=tkinter.Y)

    def onSaveNotes(self):
        note_data = {
            "text_notes": self.noteTextDisplay.get("1.0",tkinter.END),
            "teff": self.noteTeff.get(),
            "logg": self.noteLogg.get(),
            "me": self.noteMe.get(),
            "vmic": self.noteVmic.get(),
            "vsini": self.noteVsini.get(),
            "vmac": self.noteVmac.get(),
        }
        self.appLogic.setNoteData(note_data)
    
    def updateNotesOnNewSpectrum(self):
        self.spectrumBasenameVar.set("Spectrum name: " + self.appLogic.getSpectrumBaseName())
        note_data = self.appLogic.getNoteData()

        self.noteTeff.set(note_data['teff'])
        self.noteLogg.set(note_data['logg'])
        self.noteMe.set(note_data['me'])
        self.noteVmic.set(note_data['vmic'])
        self.noteVsini.set(note_data['vsini'])
        self.noteVmac.set(note_data['vmac'])
        self.noteText.set(note_data['text_notes'])

        self.noteTextDisplay.delete("1.0", tkinter.END)
        self.noteTextDisplay.insert(tkinter.INSERT, self.noteText.get())

    def onGetParamsFromModel(self):
        self.noteTeff.set(self.teffVar.get())
        self.noteLogg.set(self.loggVar.get())
        self.noteMe.set(self.meVar.get())
        self.noteVmic.set(self.vmicVar.get())
        self.noteVsini.set(self.vsiniVar.get())
        self.noteVmac.set(self.vmacVar.get())

    def onSetModelFromNotes(self):
        self.teffVar.set(self.noteTeff.get())
        self.loggVar.set(self.noteLogg.get())
        self.meVar.set(self.noteMe.get())
        self.vmicVar.set(self.noteVmic.get())
        self.vsiniVar.set(self.noteVsini.get())
        self.vmacVar.set(self.noteVmac.get())  

    def onUpdateLabelDepth(self, value):
        self.appLogic.setLabelsThreshold(self._visibility_depth.get())
        self.updateLinesAnnotations()
        self.canvas.draw()

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
            self.spanNormalization.set_visible(False)
        if self.ifChooseActiveRegion:
            self.spanNormalization.set_visible(False)
        if boolKeyVar:
            button.configure(bg = "#567",activebackground="#678")
        else:
            self.spanNormalization.set_visible(True)
            button.configure(bg = self.backgroundColor,activebackground=self.activeBackground)

    def resetButtons(self):
        self.bttn21.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.bttn31.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.bttn22.configure(bg = self.backgroundColor,activebackground=self.activeBackground)
        self.spanNormalization.set_visible(True)

    def onNextSpectrum(self):
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
        if self.vlevel.get() == self._syntheNumber:
            self.getTheoreticalSpectrumUsingSynthe()
        else:
            self.getTheoreticalSpectrumFromGrid()
        self.updateTheoreticalSpectrumPlot()
        self.updateLinesAnnotations()
        if self.appLogic.theoreticalSpectrum.wave is not None and len(self.appLogic.theoreticalSpectrum.wave)!=0:
            self.updateErrorPlot()
        self.canvas.draw()
    
    def updateTheoreticalSpectrumPlot(self):
        wave = self.appLogic.theoreticalSpectrum.wave if self.appLogic.theoreticalSpectrum.wave is not None else []
        flux = self.appLogic.theoreticalSpectrum.flux if self.appLogic.theoreticalSpectrum.flux is not None else []
        self.line23.set_data(wave,flux)

    def updateLinesAnnotations(self):
        for i in range(len(self.lines_annotations)): # Remove existing texts from axis and empty list
            self.lines_annotations[-1].remove()
            self.lines_annotations.pop()
        self.lines_indicators.set_segments([])

        if self.appLogic.theoreticalSpectrum.lines_identification is not None:
            segments = self.appLogic.getLinesIdentification(shape=self.labelSettings.get())
            self.lines_indicators.set_segments(segments)   
            if self.labelSettings.get() == 1:
                texts, positions = self.appLogic.getLabelsAndPositions()
                for text, (x,y) in zip(texts, positions):
                    self.lines_annotations.append(self.ax2.text(x, y, text, rotation=90, ha='right', va='bottom'))

    def onHover(self, event):
        if event.inaxes == self.ax2 and self.labelSettings.get() == 2:
            cont, ind = self.lines_indicators.contains(event)
            if cont :
                self.upateAnnotation(ind, event)
                self.line_annotation.set_visible(True)
                self.canvas.draw()
            else:
                if self.line_annotation.get_visible():
                    self.line_annotation.set_visible(False)
                    self.canvas.draw()

    def upateAnnotation(self, ind, event):
        pos = (event.xdata, event.ydata)
        self.line_annotation.xy = pos
        text = "{}".format("; ".join([self.appLogic.getLineLabelText(n) for n in ind["ind"]]))

        self.line_annotation.set_text(text)
        self.line_annotation.get_bbox_patch().set_facecolor('w')
        self.line_annotation.get_bbox_patch().set_alpha(0.9)


    def getTheoreticalSpectrumUsingSynthe(self):
        minWave, maxWave = self.ax1.get_xlim()
        self.appLogic.computeSpectrumUsingSYNTHE(self.teffVar.get(),
                                                self.loggVar.get(),
                                                self.vmicVar.get(),
                                                self.meVar.get(),
                                                self.vsiniVar.get(),
                                                self.vmacVar.get(),
                                                float(self.resolution.get()),
                                                minWave,
                                                maxWave
                                                )

    def getTheoreticalSpectrumFromGrid(self):
        self.appLogic.computeTheoreticalSpectrum(self.teffVar.get(),
                                                self.loggVar.get(),
                                                self.vmicVar.get(),
                                                self.meVar.get(),
                                                self.vsiniVar.get(),
                                                self.vmacVar.get(),
                                                float(self.resolution.get()),
                                                )

    def onClearTheoreticalSpectrum(self):
        self.appLogic.theoreticalSpectrum.wave = None
        self.appLogic.theoreticalSpectrum.flux = None
        self.appLogic.theoreticalSpectrum.lines_identification = None
        self.line23.set_data([],[])
        self.updateLinesAnnotations()
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
                                                            [],[],'b--',\
                                                            [],[],'b')
        self.lines_indicators = self.ax2.add_collection(LineCollection([], colors='#FF8800'))
        self.lines_annotations = []
        self.line_annotation = self.ax2.annotate("", xy=(0,0), 
                                    xytext=(20,20),
                                    # rotation=90,
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w"),
                                    arrowprops=dict(arrowstyle="->"), 
                                    zorder=40)
        self.line_annotation.set_visible(False)

        # self.ax3 = self.fig.add_subplot(313,sharex=self.ax1)
        self.ax3 = self.fig.add_subplot(gs[-1],sharex=self.ax1)
        self.ax3.grid(True)
        self.ax3.yaxis.set_major_locator(MaxNLocator(nbins=3,prune='upper'))
        self.line31, = self.ax3.plot([],[],'b')

        self.ax1.set_autoscaley_on(True)
        #self.ax2.set_autoscaley_on(False)
        self.ax2.set_ylim([0.1,2.0])

        box = self.ax1.get_position()

        self.canvas.mpl_connect('button_press_event', self.onPlotClick)
        self.canvas.mpl_connect('button_release_event', self.onPlotRealise)
        self.canvas.mpl_connect('motion_notify_event', self.onHover)
        self.canvas.mpl_connect('key_press_event', self.onKeyPress)
        self.toolbar = NavigationToolbar(self.canvas, self.plotFrame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.plotFrame.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

        #span selector
        self.spanNormalization = SpanSelector(self.ax1, self.onUsingSpanSelector,\
                                 'horizontal', useblit=True,\
                                 rectprops=dict(alpha=0.5, facecolor='red'),\
                                 button=1)

        self.spanLinesOutput = SpanSelector(self.ax2, self.onAnalysisOutput,\
                                 'horizontal', useblit=True,\
                                 rectprops=dict(alpha=0.5, facecolor='blue'),\
                                 button=1)

        #self.spanNormalization.set_visible(False)

    def onKeyPress(self,event):
        if event.key == 'n':
            self.onNextSpectrum()
        key_press_handler(event, self.canvas, self.toolbar)
        # print("TODO: add some shortcuts to buttons")

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

    def onAnalysisOutput(self, xmin, xmax):
        self.appLogic.analysisOutput(xmin, xmax)
        print(xmin, xmax)

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
        self.WENS = tkinter.W+tkinter.E+tkinter.N+tkinter.S

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
        reject.grid(column=0, row=3, columnspan = 2, sticky = self.WENS)

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
        radVel.grid(column=4, row=1, sticky = self.WENS)

        applyChanges = tkinter.Button(self.controlFrame, text="Apply correction", command=self.onApplyChanges)
        applyChanges.grid(column=4, row=2,rowspan=2, sticky = self.WENS)
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
