# Create the barcode table (RMs and CUs) based Unique IDs.

import json
import re

# create mapping of ngccm barcodes to ngccm unique ids from Kelvin's database csv file
def generateBarcodeToUidMap(ngccm_database_file):
    ngccm_file = open(ngccm_database_file, 'r')
    uid_dict = {}
    barcode = 0
    ngccm_uid = ""
    n = 0
    for line in ngccm_file:
        line = line.strip(" \r\n")
        line = line.replace('"','')
        s = line.split(";")
        bc = int(s[0])
        uid = s[1]
        uid = uid[2:10].upper()
        if barcode != bc:
            n = 1
            barcode = bc
            ngccm_uid = uid
            print "ngccm {0} card {1} : {2}".format(barcode, n, uid)
        else:
            n += 1
            ngccm_uid += "_{0}".format(uid)
            print "ngccm {0} card {1} : {2}".format(barcode, n, uid)
            if n == 4:
                print "ngccm {0} : {1}".format(barcode, ngccm_uid)
                uid_dict[barcode] = ngccm_uid
    ngccm_file.close()
    with open("ngccm_cards/ngccm.json", 'w') as j:
        json.dump(uid_dict, j, sort_keys=True, indent=4)
    return uid_dict

# generateLocationToUidMap: return dictionary and output json mapping detector location to RM, CU and ngCCM unique id 
# Example Outputs:
# "HEM03-4": "EABCC9_EA9D53_EAB3B0_EA9CD2"
# "HEP18-calib": "EAA109"
# "HEP15-ngccm": "28145393_284B9F93_287DC993_28032693"

def generateLocationToUidMap(qiecard_unique_id_file, ngccm_unique_id_file):
    qiecard_file = open(qiecard_unique_id_file, 'r')
    ngccm_file = open(ngccm_unique_id_file, 'r')
    uid_dict = {}
    
    # create mapping for RM and CU location to Unique ID
    rm_prev = 0
    rm_uid = ""
    for line in qiecard_file:
        # add to dictionary
        line = line.strip(" \r\n")
        line = line.replace('"','')
        s = line.split(":")
        location = s[0].strip()
        uid = s[1].strip()
        uid = uid.split(" ")[-1]
        uid = uid[2:8].upper()
        #print "{0} : {1}".format(location, uid)
        if "calib" in location:
            uid_dict[location] = uid
        else:
            # Match HEP07-3-4
            m = re.search('([A-Z]+[0-9]+)-([0-9])-([0-9])', location)
            rbxName = m.group(1)
            rm      = int(m.group(2))
            card    = int(m.group(3))
            if rm == rm_prev:
                rm_uid += "_{0}".format(uid)
            else:
                rm_uid = uid
                rm_prev = rm 
            if card == 4:
                rm_name = "{0}-{1}".format(rbxName, rm)
                uid_dict[rm_name] = rm_uid
    
    # create mapping for ngCCM location to Unique ID
    jslot = 0
    ngccm_uid = ""
    for line in ngccm_file:
        line = line.strip(" \r\n")
        line = line.replace('"','')
        s = line.split(":")
        location = s[0].strip()
        uid = s[1].strip()
        uid = uid[2:10].upper()
        
        # Match HEM18-J16_ID
        m = re.search('([A-Z]+[0-9]+)-J([0-9]+)_ID', location)
        rbxName = m.group(1)
        jslot = int(m.group(2))
        
        print "{0}: {1} {2}: {3}".format(location, rbxName, jslot, uid)
        
        if jslot == 13:
            ngccm_uid = uid
        else:
            ngccm_uid += "_{0}".format(uid)
            if jslot == 16:
                uid_dict["{0}-ngccm".format(rbxName)] = ngccm_uid

    qiecard_file.close()
    ngccm_file.close()
    # dump unique id dictionary to json file
    with open("uid.json", 'w') as j:
        json.dump(uid_dict, j, sort_keys=True, indent=4)
    return uid_dict

def createTable(rm_json, cu_json, qiecard_unique_id_file, ngccm_unique_id_file):
    # get mapping from detector location to unique id
    uid_dict = generateLocationToUidMap(qiecard_unique_id_file, ngccm_unique_id_file)
    # load RM and CU json files
    with open(rm_json, 'r') as rm_j:
        rm_dict = json.load(rm_j) 
    with open(cu_json, 'r') as cu_j:
        cu_dict = json.load(cu_j) 
    # invert barcode to unique id mapping into uid to barcode map
    inv_rm_dict = {v: k for k, v in rm_dict.iteritems()}
    inv_cu_dict = {v: k for k, v in cu_dict.iteritems()}
    # create map from decector location to barcode
    barcode_dict = {}
    n_rm_errors = 0
    n_cu_errors = 0
    for location in uid_dict:
        uid = uid_dict[location]
        if "calib" in location:
            try:
                barcode = inv_cu_dict[uid]
            except:
                print "{0} with uid {1} is not found CU json file.".format(location, uid)
                n_cu_errors += 1
                continue
        else:
            try:
                barcode = inv_rm_dict[uid]
            except:
                print "{0} with uid {1} is not found RM json file.".format(location, uid) 
                n_rm_errors += 1
                continue
        barcode_dict[location] = barcode

    with open("barcode.json", 'w') as j:
        json.dump(barcode_dict, j, sort_keys=True, indent=4)
    print "Number of RM errors: {0}".format(n_rm_errors)
    print "Number of CU errors: {0}".format(n_cu_errors)
    
    table = open("HE_Barcodes.txt", 'w')
    row = ""
    rowFormat = list("{%d:>5}" % i for i in xrange(6))
    row = "".join(rowFormat)
    row = row.format("RBX", "RM1", "RM2", "RM3", "RM4", "CU")
    table.write(row + "\n")
    print row
    for side in ["HEP", "HEM"]:
        for rbx in xrange(1,19):
            rbxNum = str(rbx).zfill(2)
            rbxName = "{0}{1}".format(side, rbxNum)
            row = rbxName
            for rm in xrange(1,6):
                if rm == 5:
                    rmName = "{0}-calib".format(rbxName)
                else:
                    rmName = "{0}-{1}".format(rbxName, rm)
                try:
                    barcode = barcode_dict[rmName]
                except:
                    barcode = 999
                row += "{0:>5}".format(barcode)
            table.write(row + "\n")
            print row

    table.close()
    return

if __name__ == "__main__":
    #generateBarcodeToUidMap("ngccm_cards/ngCCM_sn.csv")
    generateLocationToUidMap("qie_cards/HE_Unique_IDs.txt","ngccm_cards/HE_CCM_Unique_IDs.txt")
    #createTable("qie_cards/rm.json", "qie_cards/cu.json", "qie_cards/HE_Unique_IDs.txt", "ngccm_cards/ngCCM_sn.csv")


