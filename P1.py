import pandas as pd

from openpyxl import workbook, load_workbook

# def hello(name, age=10):
#     return "something", "else"

# x, y = hello("a")

# Calculates the section property of a I Section
def Section_Prop(Section: pd.DataFrame, n: int = 8):
 
    y = []
    mod_ratio_n = []

    if n == 0:
        Section = Section.drop([0]).reset_index()
        print(Section["Width"] )
                      

    # Calculates y 
    for i in range(0,len(Section['Width'])):
        if i == 0:
            y.append(Section.loc[i,"Thickness/Height"]/2)
            if n == 0:
                mod_ratio_n.append(1)
            else:
                mod_ratio_n.append(n)
            
        else:
            y.append(Section.loc[i,"Thickness/Height"]/2 + y[i-1] + Section.loc[i-1,"Thickness/Height"]/2)
            mod_ratio_n.append(1)


    Section["Area"] = Section["Width"] * Section ["Thickness/Height"] / mod_ratio_n

    Section["Y"] = y
    Section["AY"] = Section["Area"] * Section ["Y"] 

    print(Section["Area"])
    print(Section["Width"] * Section ["Thickness/Height"])

    Total = Section.sum()
    Centroid = Total['AY'] / Total['Y']

    Section["D"] = Section["Y"] - Centroid
    Section["AD^2"] = Section["Area"] * Section["D"]**2

    Section["I0"] = Section['Width'] * Section["Thickness/Height"]**3 / 12 / mod_ratio_n
    Total = Section.sum()

    Inertia =  Total["AD^2"] + Total["I0"]

    BM_height = Total["Thickness/Height"]

    Y_TOP = Centroid
    Y_BOT = BM_height - Centroid

    S_TOP = Inertia / Y_TOP
    S_BOT = Inertia / Y_BOT

    Modulus = pd.DataFrame({'Location':["Top","Bottom"],'Distance y':[Y_TOP,Y_BOT],'Section Modulus':[S_TOP,S_BOT ]})

    print(Total)

    print(Section)
    print(Modulus)
    print(Inertia)
    
    return Section, Modulus, Inertia

# Get the last row in the excel
def get_max_row(xlName, xlsheetname):

    wb = load_workbook(xlName)

    #Create new sheet if xlsheetname is not in the workbook
    if xlsheetname not in wb.sheetnames:
        wb.create_sheet(xlsheetname)
    
    wb.active = wb[xlsheetname]
    ws = wb.active

    return ws.max_row

# Printing the section properties to Excel
def Prop_to_Excel(xlName, xlsheetname, Section, n = 8):

    BmTable, BmModulus, BmInertia = Section_Prop(Section, n)
   
    with pd.ExcelWriter(xlFilename, engine='openpyxl', mode='a',if_sheet_exists="overlay") as writer:
        BmTable.to_excel(writer, sheet_name = xlsheetname, startrow = get_max_row(xlName, xlsheetname) + 2, index=False, startcol=2)
   
    Total = BmTable.sum()
    # sum_row = ws.max_row+10


    wb = load_workbook(xlName)
    wb.active = wb[xlsheetname]
    ws = wb.active
    sum_row = ws.max_row+1

    ws["k"+str(sum_row)]= BmInertia
    ws["f"+str(sum_row)]= Total["Area"]
    ws["h"+str(sum_row)]= Total["AY"]
    wb.save(xlFilename)
    wb.close()

    with pd.ExcelWriter(xlFilename, engine='openpyxl', mode='a',if_sheet_exists="overlay") as writer:
    
        BmModulus.to_excel(writer, sheet_name = xlsheetname, startrow = get_max_row(xlName, xlsheetname) + 2, startcol = 5,header=True, index=False)

#Calculating Vp
def Plastic_Shear_Vp(Geom_Input: dict):
    return 0.58 * Geom_Input['fyw'] * Geom_Input['D_web'] * Geom_Input['t_web']

# returns true if stiffened, false if not. Assume no longitudinal stiffener
def is_stiffened(Geom_Input: dict, Stiff_input: dict):
    if Stiff_input['Panel'] == 'Interior' and Stiff_input['Spacing d0'] <= Geom_Input['D_web'] * 3:
        print ("Check stiffened capacity using 6.10.9.3")
        return True
    elif Stiff_input['Panel'] == 'End' and Stiff_input['Spacing d0'] <= Geom_Input['D_web'] * 1.5:
        print ("Check stiffened capacity using 6.10.9.3.3")
        return True
    else:
        print ("Check unstiffened capacity using 6.10.9.2")
        return False


def Shear_buckling_k (Geom_Input, Stiff_input):
    if not is_stiffened(Geom_Input, Stiff_input):
        print("k value per AASHTO 6.10.9.2")
        return 5
    else:
        print("Calculate k per AASHTO 6.10.9.3.2-7")
        return 5 + 5 / (Stiff_input['Spacing d0'] / Geom_Input['D_web']) ** 2

# Calculate Shear-buckling resistance tot he shear yield Strength
def ratio_C(Geom_Input, Stiff_input):
    D = Geom_Input['D_web']
    tw = Geom_Input['t_web']
    E = Geom_Input['E']
    Fyw = Geom_Input['fyw']
    k = Shear_buckling_k(Geom_Input, Stiff_input)
    print("k=" + str(k))

    if D/tw <= 1.12 * (E * k / Fyw) ** 0.5:
        print("Calculate C per AASHTO 6.10.9.3.2-4")
        return 1
    elif D/tw < 1.4* (E * k / Fyw) ** 0.5:
        print("Calculate C per AASHTO 6.10.9.3.2-5")
        return 1.12 / (D / tw) * (E * k / Fyw) ** 0.5
    else:
        print("Calculate C per AASHTO 6.10.9.3.2-6")
        return 1.57 / ((D / tw) ** 2) * (E * k / Fyw)
    

def capacity_Vn (Geom_Input, Stiff_input):
    D = Geom_Input['D_web']
    tw = Geom_Input['t_web']
    ttf = Geom_Input['t_tf']
    btf = Geom_Input['b_tf']
    tbf = Geom_Input['t_bf']
    bbf = Geom_Input['b_bf']

    C = ratio_C(Geom_Input, Stiff_input)
    print("C=" + str(C))

    if Stiff_input['Panel'] == 'Interior':
        if (2 * D * tw)/(btf*ttf + bbf * tbf) <= 2.5:             #AASHTO 6.10.9.3.2-1
            print("Calculate Vn per AASHTO 6.10.9.3.2-1")
            return Plastic_Shear_Vp(Geom_Input) * (C + 0.87 * (1-C)/(1+(Stiff_input['Spacing d0'] / Geom_Input['D_web'])**2)**0.5)
        else:  #AASHTO 6.10.9.3.2-8
           print("Calculate Vn per AASHTO AASHTO 6.10.9.3.2-8")
           return Plastic_Shear_Vp(Geom_Input) * (C + 0.87 * (1-C)/((1+(Stiff_input['Spacing d0'] / Geom_Input['D_web'])**2)**0.5 + (Stiff_input['Spacing d0'] / Geom_Input['D_web'])))
    else: 
        return Plastic_Shear_Vp(Geom_Input) * C

def check_Vu(Vu, Vn):
    if Vu > Vn:
        return "NG"
    else:
        return "OK"


Stiffener_Input = {'Stiffener': 'yes',  # Should be yes/no only 
                   'Panel':'Interior',       # End/ Interior only
                   'Spacing d0': 300}    # Spacing in inches

Input = {'fyw':50, 'fyf':50, 'E':29000,'fc':4,
         'b_slab':50, 't_slab':8,
         'b_tf':28, 't_tf':1.75, 
         'D_web':110, 't_web':0.75, 
         'b_bf':28, 't_bf':2}


BmSect = pd.DataFrame({'Element':["Slab","Top Flange","Web","Bottom Flange"],
                       'Width': [Input['b_slab'], Input['b_tf'], Input['t_web'], Input['b_bf']],
                       'Thickness/Height':[Input['t_slab'],Input['t_tf'],Input['D_web'],Input['t_bf']]})

# print(Plastic_Shear_Vp(Input))

# print(is_stiffened(Input, Stiffener_Input))
# print("k = " + str(Shear_buckling_k(Input, Stiffener_Input)))

# print("C=" + str(ratio_C(Input, Stiffener_Input)))
print("Vn=" + str(capacity_Vn(Input, Stiffener_Input)))

# xlFilename = "SectionProp.xlsx"
# xlSheet = "Section2"

# Prop_to_Excel(xlFilename, xlSheet, BmSect, 0)
# Prop_to_Excel(xlFilename, xlSheet, BmSect, 8)
# Prop_to_Excel(xlFilename, xlSheet, BmSect, 24)






# BmTable.to_excel(xlFilename, index=False, startcol=2)

# wb = load_workbook(xlFilename)
# ws = wb.active

# ws["k"+str(ws.max_row+1)]= BmInertia

# wb.save(xlFilename)

# with pd.ExcelWriter(xlFilename, engine='openpyxl', mode='a',if_sheet_exists="overlay") as writer:
    
#     BmModulus.to_excel(writer, startrow = ws.max_row + 5, startcol = 5,header=True, index=False)

