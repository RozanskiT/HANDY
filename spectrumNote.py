#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os, sys
import numpy as np
import yaml

"""
DESCRIPTION

Handling the note that is associated with spectrum name.
"""

class spectrumNote:

    def __init__(self, spectrum_path=None):
        self._text_notes = None
        self._teff = None
        self._logg = None
        self._me = None
        self._vmic = None
        self._vsini = None
        self._vmac = None

        if spectrum_path is not None:
            self.set_spectrum(spectrum_path)
        else:
            self._note_path = None
            self.spectrum_path = None

    def set_spectrum(self, spectrum_path):
        self.spectrum_path = spectrum_path
        self._note_path = self.get_default_note_path()
        try:
            if os.path.exists(self._note_path):
                self.read_note()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print(f"Note {self._note_path} unreadible...")

    def update_parameter(self):
        self.save_note()

    def save_note(self):
        note_dict = {
            "spectrum": self.spectrum_path,
            "text_notes": self._text_notes,
            "teff": self._teff,
            "logg": self._logg,
            "me": self._me,
            "vmic": self._vmic,
            "vsini": self._vsini,
            "vmac": self._vmac,
        }
        with open(self._note_path,'w') as f:
            yaml.safe_dump(note_dict, f)

    def get_note_data(self):
        note_dict = {
            "spectrum": self.spectrum_path,
            "text_notes": self._text_notes,
            "teff": self._teff,
            "logg": self._logg,
            "me": self._me,
            "vmic": self._vmic,
            "vsini": self._vsini,
            "vmac": self._vmac,
        }
        return note_dict

    def set_from_dict(self, note_dict):
        self._text_notes = note_dict["text_notes"]
        self._teff = note_dict["teff"]
        self._logg = note_dict["logg"] 
        self._me = note_dict["me"] 
        self._vmic = note_dict["vmic"]
        self._vsini = note_dict["vsini"] 
        self._vmac = note_dict["vmac"]
        self.update_parameter()

    def read_note(self):
        with open(self._note_path,'r') as f:
            note_dict = yaml.safe_load(f)
            self.spectrum_path = note_dict["spectrum"]
            self._text_notes = note_dict["text_notes"]
            self._teff = note_dict["teff"]
            self._logg = note_dict["logg"] 
            self._me = note_dict["me"] 
            self._vmic = note_dict["vmic"]
            self._vsini = note_dict["vsini"] 
            self._vmac = note_dict["vmac"]

    
    def get_default_note_path(self):
        default_note_path = "out.note"
        if self.spectrum_path is not None:
            default_note_path = os.path.splitext(self.spectrum_path)[0] + ".note"
        return default_note_path

    @property
    def teff(self): 
        return self._teff

    @teff.setter
    def teff(self, teff):
        self._teff = teff
        self.update_parameter()

    @property
    def logg(self): 
        return self._logg
    
    @logg.setter
    def logg(self, logg):
        self._logg = logg
        self.update_parameter()

    @property
    def me(self): 
        return self._me

    @me.setter
    def me(self, me):
        self._me = me
        self.update_parameter()

    @property
    def vmic(self): 
        return self._vmic

    @vmic.setter
    def vmic(self, vmic):
        self._vmic = vmic
        self.update_parameter()

    @property
    def vsini(self): 
        return self._vsini

    @vsini.setter
    def vsini(self, vsini):
        self._vsini = vsini
        self.update_parameter()

    @property
    def vmac(self): 
        return self._vmac

    @vmac.setter
    def vmac(self, vmac):
        self._vmac = vmac
        self.update_parameter()

    @property
    def text_notes(self): 
        return self._text_notes

    @text_notes.setter
    def text_notes(self, text_notes):
        self._text_notes = text_notes
        self.update_parameter()

    
def main():
    note = spectrumNote("/home/tr/repos/HANDY/exampleDataMy/803432iuw_rv.dat")
    note.vsini = 200

    note2 = spectrumNote("/home/tr/repos/HANDY/exampleDataMy/803432iuw_rv.dat")
    print(note2.vsini)
    
if __name__ == '__main__':
	main()
