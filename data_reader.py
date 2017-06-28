# -*- coding: utf-8 -*-
import zipfile
import os
import io
import sys
import glob
import xml.etree.ElementTree as ET


def uxd_reader(file_name):
    """
    Scans the uxd file, for every intensity value, saves all relevant motor coordinates and sensor values.
    All values are save in temporary SPEC-style tmp file.
    """
    #Check encoding: utf8 or latin1
    try:
        infile = io.open(file_name, "r", encoding="utf8")
        data = infile.read()
        infile.close()
        coding="utf8"
    except:
        data = io.open(file_name, "r", encoding="latin1")
        data = infile.read()
        infile.close()
        coding="latin1"
    try:
        infile = io.open(file_name, "r", encoding=coding)
    except:
        return "encoding error", 0, 0
    #sys.stdout.write("Reading raw data file...\n")
    i = 0.
    outfile = open("tmp", "w", encoding='utf8')
    outfile.write("#temperature   khi   phi   x   y   theta   offset   2theta   scanning motor   intensity\n")
    for line in infile:
        i += 1.
        #sys.stdout.write("\r%d %% complete" %(100*i/Nlignes))
        #sys.stdout.flush()
        if line.startswith("_DRIVE") or line.startswith("_TYPE"):
            scantype = line.split("=")[1]
        elif line.startswith("_WL1"):
            wl = float(line.split("=")[1])
        elif line.startswith("_STEPSIZE") or line.startswith("_STEP_SIZE"):
            if not line.startswith("_STEP_SIZE_B"):
                step = float(line.split("=")[1])
                line_count= 0.
        elif line.startswith("_STEP_SIZE_B"):
            stepb = float(line.split("=")[1])
        elif line.startswith("_START"):
            start = float(line.split("=")[1])
        elif line.startswith("_THETA") or line.startswith("_OMEGA"):
            om = float(line.split("=")[1])
        elif line.startswith("_2THETA") or line.startswith("_TWOTHETA"):
            if not line.startswith("_2THETAC"):
                tth = float(line.split("=")[1])
                offset = om - tth/2
        elif line.startswith("_KHI"):
            khi = float(line.split("=")[1])
        elif line.startswith("_PHI"):
            phi = float(line.split("=")[1])
        elif line.startswith("_X"):
            tx = float(line.split("=")[1])
        elif line.startswith("_Y"):
            ty = float(line.split("=")[1])
        elif line.startswith("_V4_TEMPERATURE"):
            temperature = float(line.split("=")[1]) - 273.
        elif not line.startswith(";"):
            if not line.startswith("_"):
                if line.strip():
                    try:
                        temperature = temperature
                    except:
                        temperature = 25
                    try:
                        scanning, intensity = line.split()
                        line_count +=1
                        outfile.write(str(temperature) + " " + str(khi) + " " + str(phi) + " " + str(tx) + " " + str(ty) + " " + str(om) + " " + str(offset) + " " + str(tth) + " " + scanning + " "  + intensity +'\n')
                    except:
                        if line_count==0:
                            scanning = start
                        else:
                            scanning += step
                        line_count +=1
                        intensity = line.split()[0]
                        outfile.write(str(temperature) + " " + str(khi) + " " + str(phi) + " " + str(tx) + " " + str(ty) + " " + str(om) + " " + str(offset) + " " + str(tth) + " " + str(scanning) + " "  + intensity +'\n')
    #sys.stdout.write("\n")
    #sys.stdout.write("Done !\n")
    infile.close()
    outfile.close()
    return scantype, line_count, wl

def file_nb(path):
    number = int(path.split("RawData")[-1].split(".xml")[0])
    return number

def brml_reader(file_name):
    """
    Extracts brml into a temporary unzip file, and parses all xml files.
    For every intensity value, saves all relevant motor coordinates and sensor values.
    All values are save in temporary SPEC-style tmp file.
    """
    extract_path = os.path.join(os.getcwd(),"unzip")
    if sys.platform == "win32":
        os.system("RMDIR "+ extract_path +" /s /q")
    elif sys.platform == "darwin":
        os.system("rm -rf "+ extract_path)
    elif sys.platform == "linux" or sys.platform == "linux2":
        os.system("rm -rf "+ extract_path)

    #Extract all RawData*.xml files and InstructionContainer the brml to temporary unzip file
    with zipfile.ZipFile(file_name,"r") as brml:
        for info in brml.infolist():
            if ("RawData" in info.filename) or ("InstructionContainer" in info.filename):
            #if ("RawData" in info.filename):
                brml.extract(info.filename, extract_path)

    # Initialize all offsets to 0
    off_tth = off_om = off_phi = off_chi = off_tx = off_ty = 0
    
    #Modification June 2017
    #In some RawData.xml files, wavelength and static motors are missing.
    #Find wl and static motors in MeasurementContainer.xml
    data_path = os.path.join(extract_path, "*0","InstructionContainer.xml")
    for file in sorted(glob.glob(data_path)):
        tree = ET.parse(file)
        root = tree.getroot()
        for chain in root.findall("./ComparisonMethod/HrxrdAlignmentData"):
            wl = chain.find("WaveLength").attrib["Value"]

        for chain in root.findall("./ComparisonMethod/HrxrdAlignmentData/Data"):
            if chain.get("LogicName") == "TwoTheta":
                tth = chain.find("TheoreticalPosition").attrib["Value"]
                off_tth = chain.find("PositionOffset").attrib["Value"]
                tth = str(float(tth)-float(off_tth))

            if chain.get("LogicName") == "Theta":
                om = chain.find("TheoreticalPosition").attrib["Value"]
                off_om = chain.find("PositionOffset").attrib["Value"]
                om = str(float(om)-float(off_om))

            if chain.get("LogicName") == "Chi":
                chi = chain.find("TheoreticalPosition").attrib["Value"]
                off_chi = chain.find("PositionOffset").attrib["Value"]
                chi = str(float(chi)-float(off_chi))

            if chain.get("LogicName") == "Phi":
                phi = chain.find("TheoreticalPosition").attrib["Value"]
                off_phi = chain.find("PositionOffset").attrib["Value"]
                phi = str(float(phi)-float(off_phi))

            if chain.get("LogicName") == "X":
                tx = chain.find("TheoreticalPosition").attrib["Value"]
                off_tx = chain.find("PositionOffset").attrib["Value"]
                tx = str(float(tx)-float(off_tx))

            if chain.get("LogicName") == "Y":
                ty = chain.find("TheoreticalPosition").attrib["Value"]
                off_ty = chain.find("PositionOffset").attrib["Value"]
                ty = str(float(ty)-float(off_ty))
        os.remove(file)

    #Create ouput file
    outfile = open("tmp", "w", encoding='utf8') # Create output data file
    outfile.write("#temperature   khi   phi   x   y   theta   offset   2theta   scanning motor   intensity\n")

    # Finds scan type, wl, motors, temperature and intensity values in RawData.xml
    data_path = os.path.join(extract_path, "*0","*.xml") #reading files in Experiment0 folder
    for file in sorted(glob.glob(data_path), key=file_nb):
        new_file = 0
        check_temperature = 0
        #parsing XML file
        tree = ET.parse(file) 
        root = tree.getroot()
        #obtain scan type
        for chain in (root.findall("./DataRoutes/DataRoute/ScanInformation") or root.findall("./ScanInformation")):
            scan_type = chain.get("VisibleName")
            if ("PSD" in scan_type) or ("Psd" in scan_type):
                scan_type = "PSDFIXED"
            if ("Coupled" in scan_type) or ("coupled" in scan_type) or ("2Theta-Omega" in scan_type):
                scan_type = "COUPLED"
            if ("Rocking" in scan_type) or ("rocking" in scan_type):
                scan_type = "THETA"

        #Find wl in RawData.xml
        for chain in root.findall("./FixedInformation/Instrument/PrimaryTracks/TrackInfoData/MountedOptics/InfoData/Tube/WaveLengthAlpha1"):
            wl = chain.get("Value")

        # Find the fast-scanning axis
        for chain in (root.findall("./DataRoutes/DataRoute/ScanInformation/ScanAxes/ScanAxisInfo") or root.findall("./ScanInformation/ScanAxes/ScanAxisInfo")):
            if new_file == 0:
                if chain.get("AxisName") == "TwoTheta": #Added offset correction / June 2017. Only relevant if offset in InstructionContainer. 0 otherwise.
                    off_scan = float(off_tth)
                elif chain.get("AxisName") == "Theta":
                    off_scan = float(off_om)
                else:
                    off_scan = 0
                step = chain.find("Increment").text
                start = chain.find("Start").text
                ref = chain.find("Reference").text
                start = str(float(ref)+float(start)-off_scan)  #Added offset correction / June 2017.
                #start = str(float(ref)+float(start))
                new_file += 1

        for chain in (root.findall("./DataRoutes/DataRoute/ScanInformation/ScanAxes/ScanAxisInfo") or root.findall("./ScanInformation/ScanAxes/ScanAxisInfo")):
            if chain.get("AxisName") == "TwoTheta":
                tth = chain.find("Start").text
                ref = chain.find("Reference").text
                tth = str(float(ref)+float(tth)-float(off_tth))  #Added offset correction / June 2017.
                #tth = str(float(ref)+float(tth))

            if chain.get("AxisName") == "Theta":
                om = chain.find("Start").text
                ref = chain.find("Reference").text
                om = str(float(ref)+float(om)-float(off_om))  #Added offset correction / June 2017.
                #om = str(float(ref)+float(om))

            if chain.get("AxisName") == "Chi":
                chi = chain.find("Start").text
                ref = chain.find("Reference").text
                chi = str(float(ref)+float(chi)-float(off_chi))  #Added offset correction / June 2017.
                #chi = str(float(ref)+float(chi))

            if chain.get("AxisName") == "Phi":
                phi = chain.find("Start").text
                ref = chain.find("Reference").text
                phi = str(float(ref)+float(phi)-float(off_phi))  #Added offset correction / June 2017.
                #phi = str(float(ref)+float(phi))

            if chain.get("AxisName") == "X":
                tx = chain.find("Start").text
                ref = chain.find("Reference").text
                tx = str(float(ref)+float(tx)-float(off_tx))  #Added offset correction / June 2017.
                #tx = str(float(ref)+float(tx))

            if chain.get("AxisName") == "Y":
                ty = chain.find("Start").text
                ref = chain.find("Reference").text
                ty = str(float(ref)+float(ty)-float(off_ty))  #Added offset correction / June 2017.
                #ty = str(float(ref)+float(ty))

        for chain in (root.findall("./DataRoutes/DataRoute/DataViews/RawDataView/Recording") or root.findall("./DataViews/RawDataView/Recording")):
            if "Temperature" in chain.get("LogicName"):
                check_temperature = 1

        for chain in root.findall("./FixedInformation/Drives/InfoData"):
            if chain.get("LogicName") == "TwoTheta":
                tth = chain.find("Position").attrib["Value"]
                tth = str(float(tth)-float(off_tth))  #Added offset correction / June 2017.

            if chain.get("LogicName") == "Theta":
                om = chain.find("Position").attrib["Value"]
                om = str(float(om)-float(off_om))  #Added offset correction / June 2017.

            if chain.get("LogicName") == "Chi":
                chi = chain.find("Position").attrib["Value"]
                chi = str(float(chi)-float(off_chi))  #Added offset correction / June 2017.

            if chain.get("LogicName") == "Phi":
                phi = chain.find("Position").attrib["Value"]
                phi = str(float(phi)-float(off_phi))  #Added offset correction / June 2017.

            if chain.get("LogicName") == "X":
                tx = chain.find("Position").attrib["Value"]
                tx = str(float(tx)-float(off_tx))  #Added offset correction / June 2017.

            if chain.get("LogicName") == "Y":
                ty = chain.find("Position").attrib["Value"]
                ty = str(float(ty)-float(off_ty))  #Added offset correction / June 2017.

        offset = str(float(om) - float(tth)/2.)

        if "PSDFIXED" in scan_type:
            if check_temperature == 0:
                for chain in (root.findall("./DataRoutes/DataRoute") or root.findall("./")):
                    intensity = (chain.find("Datum").text).split(',')

                for chain in (root.findall("./DataRoutes/DataRoute/DataViews/RawDataView/Recording") or root.findall("./DataViews/RawDataView/Recording")):
                    if chain.get("LogicName") == "Counter1D":
                        n_channels = int(chain.find("Size/X").text)

                line_count = 0
                int_shift = len(intensity) - n_channels
                for i in range(n_channels): #the intensity values are shifted to the right by int_shift
                    if i == 0:
                        scanning = float(start)
                    else:
                        scanning += float(step)
                    line_count += 1
                    outfile.write("25" + " " + (chi) + " " + (phi)
                                  + " " + (tx) + " " + (ty) + " " + (om)
                                  + " " + (offset) + " " + (tth) + " " + str(scanning)
                                  + " "  + intensity[i+int_shift] +'\n')
            else:
                return implementation_warning, 0, 0
        
        #if "COUPLED" in scan_type:
        # to do check in brml that all scans (except psd fixed) share the same data structure (wrt temperature)
        else:
            if check_temperature == 0:
                line_count = 0
                for chain in (root.findall("./DataRoutes/DataRoute/Datum") or root.findall("./Datum")):
                    if line_count == 0:
                        scanning = float(start)
                    else:
                        scanning += float(step)
                    line_count += 1
                    intensity = (chain.text).split(',')[-1]
                    outfile.write("25" + " " + (chi) + " " + (phi)
                                  + " " + (tx) + " " + (ty) + " " + (om)
                                  + " " + (offset) + " " + (tth) + " " + str(round(scanning, 4))
                                  + " "  + intensity +'\n')
            else:
                line_count = 0
                for chain in (root.findall("./DataRoutes/DataRoute/Datum") or root.findall("./Datum")):
                    if line_count == 0:
                        scanning = float(start)
                    else:
                        scanning += float(step)
                    line_count += 1
                    intensity = (chain.text).split(',')[-2]
                    temperature = (chain.text).split(',')[-1]
                    outfile.write(temperature + " " + (chi) + " " + (phi)
                                  + " " + (tx) + " " + (ty) + " " + (om)
                                  + " " + (offset) + " " + (tth) + " " + str(round(scanning, 4))
                                  + " "  + intensity +'\n')


    outfile.close()
    if sys.platform == "win32":
        os.system("RMDIR "+ extract_path +" /s /q")
    elif sys.platform == "darwin":
        os.system("rm -rf "+ extract_path)
    elif sys.platform == "linux" or sys.platform == "linux2":
        os.system("rm -rf "+ extract_path)
    return scan_type, line_count, wl
